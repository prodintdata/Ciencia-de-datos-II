import numpy as np
import pandas as pd
from fairlearn.reductions import ExponentiatedGradient, TruePositiveRateParity
from sklearn.base import clone
from .fairness import audit, gap

def summarize(name, y_true, pred, sensitive):
    overall,by_group,_=audit(y_true,pred,sensitive)
    row={"variant":name,"accuracy":overall["accuracy"],"recall":overall["recall"],"fpr":overall["fpr"],"selection_rate":overall["selection_rate"],"recall_gap":gap(by_group,"recall"),"fpr_gap":gap(by_group,"fpr")}
    for g in by_group.index: row[f"recall_{g}"]=by_group.loc[g,"recall"]; row[f"fpr_{g}"]=by_group.loc[g,"fpr"]
    return row

def rule_predictions(df, min_incidents=3, max_infrastructure=0.3):
    # Non-predictive alternative from LAB11: explicit public rules, no model.
    return ((df.previous_incidents>=min_incidents)|(df.infrastructure_score<max_infrastructure)).astype(int).to_numpy()

def threshold_predictions(model, X, threshold):
    return (model.predict_proba(X)[:,1]>=threshold).astype(int)

def fit_exponentiated_gradient(pipeline, X, y, sensitive, seed=42):
    # The sensitive attribute is used only during training; prediction needs X alone.
    prep,estimator=clone(pipeline[:-1]),clone(pipeline[-1])
    Xt=prep.fit_transform(X)
    eg=ExponentiatedGradient(estimator,constraints=TruePositiveRateParity())
    eg.fit(Xt,y,sensitive_features=sensitive)
    return lambda Xnew: eg.predict(prep.transform(Xnew),random_state=seed)

def bootstrap_gaps(y_true, pred, sensitive, n=1000, seed=42):
    y,p,s=np.asarray(y_true),np.asarray(pred),np.asarray(sensitive); rng=np.random.default_rng(seed); rows=[]
    for _ in range(n):
        i=rng.integers(0,len(y),len(y)); _,g,_=audit(y[i],p[i],s[i])
        rows.append({"recall_gap":gap(g,"recall"),"fpr_gap":gap(g,"fpr"),"recall_G1":g.loc["G1","recall"] if "G1" in g.index else np.nan})
    df=pd.DataFrame(rows)
    return {c:{"p2.5":float(df[c].quantile(.025)),"p50":float(df[c].median()),"p97.5":float(df[c].quantile(.975))} for c in df}
