import json, time
from pathlib import Path
import pandas as pd
from inf8239_u04.data import load_data,features,temporal_split
from inf8239_u04.fairness import audit,intersectional
from inf8239_u04.governance import load_config
from inf8239_u04.mitigation import summarize,rule_predictions,threshold_predictions,fit_exponentiated_gradient,bootstrap_gaps
from inf8239_u04.model import build_model
out=Path("reports/e07"); out.mkdir(parents=True,exist_ok=True); gates=load_config()["gates"]
df=load_data(); train,test=temporal_split(df); X,Xt=features(train),features(test)
preds={"rules_no_model":rule_predictions(test)}
start=time.perf_counter(); base=build_model("logistic").fit(X,train.target); base_seconds=time.perf_counter()-start; preds["logistic_t0.50"]=base.predict(Xt)
for t in (0.45,0.40): preds[f"logistic_t{t:.2f}"]=threshold_predictions(base,Xt,t)
start=time.perf_counter(); eg=fit_exponentiated_gradient(build_model("logistic"),X,train.target,train.protected_group); eg_seconds=time.perf_counter()-start; preds["expgrad_tpr_parity"]=eg(Xt)
table=pd.DataFrame([summarize(k,test.target,p,test.protected_group) for k,p in preds.items()])
table["meets_gates"]=(table.recall>=gates["min_recall"])&(table.recall_gap<=gates["max_recall_gap"])&(table.fpr_gap<=gates["max_fpr_gap"])
table.round(6).to_csv(out/"mitigation_comparison.csv",index=False)
ci={k:bootstrap_gaps(test.target,preds[k],test.protected_group) for k in ("logistic_t0.50","expgrad_tpr_parity")}
(out/"bootstrap_gaps.json").write_text(json.dumps({"n_test":len(test),"resamples":1000,"seed":42,"intervals_95":ci,"training_seconds":{"logistic":base_seconds,"expgrad_tpr_parity":eg_seconds}},indent=2),encoding="utf-8")
_,inter,_=audit(test.target,preds["expgrad_tpr_parity"],intersectional(test)); inter.to_csv(out/"expgrad_intersectional.csv")
print(table.round(3).to_string(index=False)); print(json.dumps(ci,indent=2)); print(inter.round(3)); print({"training_seconds":{"logistic":round(base_seconds,3),"expgrad_tpr_parity":round(eg_seconds,3)}})
