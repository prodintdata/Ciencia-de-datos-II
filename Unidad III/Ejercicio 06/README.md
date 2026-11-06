# INF-8239 · Unidad 03 · Autoencoder y VAE con Fashion-MNIST (U03.E06)

Estudiante: Jhonatan Cabral (BE2322). Proyecto base y laboratorio: Edwin Ramón José Nolasco.

Consolida LAB10: un autoencoder (AE) y un autoencoder variacional (VAE) comparados por reconstrucción, muestreo, interpolación, diversidad, memoria y costo.

## Datos y licencia
Fashion-MNIST (Xiao, Rasul y Vollgraf, 2017; https://doi.org/10.48550/arXiv.1708.07747), licencia MIT.
- Tiene 70,000 imágenes de 28×28 en escala de grises y 10 clases balanceadas.
- **No se versiona**: Keras lo descarga en `~/.keras/datasets` la primera vez que se entrena.
- Este proyecto no usa ni redistribuye MovieLens.

## Reproducir
```bash
uv python install 3.12
uv sync --extra cpu                                   # GPU solo en WSL2/Linux: uv sync --extra gpu
uv run python scripts/check_runtime.py
uv run pytest -q                                      # 7 pruebas
uv run python scripts/train_ae_vae.py --epochs-ae 6 --epochs-vae 8
uv run jupyter nbconvert --to notebook --execute --inplace notebooks/01_ae_vae_fashion_mnist.ipynb
uv run streamlit run app/streamlit_app.py
```
Sin uv: `pip install -r requirements.txt` y `pip install -e .` (Python 3.12, CPU).

El orden importa: el script entrena y guarda los modelos y los reportes; el notebook los carga sin reentrenar y verifica que las cifras coinciden con `reports/training_metrics.json`. La semilla 42 fija los pesos iniciales, la selección del panel y las muestras. Con la misma semilla, el script reproduce exactamente las mismas métricas; solo cambia el tiempo de entrenamiento.

> Si el proyecto está en una carpeta sincronizada con OneDrive y `uv` responde `Access is denied` u `os error 5`, quite el atributo de solo lectura con `attrib -R /S /D ".venv\*"` y repita `uv sync --extra cpu`.

## Estructura
| Ruta | Contenido |
|---|---|
| `src/inf8239_u03_gen/` | `data.py`: normalización y validación. `models.py`: arquitecturas del AE y el VAE. `evaluation.py`: vecino más cercano, diversidad y error de reconstrucción |
| `scripts/` | `check_runtime.py`: entorno. `train_ae_vae.py`: entrenamiento, evaluación sobre prueba, figuras y métricas |
| `notebooks/` | Notebook ejecutado que recalcula y verifica las cifras desde los modelos guardados |
| `tests/` | Contratos de datos, forma de salida de los modelos y funciones de evaluación |
| `models/` | `autoencoder.keras`, `encoder.keras` y `decoder.keras` (este último es el que usa la app) |
| `reports/` | Métricas, panel no seleccionado, vecinos cercanos, interpolación, curvas y cierre interpretativo |
| `app/` | Aplicación Streamlit que solo hace inferencia: dos sliders recorren el latente del VAE |
| `MODEL_CARD.md`, `AI_USE_DECLARATION.md` | Model Card y declaración de uso de IA |

## Resultados principales (prueba, 10,000 imágenes, semilla 42)
| Modelo | Latente | MSE por píxel | BCE por imagen | KL | Parámetros |
|---|---|---|---|---|---|
| AE | 16 | **0.0203** | **240.5** | – | 25,888 |
| VAE (reconstrucción con μ) | 2 | 0.0331 | 267.2 | 6.34 | 202,516 |

| Indicador sobre 16 muestras del VAE | Muestras VAE | 16 imágenes reales de prueba |
|---|---|---|
| Distancia media entre pares (diversidad) | 3.67 | 11.66 |
| Distancia media al vecino de entrenamiento (memoria) | 2.32 | 3.89 |
| Intensidad media de píxel | 0.129 | 0.267 |

## Interpretación
- El AE reconstruye mejor, pero un error bajo no lo convierte en generador.
- El VAE permite muestrear e interpolar en un espacio continuo, aunque sus muestras son oscuras, borrosas y poco diversas.
- Las muestras quedan más cerca del entrenamiento que las imágenes reales, pero no son copias: son promedios difusos.
- Una imagen sintética no es automáticamente privada, original ni libre de sesgo.
- Uso previsto: solo demostración académica. Ver [MODEL_CARD.md](MODEL_CARD.md) y [reports/cierre_interpretativo.md](reports/cierre_interpretativo.md).
