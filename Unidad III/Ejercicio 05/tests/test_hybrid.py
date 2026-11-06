import numpy as np
import pandas as pd

from inf8239_u03.metrics import mean_distinct_genres, pareto_dominated, precision_at_k
from inf8239_u03.recommenders import (
    GenreProfile,
    MatrixFactorization,
    hybrid_rerank,
    popularity_ranking,
    popularity_top_n,
    temporal_leave_one_out,
)


def test_top_n_excludes_seen_and_matches_predict(sample_ratings):
    model = MatrixFactorization(factors=3, seed=42).fit(sample_ratings, epochs=2)
    result = model.top_n(1, {1, 2}, 5)
    assert not set(result["movieId"]) & {1, 2}
    for row in result.itertuples():
        assert np.isclose(row.collaborative_score, model.predict(1, row.movieId))


def test_unknown_user_has_no_collaborative_signal(sample_ratings):
    model = MatrixFactorization(factors=3, seed=42).fit(sample_ratings, epochs=2)
    assert model.top_n(999, set(), 5).empty


def test_popularity_fallback_excludes_seen(sample_ratings):
    ranking = popularity_ranking(sample_ratings)
    assert popularity_top_n(ranking, set(), 2) == ranking[:2]
    assert ranking[0] not in popularity_top_n(ranking, {ranking[0]}, 2)


def test_same_seed_is_reproducible(sample_ratings):
    first = MatrixFactorization(factors=3, seed=7).fit(sample_ratings, epochs=3)
    second = MatrixFactorization(factors=3, seed=7).fit(sample_ratings, epochs=3)
    assert np.allclose(first.item_factors, second.item_factors)


def test_temporal_split_never_trains_on_future(sample_ratings):
    train, test = temporal_leave_one_out(sample_ratings)
    merged = test.merge(train, on="userId", suffixes=("_test", "_train"))
    assert (merged["timestamp_train"] <= merged["timestamp_test"]).all()


def test_hybrid_alpha_extremes_follow_each_signal():
    pool = pd.DataFrame({"movieId": [1, 2, 3], "collaborative_score": [3.0, 2.0, 1.0]})
    content = np.array([0.0, 0.5, 1.0])
    assert hybrid_rerank(pool, content, 1.0, 3)["movieId"].tolist() == [1, 2, 3]
    assert hybrid_rerank(pool, content, 0.0, 3)["movieId"].tolist() == [3, 2, 1]


def test_genre_profile_prefers_liked_genres(sample_movies):
    genres = GenreProfile().fit(sample_movies)
    profile = genres.profile(pd.DataFrame({"movieId": [3], "rating": [5.0]}))
    scores = genres.scores(profile, [4, 5])
    assert scores[0] > scores[1]  # Delta comparte Drama con Gamma; Epsilon no


def test_precision_and_genre_diversity():
    recs = {1: [3, 2], 2: [4, 1]}
    truth = pd.DataFrame({"userId": [1, 2], "movieId": [3, 5]})
    assert precision_at_k(recs, truth, 2) == 0.25
    assert mean_distinct_genres({1: [1, 2]}, {1: "Drama|Comedy", 2: "Drama"}) == 2


def test_pareto_marks_dominated_configuration():
    table = pd.DataFrame({"hit": [0.04, 0.03, 0.05], "seconds": [10.0, 20.0, 40.0]})
    assert pareto_dominated(table, ["hit"], ["seconds"]).tolist() == [False, True, False]
