import numpy as np
from inf8239_u04.data import load_data,features,temporal_split
from inf8239_u04.mitigation import bootstrap_gaps,threshold_predictions
from inf8239_u04.model import build_model
def test_lower_threshold_never_reduces_recall():
    tr,te=temporal_split(load_data()); m=build_model().fit(features(tr),tr.target)
    hi,lo=threshold_predictions(m,features(te),.5),threshold_predictions(m,features(te),.4)
    pos=te.target.to_numpy()==1; assert lo[pos].sum()>=hi[pos].sum()
def test_support_uses_class_denominators():
    from inf8239_u04.fairness import support_table
    y=np.array([1,1,1,0,0,1,0]); p=np.array([1,0,1,1,0,1,0]); g=np.array(["A"]*5+["B"]*2)
    t=support_table(y,p,g,min_class_support=2)
    assert (t.n_pos+t.n_neg==t.n).all() and t.loc["A","n_pos"]==3 and t.loc["A","n_neg"]==2
    assert t.loc["A","recall"]==2/3 and t.loc["A","fpr"]==1/2
    assert t.loc["A","recall_supported"] and not t.loc["B","fpr_supported"]
def test_rolling_folds_are_temporal_and_disjoint():
    from inf8239_u04.mitigation import rolling_origin_folds
    folds=rolling_origin_folds(480,240,80); assert len(folds)==3
    for tr,va in folds: assert tr.max()<va.min() and len(set(tr)&set(va))==0
def test_bootstrap_interval_is_ordered_and_bounded():
    y=np.array([1,0,1,0]*20); s=np.array(["G1"]*40+["G2"]*40); ci=bootstrap_gaps(y,y,s,n=50)
    assert ci["recall_gap"]["p97.5"]==0 and 0<=ci["fpr_gap"]["p2.5"]<=ci["fpr_gap"]["p97.5"]<=1
