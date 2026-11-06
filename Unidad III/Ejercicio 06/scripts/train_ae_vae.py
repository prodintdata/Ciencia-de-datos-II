from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path
from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf

from inf8239_u03_gen.data import normalize_images, validate_images
from inf8239_u03_gen.evaluation import (
    mean_pairwise_distance,
    nearest_neighbors,
    reconstruction_errors,
)
from inf8239_u03_gen.models import build_autoencoder, build_encoder_decoder

ROOT = Path(__file__).resolve().parents[1]
SEED = 42
os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")
random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)


class VAE(tf.keras.Model):
    def __init__(self, encoder, decoder):
        super().__init__()
        self.encoder = encoder
        self.decoder = decoder
        self.loss_tracker = tf.keras.metrics.Mean(name="loss")
        self.reconstruction_tracker = tf.keras.metrics.Mean(name="reconstruction")
        self.kl_tracker = tf.keras.metrics.Mean(name="kl")

    @property
    def metrics(self):
        return [self.loss_tracker, self.reconstruction_tracker, self.kl_tracker]

    def train_step(self, data):
        images = data[0] if isinstance(data, tuple) else data
        with tf.GradientTape() as tape:
            mean, log_variance = self.encoder(images, training=True)
            epsilon = tf.random.normal(tf.shape(mean))
            latent = mean + tf.exp(0.5 * log_variance) * epsilon
            reconstruction = self.decoder(latent, training=True)
            reconstruction_loss = tf.reduce_mean(tf.reduce_sum(tf.keras.losses.binary_crossentropy(images, reconstruction), axis=(1, 2)))
            kl_loss = -0.5 * tf.reduce_mean(tf.reduce_sum(1 + log_variance - tf.square(mean) - tf.exp(log_variance), axis=1))
            total_loss = reconstruction_loss + kl_loss
        gradients = tape.gradient(total_loss, self.trainable_weights)
        self.optimizer.apply_gradients(zip(gradients, self.trainable_weights))
        self.loss_tracker.update_state(total_loss)
        self.reconstruction_tracker.update_state(reconstruction_loss)
        self.kl_tracker.update_state(kl_loss)
        return {metric.name: metric.result() for metric in self.metrics}


PANEL_SIZE = 16
CLASS_NAMES = ["T-shirt/top", "Trouser", "Pullover", "Dress", "Coat", "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"]


def image_panel(path: Path, rows, labels, titles=None):
    figure, axes = plt.subplots(len(rows), PANEL_SIZE, figsize=(PANEL_SIZE, len(rows) + 0.6))
    for row, collection in enumerate(rows):
        for column in range(PANEL_SIZE):
            axes[row, column].imshow(collection[column].squeeze(), cmap="gray", vmin=0, vmax=1)
            axes[row, column].axis("off")
            if titles is not None and titles[row] is not None:
                axes[row, column].set_title(titles[row][column], fontsize=7)
        axes[row, 0].text(-4, 14, labels[row], ha="right", va="center", fontsize=9)
    figure.tight_layout()
    figure.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(figure)


def loss_curves(path: Path, ae_history, vae_history):
    figure, axes = plt.subplots(1, 3, figsize=(13, 3.5))
    axes[0].plot(ae_history["loss"], marker="o", label="entrenamiento")
    axes[0].plot(ae_history["val_loss"], marker="o", label="validación")
    axes[0].set_title("AE · BCE media por píxel")
    axes[1].plot(vae_history["reconstruction"], marker="o", color="tab:green")
    axes[1].set_title("VAE · reconstrucción (BCE por imagen)")
    axes[2].plot(vae_history["kl"], marker="o", color="tab:red")
    axes[2].set_title("VAE · divergencia KL")
    for axis in axes:
        axis.set_xlabel("época")
        axis.grid(alpha=0.3)
    axes[0].legend()
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs-ae", type=int, default=6)
    parser.add_argument("--epochs-vae", type=int, default=8)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    reports = ROOT / "reports"
    models = ROOT / "models"
    reports.mkdir(exist_ok=True)
    models.mkdir(exist_ok=True)
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.fashion_mnist.load_data()
    x_train = normalize_images(x_train)
    x_test = normalize_images(x_test)
    if args.limit:
        x_train, y_train = x_train[: args.limit], y_train[: args.limit]
        x_test, y_test = x_test[: max(100, args.limit // 5)], y_test[: max(100, args.limit // 5)]
    validate_images(x_train)
    start = perf_counter()
    autoencoder = build_autoencoder(tf)
    autoencoder.compile(optimizer="adam", loss="binary_crossentropy")
    ae_history = autoencoder.fit(x_train, x_train, validation_split=0.1, epochs=args.epochs_ae, batch_size=256,
                                 callbacks=[tf.keras.callbacks.EarlyStopping(patience=2, restore_best_weights=True)], verbose=2)
    ae_seconds = perf_counter() - start
    encoder, decoder = build_encoder_decoder(tf, latent_dim=2)
    vae = VAE(encoder, decoder)
    vae.compile(optimizer="adam")
    start = perf_counter()
    vae_history = vae.fit(x_train, epochs=args.epochs_vae, batch_size=256, verbose=2)
    vae_seconds = perf_counter() - start
    loss_curves(reports / "loss_curves.png", ae_history.history, vae_history.history)

    # Evaluación sobre todo el conjunto de prueba (no usado en entrenamiento).
    ae_test = autoencoder.predict(x_test, batch_size=1024, verbose=0)
    test_mean, test_log_variance = encoder.predict(x_test, batch_size=1024, verbose=0)
    vae_test = decoder.predict(test_mean, batch_size=1024, verbose=0)
    test_kl = -0.5 * np.mean(np.sum(1 + test_log_variance - test_mean ** 2 - np.exp(test_log_variance), axis=1))

    # Panel no seleccionado: 16 índices de prueba elegidos con semilla fija.
    rng = np.random.default_rng(SEED)
    indices = np.sort(rng.choice(len(x_test), size=PANEL_SIZE, replace=False))
    originals = x_test[indices]
    generated = decoder.predict(rng.normal(size=(PANEL_SIZE, 2)), verbose=0)
    image_panel(reports / "ae_vae_panel.png", [originals, ae_test[indices], vae_test[indices], generated],
                ["Original", "AE", "VAE", "VAE muestra"], [[CLASS_NAMES[y_test[i]] for i in indices], None, None, None])

    # Vecinos más cercanos en entrenamiento: ¿la muestra copia o produce una variación?
    generated_index, generated_distance = nearest_neighbors(generated, x_train)
    _, test_distance = nearest_neighbors(originals, x_train)
    image_panel(reports / "nearest_neighbors.png", [generated, x_train[generated_index]],
                ["VAE muestra", "Vecino train"],
                [[f"d={value:.1f}" for value in generated_distance],
                 [CLASS_NAMES[y_train[i]] for i in generated_index]])

    grid = np.array([(1 - value) * np.array([-2.0, -1.0]) + value * np.array([2.0, 1.0]) for value in np.linspace(0, 1, 12)])
    interpolation = decoder.predict(grid, verbose=0)
    figure, axes = plt.subplots(1, 12, figsize=(12, 1.3))
    for axis, image in zip(axes, interpolation):
        axis.imshow(image.squeeze(), cmap="gray", vmin=0, vmax=1)
        axis.axis("off")
    figure.savefig(reports / "interpolation.png", dpi=170, bbox_inches="tight")
    plt.close(figure)
    autoencoder.save(models / "autoencoder.keras")
    encoder.save(models / "encoder.keras")
    decoder.save(models / "decoder.keras")
    metrics = {"seed": SEED, "epochs_ae_run": len(ae_history.history["loss"]), "epochs_vae_run": len(vae_history.history["loss"]),
               "train_size": len(x_train), "test_size": len(x_test),
               "ae_train_seconds": ae_seconds, "vae_train_seconds": vae_seconds,
               "ae_parameters": autoencoder.count_params(), "decoder_parameters": decoder.count_params(),
               "vae_parameters": encoder.count_params() + decoder.count_params(),
               "ae_test": reconstruction_errors(x_test, ae_test), "vae_test": reconstruction_errors(x_test, vae_test),
               "vae_test_kl": float(test_kl),
               "panel_test_indices": indices.tolist(),
               "diversity_generated": mean_pairwise_distance(generated),
               "diversity_test_panel": mean_pairwise_distance(originals),
               "nn_distance_generated_mean": float(generated_distance.mean()),
               "nn_distance_generated_min": float(generated_distance.min()),
               "nn_distance_test_mean": float(test_distance.mean()),
               "nn_unique_generated": len(set(generated_index.tolist())),
               "mean_intensity_generated": float(generated.mean()),
               "mean_intensity_test_panel": float(originals.mean()),
               "history": {name: {key: [float(value) for value in values] for key, values in history.history.items()}
                           for name, history in [("ae", ae_history), ("vae", vae_history)]}}
    (reports / "training_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
