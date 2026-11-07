import numpy as np
import pandas as pd
from fairlearn.metrics import MetricFrame, count, false_positive_rate, selection_rate, true_positive_rate
from sklearn.metrics import accuracy_score, precision_score

METRICS={"count":count,"accuracy":accuracy_score,"selection_rate":selection_rate,"recall":true_positive_rate,"precision":lambda y,p:precision_score(y,p,zero_division=0),"fpr":false_positive_rate}

def audit(y_true, y_pred, sensitive):
    mf=MetricFrame(metrics=METRICS,y_true=y_true,y_pred=y_pred,sensitive_features=sensitive)
    return mf.overall, mf.by_group, mf.difference(method="between_groups")

def intersectional(df):
    return df[["protected_group","age_band"]].astype(str).agg(" | ".join,axis=1)

def gap(by_group, metric):
    values=pd.to_numeric(by_group[metric],errors="coerce").dropna()
    return float(values.max()-values.min()) if len(values) else 0.0

def wilson(k, n, z=1.96):
    # 95 % Wilson interval for a proportion k/n; (nan, nan) when n == 0.
    if n==0: return (np.nan,np.nan)
    p=k/n; den=1+z**2/n; c=(p+z**2/(2*n))/den; h=z*np.sqrt(p*(1-p)/n+z**2/(4*n**2))/den
    return (float(max(0.0,c-h)),float(min(1.0,c+h)))

def support_table(y_true, y_pred, groups, min_class_support=20):
    # Recall is judged by the positives of each subgroup and FPR by its negatives,
    # so support is checked against the denominator of each metric, not the total n.
    d=pd.DataFrame({"y":np.asarray(y_true),"p":np.asarray(y_pred),"g":np.asarray(groups)})
    rows=[]
    for g,s in d.groupby("g",sort=True):
        pos,neg=int((s.y==1).sum()),int((s.y==0).sum())
        tp,fp=int(((s.y==1)&(s.p==1)).sum()),int(((s.y==0)&(s.p==1)).sum())
        rl,rh=wilson(tp,pos); fl,fh=wilson(fp,neg)
        rows.append({"group":g,"n":len(s),"n_pos":pos,"n_neg":neg,"tp":tp,"fn":pos-tp,"fp":fp,"tn":neg-fp,
                     "recall":tp/pos if pos else np.nan,"recall_ci_low":rl,"recall_ci_high":rh,
                     "fpr":fp/neg if neg else np.nan,"fpr_ci_low":fl,"fpr_ci_high":fh,
                     "recall_supported":pos>=min_class_support,"fpr_supported":neg>=min_class_support})
    return pd.DataFrame(rows).set_index("group")
