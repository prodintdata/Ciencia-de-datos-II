import numpy as np
import pytest

from inf8239_u03_gen.evaluation import (
    mean_pairwise_distance,
    nearest_neighbors,
    reconstruction_errors,
)


def test_nearest_neighbor_finds_exact_copy_across_batches():
    reference = np.random.default_rng(0).random((25, 28, 28, 1))
    queries = reference[[3, 21]]
    index, distance = nearest_neighbors(queries, reference, batch_size=10)
    assert index.tolist() == [3, 21]
    assert np.allclose(distance, 0, atol=1e-6)


def test_identical_samples_have_zero_diversity():
    assert mean_pairwise_distance(np.ones((4, 28, 28, 1))) == 0
    assert mean_pairwise_distance(np.stack([np.zeros((28, 28, 1)), np.ones((28, 28, 1))])) == pytest.approx(28.0)


def test_perfect_reconstruction_has_zero_mse():
    images = np.random.default_rng(1).integers(0, 2, (3, 28, 28, 1)).astype("float32")
    errors = reconstruction_errors(images, images)
    assert errors["mse"] == 0
    assert errors["bce_per_image"] < 1e-3
