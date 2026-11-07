from pathlib import Path
import numpy as np, pandas as pd, pytest, yaml
from inf8239_u04.data import PROHIBITED, REQUIRED, features, load_data, temporal_split
from inf8239_u04.governance import load_config
from inf8239_u04.monitoring import alerts, monthly_report, psi
from inf8239_u04.pipeline import evaluate, run

RACI=pd.read_csv("student_inputs/raci.csv")
ROLES={r.strip() for col in "RACI" for cell in RACI[col].dropna() for r in cell.split(";")}
INVENTORY=pd.read_csv("student_inputs/data_inventory.csv")
MON=yaml.safe_load(Path("configs/monitoring.yml").read_text(encoding="utf-8"))

def test_inventory_covers_every_column_and_identifier():
    collected=set(INVENTORY.loc[INVENTORY.status=="collected","field"])
    assert collected==REQUIRED and set(INVENTORY.loc[INVENTORY.status=="prohibited","field"])==PROHIBITED

def test_inventory_matches_model_features_and_excludes_protected_group():
    used=set(INVENTORY.loc[INVENTORY.used_in_model=="sí","field"])
    assert used==set(features(load_data()).columns) and "protected_group" not in used

def test_every_collected_field_has_minimization_retention_and_access():
    rows=INVENTORY[INVENTORY.status=="collected"]
    assert not rows[["purpose","minimization","retention","access"]].isna().any().any()

def test_retention_owners_are_raci_roles():
    ret=pd.read_csv("student_inputs/retention_policy.csv")
    assert not ret.retention.isna().any() and set(ret.owner)|set(ret.accountable)<=ROLES

def test_handoffs_signed_by_activity_accountable_with_existing_evidence():
    hand=pd.read_csv("student_inputs/handoffs.csv"); accountable=dict(zip(RACI.activity,RACI.A))
    for h in hand.itertuples():
        assert {h.from_role,h.to_role}<=ROLES and h.sign_off==accountable[h.raci_activity]
        assert all(Path(p.strip()).exists() for p in h.evidence.split(";")), h.stage

def test_monitoring_owners_in_raci_and_thresholds_match_gates():
    gates=load_config()["gates"]; t=MON["thresholds"]
    assert all({s["owner"],s["accountable"]}<=ROLES for s in MON["signals"])
    assert (t["min_recall"],t["max_recall_gap"],t["max_fpr_gap"])==(gates["min_recall"],gates["max_recall_gap"],gates["max_fpr_gap"])

def test_psi_detects_shift_but_not_identical_distribution():
    x=pd.Series(np.random.default_rng(42).normal(size=500))
    assert psi(x,x)<0.01 and psi(x,x+1)>MON["thresholds"]["psi_action"]

def test_gaps_not_interpreted_without_support():
    df=load_data(); r=run(df,load_config()["gates"])
    monthly=monthly_report(r["test"],r["pred"],MON["min_support"]); found=alerts(monthly,pd.DataFrame(columns=["feature","psi"]),MON)
    unsupported=set(monthly.loc[~monthly.support_ok,"month"])
    assert not found[found.month.isin(unsupported)&found.signal.isin(["recall_gap","fpr_gap"])].shape[0]

def test_november_fpr_gap_keeps_mitigated_variant_in_review():
    # The tolerance is not relaxed after seeing the result; EG stays in REVIEW.
    from inf8239_u04.mitigation import fit_exponentiated_gradient
    from inf8239_u04.model import build_model
    from inf8239_u04.monitoring import month_gap_bootstrap, variant_status
    df=load_data(); train,_=temporal_split(df); r=run(df,load_config()["gates"])
    eg=fit_exponentiated_gradient(build_model("logistic"),features(train),train.target,train.protected_group)
    pred=eg(features(r["test"])); monthly=monthly_report(r["test"],pred,MON["min_support"])
    status=variant_status(alerts(monthly,pd.DataFrame(columns=["feature","psi"]),MON))
    assert status["status"]=="REVIEW" and "fpr_gap@2026-11" in status["failed"]
    assert MON["thresholds"]["max_fpr_gap"]==0.16
    gaps=month_gap_bootstrap(r["test"],pred,"2026-11","fpr")
    assert np.percentile(gaps,2.5)<MON["thresholds"]["max_fpr_gap"]<np.percentile(gaps,97.5)

def test_drill_ingestion_failure_triggers_review_and_recovers():
    df=load_data(); gates=load_config()["gates"]; base=run(df,gates); _,test=temporal_split(df)
    bad=test.copy(); bad.loc[bad.zone=="Oeste","previous_incidents"]=0
    assert evaluate(base["model"],bad,base["resources"],gates)["decision"]["status"]=="REVIEW"
    assert evaluate(base["model"],test,base["resources"],gates)["decision"]["status"]=="GO"
