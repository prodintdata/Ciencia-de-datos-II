from __future__ import annotations

import numpy as np


def _flatten(images: np.ndarray) -> np.ndarray:
    return images.reshape(len(images), -1).astype("float64")


def nearest_neighbors(queries: np.ndarray, reference: np.ndarray, batch_size: int = 10_000) -> tuple[np.ndarray, np.ndarray]:
    """Índice y distancia euclidiana del vecino más cercano en `reference` para cada consulta."""
    queries = _flatten(queries)
    query_norms = (queries ** 2).sum(axis=1)
    best_index = np.zeros(len(queries), dtype=int)
    best_distance = np.full(len(queries), np.inf)
    for start in range(0, len(reference), batch_size):
        block = _flatten(reference[start:start + batch_size])
        squared = query_norms[:, None] + (block ** 2).sum(axis=1)[None, :] - 2 * queries @ block.T
        candidates = np.sqrt(np.clip(squared, 0, None))
        local_index = candidates.argmin(axis=1)
        local_distance = candidates[np.arange(len(queries)), local_index]
        improved = local_distance < best_distance
        best_index[improved] = start + local_index[improved]
        best_distance[improved] = local_distance[improved]
    return best_index, best_distance


def mean_pairwise_distance(images: np.ndarray) -> float:
    """Distancia euclidiana media entre pares distintos; valores bajos indican poca diversidad."""
    values = _flatten(images)
    if len(values) < 2:
        raise ValueError("Se requieren al menos dos imágenes")
    differences = values[:, None, :] - values[None, :, :]
    distances = np.sqrt((differences ** 2).sum(axis=2))
    upper = np.triu_indices(len(values), k=1)
    return float(distances[upper].mean())


def reconstruction_errors(originals: np.ndarray, reconstructed: np.ndarray) -> dict[str, float]:
    """MSE y entropía cruzada binaria media por imagen (suma sobre píxeles)."""
    clipped = np.clip(reconstructed, 1e-7, 1 - 1e-7)
    bce = -(originals * np.log(clipped) + (1 - originals) * np.log(1 - clipped))
    return {"mse": float(((originals - reconstructed) ** 2).mean()),
            "bce_per_image": float(bce.reshape(len(originals), -1).sum(axis=1).mean())}
