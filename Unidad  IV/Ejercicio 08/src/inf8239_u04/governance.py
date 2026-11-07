import math
from pathlib import Path
import pandas as pd
import yaml

def load_config(path="configs/governance.yml"):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))

def validate_raci(df):
    required={"activity","R","A","C","I"}
    if required-set(df.columns): raise ValueError("RACI columns missing")
    if df[["R","A"]].fillna("").apply(lambda s:s.str.strip().eq("")).any().any(): raise ValueError("Every activity needs R and A")
    if df["A"].astype(str).str.contains(r"[;,]").any(): raise ValueError("Every activity needs exactly one A")
    return True

def deployment_decision(metrics, gaps, resources, gates):
    # Missing or non-finite evidence fails the gate: it can never pass silently.
    ok=lambda v: v is not None and math.isfinite(v)
    checks={
      "recall": ok(metrics["recall"]) and metrics["recall"] >= gates["min_recall"],
      "recall_gap": ok(gaps["recall_gap"]) and gaps["recall_gap"] <= gates["max_recall_gap"],
      "fpr_gap": ok(gaps["fpr_gap"]) and gaps["fpr_gap"] <= gates["max_fpr_gap"],
      "latency": ok(resources["latency_ms"]) and resources["latency_ms"] <= gates["max_latency_ms"],
      "model_size": ok(resources["model_kb"]) and resources["model_kb"] <= gates["max_model_kb"],
    }
    failed=[k for k,v in checks.items() if not v]
    return {"status":"GO" if not failed else "REVIEW", "checks":checks, "failed":failed, "human_action":"Document review and final decision"}

EVIDENCE=["reports/lab13/deployment_decision.json","reports/lab13/fairness_by_group.csv","docs/MODEL_CARD.md","docs/RUNBOOK.md","student_inputs/raci.csv"]
AUTHORITY_LIMIT="El DSS prioriza revisión y presenta evidencia; no declara emergencias, culpabilidad, elegibilidad ni intervención automática."

def model_version(kind="logistic"):
    import sklearn, subprocess
    try: commit=subprocess.run(["git","rev-parse","--short","HEAD"],capture_output=True,text=True,check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError): commit="unversioned"
    return f"{kind}-sklearn{sklearn.__version__}-{commit}"

def recommendation(decision, cfg, version):
    # Traceable recommendation: version, policy, evidence and the human action it requires.
    if decision["status"]=="GO": action="El analista revisa cada caso priorizado y registra su decisión; la Dirección firma el despliegue."
    else: action=f"Un responsable humano analiza las puertas fallidas ({', '.join(decision['failed'])}) y registra su decisión; no se despliega hasta entonces."
    return {"status":decision["status"], "model_version":version,
            "policy":{"system":cfg["system_name"],"purpose":cfg["purpose"],"prohibited_uses":cfg["prohibited_uses"],"gates":cfg["gates"]},
            "evidence":{"checks":decision["checks"],"failed":decision["failed"],"files":EVIDENCE},
            "authority_limit":AUTHORITY_LIMIT, "human_action":action}
