# Model Card · Autoencoder y VAE

Formato basado en Mitchell et al. (2019), *Model Cards for Model Reporting*, https://doi.org/10.1145/3287560.3287596.

## Modelos y versiones

| Modelo | Archivos | Versión | Latente | Parámetros |
|---|---|---|---|---|
| Autoencoder denso (AE) | `models/autoencoder.keras` | 0.1.0 | 16 dimensiones (ReLU) | 25,888 |
| VAE denso | `models/encoder.keras`, `models/decoder.keras` | 0.1.0 | 2 dimensiones (media y log-varianza) | 202,516 (decodificador: 101,520) |

- Entorno: Python 3.12.13, TensorFlow 2.21.0 (CPU) y Keras 3.15.1, gestionados con `uv`.
- Semilla: 42 (`random`, `numpy` y `tensorflow`, con `TF_DETERMINISTIC_OPS=1`).
- Comando de entrenamiento: `scripts/train_ae_vae.py --epochs-ae 6 --epochs-vae 8`, con Adam y batch de 256.
- Reproducibilidad: tres ejecuciones del script dieron métricas de prueba, panel, diversidad y vecinos idénticos. Solo cambió el tiempo. El notebook `notebooks/01_ae_vae_fashion_mnist.ipynb` recalcula las cifras desde los modelos guardados y obtiene los mismos valores.

## Uso previsto y usuarios

- Demostración académica para INF-8239, dirigida a estudiantes y docentes.
- Sirve para comparar reconstrucción y generación entre un AE y un VAE, y para explorar visualmente un espacio latente de 2 dimensiones con la app de Streamlit.
- La aplicación solo hace inferencia con el decodificador; nunca entrena.

## Usos fuera de alcance

- Diseño de moda real, catálogos comerciales o cualquier producto final.
- Generar datos sintéticos para "anonimizar" o reemplazar datos reales: una muestra sintética no es automáticamente privada, original ni libre de sesgo.
- Clasificar prendas o detectar anomalías en producción sin una validación específica.
- Aplicarlo a otros dominios (fotos a color, rostros, imágenes médicas) sin reentrenar ni validar.

## Dataset, licencia y particiones

- **Fashion-MNIST** (Xiao, Rasul y Vollgraf, 2017, https://doi.org/10.48550/arXiv.1708.07747), con licencia MIT: imágenes de 28×28 en escala de grises y 10 clases.
- Entrenamiento: 60,000 imágenes, 6,000 por clase.
  - El AE reserva el 10 % final como validación (`validation_split=0.1`): 54,000 para entrenar y 6,000 para validar.
  - El VAE entrena con las 60,000, sin validación.
- Prueba: 10,000 imágenes (1,000 por clase), usadas solo para la evaluación final.
- Preprocesamiento: normalización a [0, 1] y forma (28, 28, 1), comprobados con `validate_images`.
- El dataset no se versiona: Keras lo descarga.

## Arquitectura y espacio latente

- **AE**: `Flatten → Dense(16, relu) → Dense(784, sigmoid) → Reshape`. Pérdida: entropía cruzada binaria (BCE). Usa EarlyStopping con paciencia 2 y conserva los mejores pesos; las 6 épocas se completaron.
- **VAE** (Kingma y Welling, 2013, https://doi.org/10.48550/arXiv.1312.6114):
  - Codificador: `Flatten → Dense(128, relu) → [z_mean(2), z_log_var(2)]`.
  - Decodificador: `Dense(128, relu) → Dense(784, sigmoid)`.
  - Usa el truco de reparametrización `z = μ + exp(½·logσ²)·ε`.
  - Pérdida = BCE sumada por imagen + KL respecto de N(0, I), con peso 1.
- El latente de 2 dimensiones permite visualizarlo y explorarlo con dos sliders, pero limita mucho la cantidad de información que se puede conservar. Sus ejes no tienen un significado garantizado.

## Métricas de reconstrucción y generación

Todas las métricas se calcularon sobre las 10,000 imágenes de prueba (`reports/training_metrics.json`).

| Métrica (prueba) | AE (latente 16) | VAE (latente 2, usando μ) |
|---|---|---|
| MSE por píxel | **0.0203** | 0.0331 |
| BCE por imagen | **240.5** | 267.2 |
| KL media | — | 6.34 |

- Curvas de pérdida (`reports/loss_curves.png`):
  - AE: entrenamiento y validación bajan juntos (0.306 contra 0.307 en la última época). No hay señales de sobreajuste.
  - VAE: la reconstrucción baja de 330.1 a 267.4. La KL cae de 12.4 a cerca de 6.2 desde la época 4 y se mantiene ahí, por lo que no hay colapso del latente.
- El AE reconstruye mejor porque tiene un cuello de botella 8 veces más ancho y no paga el costo de la regularización KL.

## Diversidad y vecinos cercanos

El panel no seleccionado (`reports/ae_vae_panel.png`) usa 16 índices de prueba elegidos con semilla 42 y 16 puntos z ~ N(0, I).

| Indicador | Muestras VAE | 16 imágenes reales de prueba |
|---|---|---|
| Distancia L2 media entre pares (diversidad) | 3.67 | 11.66 |
| Distancia media al vecino más cercano de entrenamiento | 2.32 (mínimo 1.64) | 3.89 |
| Vecinos distintos de entrenamiento | 12 de 16 | — |
| Intensidad media de píxel | 0.129 | 0.267 |

- **Diversidad**: las muestras son unas 3 veces menos diversas que las imágenes reales. Visualmente se reducen a 3 o 4 prototipos (calzado, prenda superior y pantalón o vestido).
- **Vecinos cercanos** (`reports/nearest_neighbors.png`): las muestras quedan más cerca del entrenamiento que las propias imágenes de prueba, pero no son copias.
  - Son promedios difusos y oscuros: su intensidad media es la mitad que la de las imágenes reales.
  - En distancia L2, una imagen oscura queda cerca de prendas oscuras y lisas.
  - Solo hay 12 vecinos distintos: una imagen de entrenamiento es la vecina de 3 muestras y otras dos lo son de 2 cada una.
- **Interpolación** (`reports/interpolation.png`): la transición de botín a prenda superior y luego a pantalón es gradual. Los puntos intermedios son mezclas poco plausibles.

## Hardware, tiempo y tamaño

| Concepto | Valor |
|---|---|
| Hardware | Intel Core i7-1165G7 (CPU, 16 GB RAM), Windows 11, sin GPU (TensorFlow ≥ 2.11 no usa GPU en Windows nativo) |
| Tiempo de entrenamiento | AE: entre 11.2 y 18.5 s (6 épocas). VAE: entre 16.7 y 34.4 s (8 épocas), según la ejecución |
| Tamaño en disco | `autoencoder.keras`: 339 KB. `encoder.keras`: 427 KB. `decoder.keras`: 426 KB |
| Inferencia en la app | Un punto latente por consulta. Costo despreciable en CPU |

Los tiempos varían con la carga del equipo; las métricas no.

## Limitaciones, riesgos y supervisión

- **Calidad**: tanto las reconstrucciones como las muestras son borrosas, porque la BCE con capas densas favorece promedios. En el panel, el VAE convierte sandalias en botines y bolsos en prendas superiores, y ambos modelos pierden texturas y logotipos.
- **Diversidad**: la generación muestra poca variedad, medida sobre solo 16 muestras. No debe afirmarse que el VAE garantice diversidad.
- **Error bajo no implica buena generación**: el AE reconstruye mejor, pero no es un modelo generativo. Decodificar puntos arbitrarios de su latente no está garantizado.
- **Privacidad y originalidad**: el análisis de vecinos es solo un indicador (L2 en píxeles). No es una prueba formal de privacidad.
- **Validación del VAE**: el VAE no usa partición de validación; su único control externo es la evaluación sobre prueba.
- **Sesgo**: el modelo hereda la distribución de Fashion-MNIST (prendas de catálogo, centradas y con fondo negro).
- **Supervisión**: los resultados se revisaron con un panel no seleccionado. Cualquier uso fuera del aula requiere evaluar el modelo con métricas perceptuales y con revisión humana.
