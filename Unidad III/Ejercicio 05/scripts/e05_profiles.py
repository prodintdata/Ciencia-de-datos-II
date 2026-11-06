"""Ejercicio 05: tres perfiles (historial amplio, historial pequeño, usuario nuevo) con la configuración elegida."""

from __future__ import annotations

import argparse
import json

import pandas as pd

from inf8239_u03.config import MOVIELENS_DIR, ROOT
from inf8239_u03.data import load_movielens
from inf8239_u03.recommenders import (
    GenreProfile,
    MatrixFactorization,
    hybrid_rerank,
    popularity_ranking,
    popularity_top_n,
    temporal_leave_one_out,
)

parser = argparse.ArgumentParser()
parser.add_argument("--factors", type=int, default=20)
parser.add_argument("--epochs", type=int, default=12)
parser.add_argument("--alpha", type=float, default=0.75)
parser.add_argument("--seeds", type=int, nargs="+", default=[42, 123, 2026])
args = parser.parse_args()

ratings, movies = load_movielens(MOVIELENS_DIR)
train, _ = temporal_leave_one_out(ratings)
counts = train.groupby("userId").size()
wide_user, small_user = int(counts.idxmax()), int(counts.idxmin())
new_user = int(ratings["userId"].max()) + 1  # no existe en los datos: simula un usuario frío
genres = GenreProfile().fit(movies)
titles = movies.set_index("movieId")[["title", "genres"]]


def jaccard(a: list[int], b: list[int]) -> float:
    return len(set(a) & set(b)) / len(set(a) | set(b))


lists: dict[str, dict[int, list[int]]] = {"wide": {}, "small": {}}
rows, checks = [], {}
for seed in args.seeds:
    model = MatrixFactorization(factors=args.factors, seed=seed).fit(train, epochs=args.epochs)
    for label, user in [("wide", wide_user), ("small", small_user)]:
        history = train.loc[train["userId"].eq(user), ["movieId", "rating"]]
        seen = set(history["movieId"])
        pool = model.top_n(user, seen, 100)
        content = genres.scores(genres.profile(history), pool["movieId"])
        hybrid = hybrid_rerank(pool, content, args.alpha)
        lists[label][seed] = hybrid["movieId"].astype(int).tolist()
        if seed == args.seeds[0]:
            collaborative_only = hybrid_rerank(pool, content, 1.0)["movieId"].astype(int).tolist()
            content_only = hybrid_rerank(pool, content, 0.0)["movieId"].astype(int).tolist()
            checks[label] = {
                "userId": user,
                "train_ratings": len(history),
                "seen_in_list": len(seen & set(lists[label][seed])),
                "overlap_with_alpha_1": len(set(collaborative_only) & set(lists[label][seed])),
                "overlap_with_alpha_0": len(set(content_only) & set(lists[label][seed])),
            }
            for rank, row in enumerate(hybrid.itertuples(), start=1):
                rows.append({"profile": label, "userId": user, "rank": rank, "movieId": int(row.movieId),
                             **titles.loc[int(row.movieId)].to_dict(), "collaborative": round(row.normalized, 3),
                             "content": round(row.content_score, 3), "hybrid": round(row.hybrid_score, 3),
                             "source": "híbrido personalizado"})
    print(f"seed={seed} listo", flush=True)

for label in lists:
    pairs = [(a, b) for i, a in enumerate(args.seeds) for b in args.seeds[i + 1:]]
    checks[label]["mean_jaccard_across_seeds"] = sum(jaccard(lists[label][a], lists[label][b]) for a, b in pairs) / len(pairs)

# Usuario nuevo: el modelo no tiene vector para él, así que top_n devuelve vacío y se aplica el fallback.
fallback_model_rows = len(model.top_n(new_user, set(), 10))
fallback = popularity_top_n(popularity_ranking(train), set())
for rank, item in enumerate(fallback, start=1):
    rows.append({"profile": "new", "userId": new_user, "rank": rank, "movieId": item, **titles.loc[item].to_dict(),
                 "collaborative": None, "content": None, "hybrid": None, "source": "fallback popularidad; no personalizada"})
checks["new"] = {"userId": new_user, "train_ratings": 0, "collaborative_rows": fallback_model_rows, "fallback_items": len(fallback)}

pd.DataFrame(rows).to_csv(ROOT / "reports/profiles.csv", index=False)
(ROOT / "reports/profiles_checks.json").write_text(json.dumps({"config": vars(args), **checks}, indent=2), encoding="utf-8")
print(json.dumps(checks, indent=2))
