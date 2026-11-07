"""Corrections requested in the E07 review.

1. Support by class: recall is judged by the positives of each subgroup and FPR by its
   negatives (support_by_class.csv), with 95 % Wilson intervals.
2. The comparison in mitigation_comparison.csv used the same test set to choose the
   variant, so it stays exploratory. Here the chosen alternative (ExponentiatedGradient)
   is validated on data that played no part in that choice: expanding-window temporal
   folds built only from the training period (before 2026-09-25). The test set is not used.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from inf8239_u04.data import load_data, features, temporal_split
from inf8239_u04.fairness import intersectional, support_table
from inf8239_u04.governance import load_config
from inf8239_u04.mitigation import (fit_exponentiated_gradient, paired_bootstrap_diff, rolling_origin_folds,
                                    rule_predictions, summarize, threshold_predictions)
from inf8239_u04.model import build_model

MIN_CLASS_SUPPORT = 20
FIRST_TRAIN, FOLD_SIZE = 240, 80
# Validation criterion, fixed before running the folds:
CRITERION = {
    "recall_gap_diff_ci_high_below": 0.0,   # expgrad - base: whole 95 % interval below 0
    "min_pooled_recall": None,              # filled from configs/governance.yml (0.68)
    "max_fpr_increase": 0.05,               # pooled FPR may not rise more than 5 points
    "min_folds_with_lower_gap": "all",
}

out = Path("reports/e07"); out.mkdir(parents=True, exist_ok=True)
gates = load_config()["gates"]; CRITERION["min_pooled_recall"] = gates["min_recall"]
df = load_data(); train, test = temporal_split(df)


def variants(tr, te):
    X, Xt = features(tr), features(te)
    base = build_model("logistic").fit(X, tr.target)
    eg = fit_exponentiated_gradient(build_model("logistic"), X, tr.target, tr.protected_group)
    return {"logistic_t0.50": base.predict(Xt), "logistic_t0.40": threshold_predictions(base, Xt, .40),
            "expgrad_tpr_parity": eg(Xt), "rules_no_model": rule_predictions(te)}


# 1. Support by class on the test set (same predictions as LAB12 and E07)
test_preds = variants(train, test)
test_preds["tree"] = build_model("tree").fit(features(train), train.target).predict(features(test))
tables = []
for name in ("logistic_t0.50", "tree", "expgrad_tpr_parity"):
    for level, groups in (("group", test.protected_group), ("intersectional", intersectional(test))):
        t = support_table(test.target, test_preds[name], groups, MIN_CLASS_SUPPORT)
        t.insert(0, "level", level); t.insert(0, "variant", name); tables.append(t)
support = pd.concat(tables)
support.round(6).to_csv(out / "support_by_class.csv")

# 2. Temporal validation on the training period only
rows, pooled = [], {k: [] for k in ("y", "s", "logistic_t0.50", "logistic_t0.40", "expgrad_tpr_parity", "rules_no_model")}
for k, (tr_idx, va_idx) in enumerate(rolling_origin_folds(len(train), FIRST_TRAIN, FOLD_SIZE), start=1):
    tr, va = train.iloc[tr_idx], train.iloc[va_idx]
    preds = variants(tr, va)
    for name, p in preds.items():
        r = summarize(name, va.target, p, va.protected_group)
        r.update({"fold": k, "train_rows": len(tr), "valid_rows": len(va),
                  "valid_from": str(va.received_date.min().date()), "valid_to": str(va.received_date.max().date()),
                  "pos_G1": int(((va.protected_group == "G1") & (va.target == 1)).sum()),
                  "pos_G2": int(((va.protected_group == "G2") & (va.target == 1)).sum()),
                  "neg_G1": int(((va.protected_group == "G1") & (va.target == 0)).sum()),
                  "neg_G2": int(((va.protected_group == "G2") & (va.target == 0)).sum())})
        rows.append(r); pooled[name].append(p)
    pooled["y"].append(va.target.to_numpy()); pooled["s"].append(va.protected_group.to_numpy())
folds = pd.DataFrame(rows)
cols = ["fold", "valid_from", "valid_to", "train_rows", "valid_rows", "variant", "accuracy", "recall", "fpr",
        "selection_rate", "recall_gap", "fpr_gap", "recall_G1", "recall_G2", "fpr_G1", "fpr_G2",
        "pos_G1", "pos_G2", "neg_G1", "neg_G2"]
folds[cols].round(6).to_csv(out / "temporal_validation.csv", index=False)

y, s = np.concatenate(pooled["y"]), np.concatenate(pooled["s"])
P = {k: np.concatenate(v) for k, v in pooled.items() if k not in ("y", "s")}
pooled_rows = {k: {m: float(v) for m, v in summarize(k, y, p, s).items() if m != "variant"} for k, p in P.items()}
diff_gap = paired_bootstrap_diff(y, P["logistic_t0.50"], P["expgrad_tpr_parity"], s, "recall_gap")
diff_recall = paired_bootstrap_diff(y, P["logistic_t0.50"], P["expgrad_tpr_parity"], s, "recall")
diff_fpr = paired_bootstrap_diff(y, P["logistic_t0.50"], P["expgrad_tpr_parity"], s, "fpr")
fold_gaps = folds.pivot(index="fold", columns="variant", values="recall_gap")
lower_in_folds = int((fold_gaps["expgrad_tpr_parity"] < fold_gaps["logistic_t0.50"]).sum())
checks = {
    "recall_gap_reduction_ci_below_0": diff_gap["p97.5"] < CRITERION["recall_gap_diff_ci_high_below"],
    "pooled_recall_meets_gate": pooled_rows["expgrad_tpr_parity"]["recall"] >= CRITERION["min_pooled_recall"],
    "fpr_increase_within_limit": pooled_rows["expgrad_tpr_parity"]["fpr"] - pooled_rows["logistic_t0.50"]["fpr"] <= CRITERION["max_fpr_increase"],
    "lower_gap_in_all_folds": lower_in_folds == len(fold_gaps),
}
summary = {
    "design": {"data": "training period only (test set not used)", "first_train_rows": FIRST_TRAIN,
               "fold_size": FOLD_SIZE, "folds": len(fold_gaps), "pooled_valid_rows": int(len(y)),
               "pooled_pos_by_group": {g: int(((s == g) & (y == 1)).sum()) for g in ("G1", "G2")},
               "pooled_neg_by_group": {g: int(((s == g) & (y == 0)).sum()) for g in ("G1", "G2")},
               "bootstrap": {"resamples": 1000, "seed": 42, "paired": True}},
    "criterion": CRITERION,
    "pooled_metrics": pooled_rows,
    "expgrad_minus_base": {"recall_gap": diff_gap, "recall": diff_recall, "fpr": diff_fpr},
    "folds_with_lower_recall_gap": f"{lower_in_folds}/{len(fold_gaps)}",
    "checks": checks,
    "validated": bool(all(checks.values())),
}
(out / "validation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

pd.set_option("display.width", 200)
print("Support by class (test):")
print(support[["variant", "level", "n", "n_pos", "n_neg", "recall", "recall_ci_low", "recall_ci_high",
               "recall_supported", "fpr", "fpr_supported"]].round(3).to_string())
print("\nTemporal validation (training period only):")
print(folds[["fold", "valid_from", "valid_to", "variant", "recall", "fpr", "recall_gap", "fpr_gap", "recall_G1",
             "pos_G1", "pos_G2"]].round(3).to_string(index=False))
print(json.dumps({k: summary[k] for k in ("pooled_metrics", "expgrad_minus_base", "folds_with_lower_recall_gap",
                                          "checks", "validated")}, indent=2))
