"""Ejercicio 05: baselines, factorización con tres semillas, barrido de alpha y tabla de Pareto."""

from __future__ import annotations

import argparse
import json
from time import perf_counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import root_mean_squared_error

from inf8239_u03.config import MOVIELENS_DIR, ROOT
from inf8239_u03.data import load_movielens
from inf8239_u03.metrics import (
    catalog_coverage,
    hit_rate_at_k,
    mean_distinct_genres,
    pareto_dominated,
    precision_at_k,
)
from inf8239_u03.recommenders import (
    GenreProfile,
    MatrixFactorization,
    hybrid_rerank,
    popularity_ranking,
    popularity_top_n,
    temporal_leave_one_out,
)

parser = argparse.ArgumentParser()
parser.add_argument("--factors", type=int, nargs="+", default=[10, 20, 40])
parser.add_argument("--seeds", type=int, nargs="+", default=[42, 123, 2026])
parser.add_argument("--alphas", type=float, nargs="+", default=[0.0, 0.25, 0.5, 0.75, 1.0])
parser.add_argument("--epochs", type=int, default=12)
args = parser.parse_args()

reports = ROOT / "reports"
(reports / "figures").mkdir(parents=True, exist_ok=True)
ratings, movies = load_movielens(MOVIELENS_DIR)
train, test = temporal_leave_one_out(ratings)
catalog = sorted(train["movieId"].unique())
evaluable = test[test["movieId"].isin(catalog)]
genre_of = dict(zip(movies["movieId"].astype(int), movies["genres"]))
histories = {int(user): group[["movieId", "rating"]] for user, group in train.groupby("userId")}
genres = GenreProfile().fit(movies)
profiles = {user: genres.profile(history) for user, history in histories.items()}


def ranking_metrics(recommendations: dict[int, list[int]]) -> dict[str, float]:
    return {
        "hit_rate_at_10": hit_rate_at_k(recommendations, evaluable, 10),
        "precision_at_10": precision_at_k(recommendations, evaluable, 10),
        "catalog_coverage": catalog_coverage(recommendations, len(catalog)),
        "distinct_genres": mean_distinct_genres(recommendations, genre_of),
    }


# Baselines de ratings: ¿la factorización mejora a predecir la media?
global_mean = train["rating"].mean()
item_mean = train.groupby("movieId")["rating"].mean()
baselines = [
    {"method": "Media global (ratings)", "rmse": root_mean_squared_error(evaluable["rating"], np.full(len(evaluable), global_mean))},
    {"method": "Media por película (ratings)", "rmse": root_mean_squared_error(evaluable["rating"], evaluable["movieId"].map(item_mean))},
]

# Baselines de ranking: popularidad (no personalizada) y contenido puro sobre todo el catálogo no visto.
popular = popularity_ranking(train)
users = [int(user) for user in evaluable["userId"]]
seen_by = {user: set(histories[user]["movieId"]) for user in users}
popularity_recs = {user: popularity_top_n(popular, seen_by[user]) for user in users}
baselines.append({"method": "Popularidad (cantidad, media)", **ranking_metrics(popularity_recs)})
content_recs = {}
for user in users:
    candidates = [item for item in catalog if item not in seen_by[user]]
    scores = genres.scores(profiles[user], candidates)
    content_recs[user] = [candidates[i] for i in np.argsort(-scores, kind="stable")[:10]]
baselines.append({"method": "Contenido puro (perfil de géneros)", **ranking_metrics(content_recs)})
pd.DataFrame(baselines).to_csv(reports / "baselines.csv", index=False)

# Factorización: cada combinación de factores y semilla se entrena una vez; alpha solo reordena el pool de 100.
rows = []
for factors in args.factors:
    for seed in args.seeds:
        start = perf_counter()
        model = MatrixFactorization(factors=factors, seed=seed).fit(train, epochs=args.epochs)
        train_seconds = perf_counter() - start
        rmse = root_mean_squared_error(evaluable["rating"], [model.predict(r.userId, r.movieId) for r in evaluable.itertuples()])
        pools = {}
        for user in users:
            pool = model.top_n(user, seen_by[user], 100)
            pools[user] = (pool, genres.scores(profiles[user], pool["movieId"]))
        for alpha in args.alphas:
            recs = {user: hybrid_rerank(pool, content, alpha)["movieId"].astype(int).tolist() for user, (pool, content) in pools.items()}
            rows.append({"factors": factors, "seed": seed, "alpha": alpha, "epochs": args.epochs, "rmse": rmse,
                         **ranking_metrics(recs), "train_seconds": train_seconds, "model_bytes": model.size_bytes})
        print(f"factors={factors} seed={seed} rmse={rmse:.4f} t={train_seconds:.1f}s", flush=True)
experiments = pd.DataFrame(rows)
experiments.to_csv(reports / "experiments.csv", index=False)

# Pareto: utilidad = HitRate@10 y cobertura (más es mejor); costo = tiempo y tamaño (menos es mejor).
summary = experiments.groupby(["factors", "alpha"]).agg(
    hit_rate_mean=("hit_rate_at_10", "mean"), hit_rate_std=("hit_rate_at_10", "std"),
    coverage_mean=("catalog_coverage", "mean"), coverage_std=("catalog_coverage", "std"),
    distinct_genres=("distinct_genres", "mean"), rmse_mean=("rmse", "mean"),
    train_seconds_mean=("train_seconds", "mean"), model_bytes=("model_bytes", "first"),
).reset_index()
summary["dominated"] = pareto_dominated(summary, ["hit_rate_mean", "coverage_mean"], ["train_seconds_mean", "model_bytes"])
summary.to_csv(reports / "pareto.csv", index=False)
(reports / "experiments_config.json").write_text(json.dumps(vars(args), indent=2), encoding="utf-8")

# Figura: dos paneles con el mismo eje x (alpha); sin doble eje y.
colors = {10: "#2a78d6", 20: "#eb6834", 40: "#1baf7a"}
figure, axes = plt.subplots(1, 2, figsize=(10, 3.8))
for metric, axis, title, base_key in [("hit_rate", axes[0], "HitRate@10", "hit_rate_at_10"), ("coverage", axes[1], "Cobertura del catálogo", "catalog_coverage")]:
    for factors, group in summary.groupby("factors"):
        axis.errorbar(group["alpha"], group[f"{metric}_mean"], yerr=group[f"{metric}_std"], color=colors[factors],
                      marker="o", markersize=5, linewidth=2, capsize=3, label=f"{factors} factores")
    for method, style in [("Popularidad (cantidad, media)", ":"), ("Contenido puro (perfil de géneros)", "--")]:
        value = pd.DataFrame(baselines).set_index("method").loc[method, base_key]
        axis.axhline(value, color="#898781", linestyle=style, linewidth=1.2)
        axis.annotate(method.split(" (")[0], (1.0, value), xytext=(-4, 3), textcoords="offset points", ha="right", fontsize=8, color="#52514e")
    axis.set_title(title, fontsize=11)
    axis.set_xlabel("alpha (peso colaborativo)")
    axis.set_xticks(args.alphas)
    axis.grid(color="#e1e0d9", linewidth=0.6)
    axis.spines[["top", "right"]].set_visible(False)
axes[0].legend(frameon=False, fontsize=8)
figure.tight_layout()
figure.savefig(reports / "figures/alpha_tradeoff.png", dpi=200)
print(pd.DataFrame(baselines).to_string())
print(summary.round(4).to_string())
