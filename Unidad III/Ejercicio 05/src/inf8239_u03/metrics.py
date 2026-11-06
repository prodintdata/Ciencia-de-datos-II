from __future__ import annotations

import pandas as pd


def hit_rate_at_k(recommendations: dict[int, list[int]], truth: pd.DataFrame, k: int = 10) -> float:
    hits = []
    for row in truth.itertuples():
        if row.userId in recommendations:
            hits.append(int(row.movieId in recommendations[row.userId][:k]))
    return sum(hits) / len(hits) if hits else 0.0


def precision_at_k(recommendations: dict[int, list[int]], truth: pd.DataFrame, k: int = 10) -> float:
    relevant = truth.groupby("userId")["movieId"].apply(set)
    values = [len(set(recommendations[user][:k]) & items) / k for user, items in relevant.items() if user in recommendations]
    return sum(values) / len(values) if values else 0.0


def catalog_coverage(recommendations: dict[int, list[int]], catalog_size: int) -> float:
    recommended = {item for values in recommendations.values() for item in values}
    return len(recommended) / catalog_size if catalog_size else 0.0


def mean_distinct_genres(recommendations: dict[int, list[int]], genres: dict[int, str]) -> float:
    """Promedio de géneros distintos por lista; valores bajos indican sobre-especialización."""
    counts = [len({g for item in items for g in genres[item].split("|")}) for items in recommendations.values() if items]
    return sum(counts) / len(counts) if counts else 0.0


def pareto_dominated(table: pd.DataFrame, utility: list[str], cost: list[str]) -> pd.Series:
    """Una fila está dominada si otra tiene igual o mejor utilidad e igual o menor costo, y es estrictamente mejor en algo."""
    flags = []
    for index, row in table.iterrows():
        others = table.drop(index)
        no_worse = (others[utility] >= row[utility]).all(axis=1) & (others[cost] <= row[cost]).all(axis=1)
        better = (others[utility] > row[utility]).any(axis=1) | (others[cost] < row[cost]).any(axis=1)
        flags.append(bool((no_worse & better).any()))
    return pd.Series(flags, index=table.index, name="dominated")
