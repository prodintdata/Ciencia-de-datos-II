import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix

def psi(expected, actual, bins=10):
    # Population Stability Index; numeric features use the reference deciles, categorical ones their levels.
    expected,actual=pd.Series(expected),pd.Series(actual)
    if pd.api.types.is_numeric_dtype(expected):
        edges=np.unique(np.quantile(expected,np.linspace(0,1,bins+1))); edges[0],edges[-1]=-np.inf,np.inf
        e,a=pd.cut(expected,edges).value_counts(normalize=True,sort=False),pd.cut(actual,edges).value_counts(normalize=True,sort=False)
    else:
        levels=sorted(set(expected)|set(actual))
        e,a=expected.value_counts(normalize=True).reindex(levels,fill_value=0),actual.value_counts(normalize=True).reindex(levels,fill_value=0)
    e,a=np.clip(e.to_numpy(),1e-4,None),np.clip(a.to_numpy(),1e-4,None)
    return float(np.sum((a-e)*np.log(a/e)))

def drift_table(reference, current, columns):
    return pd.DataFrame([{"feature":c,"psi":psi(reference[c],current[c])} for c in columns])

def _rates(y, p):
    tn,fp,fn,tp=confusion_matrix(y,p,labels=[0,1]).ravel()
    return (tp/(tp+fn) if tp+fn else float("nan")),(fp/(fp+tn) if fp+tn else float("nan"))

def monthly_report(test, pred, min_support=20):
    # One row per month; a group below min_support is reported but its gap is not interpreted.
    df=test.assign(pred=pred,month=test.received_date.dt.to_period("M").astype(str)); rows=[]
    for month,g in df.groupby("month"):
        row={"month":month,"n":len(g)}; row["recall"],row["fpr"]=_rates(g.target,g.pred)
        for grp,h in g.groupby("protected_group"):
            row[f"n_{grp}"]=len(h); row[f"recall_{grp}"],row[f"fpr_{grp}"]=_rates(h.target,h.pred)
            # Denominators of recall (positives) and FPR (negatives): a gap rests on these, not on n.
            row[f"pos_{grp}"]=int((h.target==1).sum()); row[f"neg_{grp}"]=int((h.target==0).sum())
        row["support_ok"]=all(row.get(f"n_{k}",0)>=min_support for k in ("G1","G2"))
        row["recall_gap"]=abs(row.get("recall_G1",np.nan)-row.get("recall_G2",np.nan))
        row["fpr_gap"]=abs(row.get("fpr_G1",np.nan)-row.get("fpr_G2",np.nan))
        rows.append(row)
    return pd.DataFrame(rows)

def alerts(monthly, drift, cfg):
    t=cfg["thresholds"]; out=[]
    for r in monthly.itertuples():
        # Global recall needs only the month's support; gaps need support in every group.
        if r.n<cfg["min_support"]: out.append({"month":r.month,"signal":"support","level":"info","detail":f"n={r.n}; mes no interpretable"}); continue
        if r.recall<t["min_recall"]: out.append({"month":r.month,"signal":"recall","level":"high","detail":f"recall={r.recall:.3f}"})
        if not r.support_ok: out.append({"month":r.month,"signal":"support","level":"info","detail":f"n_G1={r.n_G1}, n_G2={r.n_G2}; brechas no interpretables"}); continue
        if r.recall_gap>t["max_recall_gap"]: out.append({"month":r.month,"signal":"recall_gap","level":"high","detail":f"gap={r.recall_gap:.3f}"})
        if r.fpr_gap>t["max_fpr_gap"]: out.append({"month":r.month,"signal":"fpr_gap","level":"high","detail":f"gap={r.fpr_gap:.3f}"})
        if r.recall_G1<t["watch_recall_G1"]: out.append({"month":r.month,"signal":"recall_G1","level":"medium","detail":f"recall_G1={r.recall_G1:.3f}"})
    for r in drift.itertuples():
        if r.psi>=t["psi_action"]: out.append({"month":"all","signal":f"drift:{r.feature}","level":"high","detail":f"psi={r.psi:.3f}"})
        elif r.psi>=t["psi_watch"]: out.append({"month":"all","signal":f"drift:{r.feature}","level":"medium","detail":f"psi={r.psi:.3f}"})
    return pd.DataFrame(out,columns=["month","signal","level","detail"])

def month_gap_bootstrap(test, pred, month, metric="fpr", resamples=1000, seed=42):
    # 95 % bootstrap interval of one month's gap between G1 and G2, resampling cases within the month.
    df=test.assign(pred=pred,month=test.received_date.dt.to_period("M").astype(str)); g=df[df.month==month]
    k=1 if metric=="fpr" else 0; rng=np.random.default_rng(seed); gaps=[]
    for _ in range(resamples):
        s=g.iloc[rng.integers(0,len(g),len(g))]
        r={grp:_rates(h.target,h.pred)[k] for grp,h in s.groupby("protected_group")}
        if {"G1","G2"}<=set(r) and not np.isnan(r["G1"]) and not np.isnan(r["G2"]): gaps.append(abs(r["G1"]-r["G2"]))
    return np.array(gaps)

def variant_status(found):
    # Monitoring policy (configs/monitoring.yml): any high alert in an interpretable month = REVIEW.
    high=found[found.level=="high"]
    return {"status":"REVIEW" if len(high) else "GO","failed":[f"{r.signal}@{r.month}" for r in high.itertuples()]}
