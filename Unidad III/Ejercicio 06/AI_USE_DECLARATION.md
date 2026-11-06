# Declaración de uso de inteligencia artificial

## Herramientas utilizadas

Claude Code (modelo Claude Opus 5.5, de Anthropic), usado desde Visual Studio Code en octubre de 2026 como apoyo durante el Ejercicio 06.

## Propósito de cada uso

| Uso | Resultado |
|---|---|
| Revisar el proyecto frente a la guía LAB10 y el mandato de U03.E06 | Lista de evidencias faltantes: panel de 16 ejemplos, vecinos cercanos, curvas y métricas, notebook, `requirements.txt`, README y documentación. |
| Ampliar `scripts/train_ae_vae.py` | Panel de 16 índices de prueba elegidos con semilla, curvas de pérdida, métricas de prueba (MSE, BCE y KL), diversidad, vecinos cercanos, intensidad media y guardado del codificador. |
| Crear `src/inf8239_u03_gen/evaluation.py` y `tests/test_evaluation.py` | Funciones de vecino más cercano, diversidad y error de reconstrucción, con 3 pruebas unitarias. |
| Crear el notebook `notebooks/01_ae_vae_fashion_mnist.ipynb` | Recalcula las cifras desde los modelos guardados y comprueba que coinciden con `training_metrics.json`. |
| Diagnosticar errores del entorno | Causa del `Access is denied` de `uv` (OneDrive) y su solución. |
| Redactar borradores del README, `MODEL_CARD.md`, el cierre interpretativo, esta declaración y el informe PDF | Textos construidos a partir de las métricas y figuras generadas por el código. |

## Prompts o decisiones relevantes

Prompts (resumidos):
1. "Ponte en contexto de este laboratorio, ya hice estos pasos que pide el maestro", con la guía LAB10.
2. "Ya hice todo lo que pide el laboratorio, pero apóyame en lo que falte".
3. "Analiza y estudia lo que pide el maestro en este ejercicio", con el enunciado de U03.E06.
4. "No te inventes nada, solo haz lo que pide el maestro, crea otro PDF que sería el entregable", con el informe del Ejercicio 05 como referencia de formato y las capturas de LAB10 como evidencia.

Decisiones:
- No cambiar las arquitecturas, las épocas ni la función de pérdida del proyecto base. Los baselines son el AE y el VAE del laboratorio.
- Elegir los 16 ejemplos de prueba con `np.random.default_rng(42)`, para no seleccionar a mano los mejores.
- Usar distancia L2 en píxeles para los vecinos y la diversidad: es simple e interpretable, aunque no es perceptual.
- Fijar la escala de las imágenes en [0, 1], para que el contraste automático de matplotlib no oculte que las muestras son oscuras.

## Elementos verificados

- Ejecuté LAB10 en mi equipo: instalación con `uv`, entrenamiento, aplicación Streamlit y `uv export` (capturas E1 a E4 del informe).
- Tres ejecuciones del script con semilla 42 dieron métricas idénticas; solo cambió el tiempo.
- El notebook ejecutado recalcula las métricas desde los modelos guardados, y todas coinciden con `training_metrics.json`.
- `uv run pytest -q`: 7 pruebas pasan. `uv run ruff check`: sin errores.
- La aplicación Streamlit carga `models/decoder.keras` sin errores.
- Las tres referencias (Xiao et al., 2017; Kingma y Welling, 2013; Mitchell et al., 2019) tienen DOI; se comprobó que los tres resuelven en doi.org y que sus metadatos (título, autores y año) coinciden:
  - https://doi.org/10.48550/arXiv.1708.07747
  - https://doi.org/10.48550/arXiv.1312.6114
  - https://doi.org/10.1145/3287560.3287596

## Cambios realizados sobre resultados generados

- La afirmación "3 muestras comparten el mismo vecino" se corrigió tras recalcularla: hay 12 vecinos distintos para 16 muestras (uno compartido por 3 muestras y dos compartidos por 2).
- La descripción "muestras oscuras" se respaldó con una medida reproducible: la intensidad media (0.129 frente a 0.267), agregada al script y al notebook.
- El Model Card y el cierre se actualizaron con el rango real de tiempos de las ejecuciones, en lugar de un solo valor.

## Responsabilidad asumida

Asumo la responsabilidad del contenido entregado. Las métricas provienen de la ejecución real del código en mi equipo. Revisé el código, las cifras y las conclusiones, y puedo explicar cada parte del trabajo.
