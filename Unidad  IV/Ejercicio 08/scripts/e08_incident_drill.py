"""Simulacro E08: fallo de ingesta que deja previous_incidents en 0 para la zona Oeste.
Recorre detección, contención, preservación de evidencia, recuperación y verificación, y deja todo en reports/e08/incident_drill/."""
import hashlib, json, shutil
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import yaml
from inf8239_u04.data import features, load_data, temporal_split, validate_schema
from inf8239_u04.governance import load_config, model_version, recommendation
from inf8239_u04.monitoring import psi
from inf8239_u04.pipeline import evaluate, run

OUT=Path("reports/e08/incident_drill"); OUT.mkdir(parents=True,exist_ok=True)
now=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
sha=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=load_config(); mon=yaml.safe_load(Path("configs/monitoring.yml").read_text(encoding="utf-8")); timeline=[]
def step(name, owner, detail): timeline.append({"at":now(),"step":name,"owner":owner,"detail":detail}); print(f"[{name}] {detail}")
def summary(r): return {"metrics":r["metrics"],"gaps":r["gaps"],"decision":r["decision"]}

df=load_data(); train,test=temporal_split(df); base=run(df,cfg["gates"])
step("baseline","Ingeniero de ML",f"decisión {base['decision']['status']} con el lote correcto")

# 1. Contrato: un lote con identificador directo se rechaza antes de predecir.
try: validate_schema(test.assign(email="x@example.org")); contract="aceptado"
except ValueError as e: contract=f"rechazado: {e}"
step("contrato","Ingeniero de datos",f"lote con columna email {contract}")

# 2. Incidente: la migración de la fuente deja previous_incidents en 0 para la zona Oeste.
bad=test.copy(); bad.loc[bad.zone=="Oeste","previous_incidents"]=0
drift_psi=psi(train.previous_incidents,bad.previous_incidents)
# A failure in one zone is diluted in the global PSI; the per-zone PSI shows it.
zone_psi={z:round(psi(train.loc[train.zone==z,"previous_incidents"],bad.loc[bad.zone==z,"previous_incidents"]),4) for z in sorted(bad.zone.unique())}
step("detección sin etiquetas","Ingeniero de ML",f"PSI previous_incidents global = {drift_psi:.3f}; por zona = {zone_psi} (acción >= {mon['thresholds']['psi_action']})")
incident=evaluate(base["model"],bad,base["resources"],cfg["gates"])
step("detección con etiquetas","Ingeniero de ML",f"decisión {incident['decision']['status']}; puertas fallidas {incident['decision']['failed']}")

# 3. Contención: REVIEW, cola en FIFO y lote en cuarentena.
step("contención","Ingeniero de ML; Científico de datos","sistema en REVIEW, cola en FIFO, lote en cuarentena")

# 4. Preservación de evidencia: solo agregados y hashes, nunca filas de casos.
for src in ("configs/governance.yml","configs/monitoring.yml","student_inputs/raci.csv"): shutil.copy(src,OUT/Path(src).name)
(OUT/"decision_baseline.json").write_text(json.dumps(summary(base),indent=2),encoding="utf-8")
(OUT/"decision_incident.json").write_text(json.dumps({**summary(incident),"recommendation":recommendation(incident["decision"],cfg,model_version())},indent=2,ensure_ascii=False),encoding="utf-8")
incident["by_group"].to_csv(OUT/"fairness_incident.csv")
zeros=lambda d: d.previous_incidents.eq(0).groupby(d.zone).mean()
pd.DataFrame({"n_batch":bad.zone.value_counts(),"share_zero_reference":zeros(train),"share_zero_batch":zeros(bad),"psi_previous_incidents":pd.Series(zone_psi)}
             ).rename_axis("zone").round(4).to_csv(OUT/"batch_profile.csv")
step("evidencia","Científico de datos","configuración, RACI, decisiones y perfil agregado del lote preservados")

# 5. Recuperación: lote corregido en la fuente; se verifica que las puertas vuelven a pasar.
recovered=evaluate(base["model"],test,base["resources"],cfg["gates"])
(OUT/"decision_recovered.json").write_text(json.dumps(summary(recovered),indent=2),encoding="utf-8")
step("recuperación","Ingeniero de datos",f"lote corregido: decisión {recovered['decision']['status']}; reactivación pendiente de firma de la Dirección")

files=sorted(p for p in OUT.iterdir() if p.name not in ("manifest.json","timeline.json"))
(OUT/"timeline.json").write_text(json.dumps({"scenario":"previous_incidents = 0 en la zona Oeste por fallo de ingesta","contract_check":contract,
    "psi_previous_incidents":round(drift_psi,4),"psi_previous_incidents_by_zone":zone_psi,"timeline":timeline},indent=2,ensure_ascii=False),encoding="utf-8")
manifest={"created_at":now(),"model_version":model_version(),"model_sha256":sha("models/model.joblib"),
          "files":{p.name:sha(p) for p in files+[OUT/"timeline.json"]}}
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8"); print(OUT/"manifest.json")
