import math, pandas as pd, pytest
from inf8239_u04.governance import deployment_decision,validate_raci
def test_failed_gate_requires_review():
    d=deployment_decision({"recall":.5},{"recall_gap":.1,"fpr_gap":.1},{"latency_ms":1,"model_kb":5},{"min_recall":.7,"max_recall_gap":.2,"max_fpr_gap":.2,"max_latency_ms":10,"max_model_kb":20}); assert d["status"]=="REVIEW"
GATES={"min_recall":.7,"max_recall_gap":.2,"max_fpr_gap":.2,"max_latency_ms":10,"max_model_kb":20}
@pytest.mark.parametrize("field",["recall","recall_gap","fpr_gap","latency_ms","model_kb"])
def test_each_failed_gate_is_reported(field):
    m,g,r={"recall":.9},{"recall_gap":.1,"fpr_gap":.1},{"latency_ms":1,"model_kb":5}
    bad={"recall":.1,"recall_gap":.9,"fpr_gap":.9,"latency_ms":99,"model_kb":99}[field]
    for part in (m,g,r):
        if field in part: part[field]=bad
    d=deployment_decision(m,g,r,GATES); assert d["status"]=="REVIEW" and len(d["failed"])==1
def test_undefined_gap_is_not_hidden():
    from inf8239_u04.fairness import gap
    g=pd.DataFrame({"recall":[.8,float("nan")]},index=["G1","G2"])
    assert math.isnan(gap(g,"recall"))
    d=deployment_decision({"recall":.9},{"recall_gap":gap(g,"recall"),"fpr_gap":.1},{"latency_ms":1,"model_kb":5},GATES)
    assert d["status"]=="REVIEW" and d["failed"]==["recall_gap"]
def test_all_gates_pass_is_go():
    assert deployment_decision({"recall":.9},{"recall_gap":.1,"fpr_gap":.1},{"latency_ms":1,"model_kb":5},GATES)["status"]=="GO"
def test_raci_requires_accountable():
    with pytest.raises(ValueError): validate_raci(pd.DataFrame([{"activity":"deploy","R":"ML","A":"","C":"DS","I":"Users"}]))
def test_raci_rejects_two_accountables():
    with pytest.raises(ValueError,match="exactly one A"): validate_raci(pd.DataFrame([{"activity":"deploy","R":"ML","A":"Lead; Director","C":"DS","I":"Users"}]))
def test_student_raci_is_valid():
    assert validate_raci(pd.read_csv("student_inputs/raci.csv"))
def test_recommendation_is_traceable():
    from inf8239_u04.governance import load_config,recommendation
    d=deployment_decision({"recall":.1},{"recall_gap":.1,"fpr_gap":.1},{"latency_ms":1,"model_kb":5},GATES)
    rec=recommendation(d,load_config(),"logistic-test")
    assert rec["status"]=="REVIEW" and rec["model_version"]=="logistic-test" and rec["policy"]["gates"]
    assert rec["evidence"]["failed"]==["recall"] and "recall" in rec["human_action"]
