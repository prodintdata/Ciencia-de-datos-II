import json

import pandas as pd

from inf8239_u03.config import MOVIELENS_DIR, ROOT
from inf8239_u03.data import load_movielens

ratings, movies = load_movielens(MOVIELENS_DIR)
possible = ratings["userId"].nunique() * movies["movieId"].nunique()
print("Ratings:", ratings.shape, "Movies:", movies.shape)
print("Usuarios:", ratings["userId"].nunique(), "Ítems valorados:", ratings["movieId"].nunique())
print("Rango temporal:", ratings["timestamp"].min(), ratings["timestamp"].max())
print("Densidad:", len(ratings) / possible)
print(ratings["rating"].describe())

per_user = ratings.groupby("userId").size()
per_movie = ratings.groupby("movieId").size()
audit = {
    "ratings": len(ratings),
    "users": int(ratings["userId"].nunique()),
    "movies_in_catalog": len(movies),
    "movies_rated": int(ratings["movieId"].nunique()),
    "movies_without_ratings": int((~movies["movieId"].isin(ratings["movieId"])).sum()),
    "density": len(ratings) / possible,
    "nulls": int(ratings.isna().sum().sum() + movies.isna().sum().sum()),
    "duplicate_user_movie_pairs": int(ratings.duplicated(["userId", "movieId"]).sum()),
    "duplicate_movie_ids": int(movies["movieId"].duplicated().sum()),
    "orphan_ratings": int((~ratings["movieId"].isin(movies["movieId"])).sum()),
    "rating_min": float(ratings["rating"].min()),
    "rating_max": float(ratings["rating"].max()),
    "rating_mean": float(ratings["rating"].mean()),
    "rating_distribution": {str(k): int(v) for k, v in ratings["rating"].value_counts().sort_index().items()},
    "first_rating": str(pd.to_datetime(ratings["timestamp"].min(), unit="s").date()),
    "last_rating": str(pd.to_datetime(ratings["timestamp"].max(), unit="s").date()),
    "ratings_per_user_min": int(per_user.min()),
    "ratings_per_user_median": float(per_user.median()),
    "ratings_per_user_max": int(per_user.max()),
    "movies_with_one_rating": int((per_movie == 1).sum()),
    "movies_with_less_than_5_ratings": int((per_movie < 5).sum()),
    "movies_without_genres": int(movies["genres"].eq("(no genres listed)").sum()),
}
(ROOT / "reports").mkdir(exist_ok=True)
(ROOT / "reports/audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(audit, indent=2, ensure_ascii=False))
