import numpy as np
from inf8239_u04.data import load_data,features,temporal_split
from inf8239_u04.mitigation import bootstrap_gaps,threshold_predictions
from inf8239_u04.model import build_model
def test_lower_threshold_never_reduces_recall():
    tr,te=temporal_split(load_data()); m=build_model().fit(features(tr),tr.target)
    hi,lo=threshold_predictions(m,features(te),.5),threshold_predictions(m,features(te),.4)
    pos=te.target.to_numpy()==1; assert lo[pos].sum()>=hi[pos].sum()
def test_bootstrap_interval_is_ordered_and_bounded():
    y=np.array([1,0,1,0]*20); s=np.array(["G1"]*40+["G2"]*40); ci=bootstrap_gaps(y,y,s,n=50)
    assert ci["recall_gap"]["p97.5"]==0 and 0<=ci["fpr_gap"]["p2.5"]<=ci["fpr_gap"]["p97.5"]<=1
