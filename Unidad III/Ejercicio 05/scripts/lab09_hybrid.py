from __future__ import annotations

import argparse
import json
from time import perf_counter

from sklearn.metrics import root_mean_squared_error

from inf8239_u03.config import MOVIELENS_DIR, RANDOM_STATE, ROOT
from inf8239_u03.data import load_movielens
from inf8239_u03.metrics import catalog_coverage, hit_rate_at_k, precision_at_k
from inf8239_u03.recommenders import (
    GenreProfile,
    MatrixFactorization,
    hybrid_rerank,
    popularity_ranking,
    temporal_leave_one_out,
)

parser = argparse.ArgumentParser()
parser.add_argument("--factors", type=int, default=20)
parser.add_argument("--epochs", type=int, default=12)
parser.add_argument("--alpha", type=float, default=0.75)
parser.add_argument("--seed", type=int, default=RANDOM_STATE)
args = parser.parse_args()

ratings, movies = load_movielens(MOVIELENS_DIR)
train, test = temporal_leave_one_out(ratings)
start = perf_counter()
model = MatrixFactorization(factors=args.factors, seed=args.seed).fit(train, epochs=args.epochs)
train_seconds = perf_counter() - start
evaluable = test[test["userId"].isin(model.user_index) & test["movieId"].isin(model.item_index)]
predictions = [model.predict(row.userId, row.movieId) for row in evaluable.itertuples()]
rmse = root_mean_squared_error(evaluable["rating"], predictions)
popular_items = popularity_ranking(train)
genres = GenreProfile().fit(movies)
recommendations = {}
for user_id in evaluable["userId"].unique():
    history = train.loc[train["userId"].eq(user_id), ["movieId", "rating"]]
    collaborative = model.top_n(user_id, set(history["movieId"]), 100)
    content_scores = genres.scores(genres.profile(history), collaborative["movieId"])
    recommendations[int(user_id)] = hybrid_rerank(collaborative, content_scores, args.alpha)["movieId"].astype(int).tolist()
metrics = {
    "rmse": float(rmse),
    "hit_rate_at_10": hit_rate_at_k(recommendations, evaluable, 10),
    "precision_at_10": precision_at_k(recommendations, evaluable, 10),
    "catalog_coverage": catalog_coverage(recommendations, len(model.items)),
    "train_seconds": train_seconds,
    "model_bytes": model.size_bytes,
    "factors": args.factors,
    "epochs": args.epochs,
    "alpha": args.alpha,
    "seed": args.seed,
    "cold_start_policy": "popularidad por cantidad y media; no personalizada",
}
(ROOT / "reports").mkdir(exist_ok=True)
(ROOT / "reports/hybrid_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
cold_start_items = popular_items[:10]
movies[movies["movieId"].isin(cold_start_items)].set_index("movieId").loc[cold_start_items].reset_index().to_csv(
    ROOT / "reports/cold_start_fallback.csv", index=False
)
print(json.dumps(metrics, indent=2))
