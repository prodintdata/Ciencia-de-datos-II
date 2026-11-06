import pandas as pd

from inf8239_u03.config import MOVIELENS_DIR, ROOT
from inf8239_u03.data import load_movielens
from inf8239_u03.recommenders import ContentRecommender, weighted_popularity

ratings, movies = load_movielens(MOVIELENS_DIR)
reports = ROOT / "reports"
reports.mkdir(exist_ok=True)
popular = weighted_popularity(ratings, movies).head(10)
popular[["title", "count", "mean", "weighted_score"]].to_csv(reports / "popular_top10.csv")
title = "Toy Story (1995)"
model = ContentRecommender().fit(movies)
recommendations = model.recommend(title, 10)
recommendations.to_csv(reports / "content_recommendations.csv", index=False)
print("Popularidad:\n", popular[["title", "count", "mean", "weighted_score"]])
print(f"\nSimilares a {title}:\n", recommendations)

# Tres consultas de géneros distintos para comparar listas, empates y sobre-especialización.
queries = ["Toy Story (1995)", "Godfather, The (1972)", "Alien (1979)"]
frames = []
for query in queries:
    result = model.recommend(query, 10)
    result.insert(0, "query_genres", movies.loc[movies["title"].eq(query), "genres"].iloc[0])
    result.insert(0, "query", query)
    result["same_genres_as_query"] = result["genres"].eq(result["query_genres"])
    frames.append(result)
queries_table = pd.concat(frames, ignore_index=True)
queries_table.to_csv(reports / "content_queries.csv", index=False)
summary = queries_table.groupby("query", sort=False).agg(
    ties_at_top=("content_score", lambda s: int((s == s.max()).sum())),
    same_genres=("same_genres_as_query", "sum"),
    min_score=("content_score", "min"),
)
print("\nResumen de las tres consultas:\n", summary)
