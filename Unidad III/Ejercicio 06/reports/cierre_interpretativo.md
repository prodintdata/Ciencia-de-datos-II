# Cierre interpretativo · U03.LAB10

Evidencias: `ae_vae_panel.png`, `nearest_neighbors.png`, `interpolation.png`, `loss_curves.png`, `training_metrics.json` y `notebooks/01_ae_vae_fashion_mnist.ipynb`.
Configuración: semilla 42, AE de 6 épocas, VAE de 8 épocas, CPU.

**Resultado de reconstrucción:** El AE (latente de 16 dimensiones) reconstruye mejor que el VAE (latente de 2):

| | MSE en prueba | BCE por imagen |
|---|---|---|
| AE | 0.0203 | 240.5 |
| VAE | 0.0331 | 267.2 |

- El AE conserva la silueta y algo de detalle, como las correas de las sandalias y la forma del bolso.
- El VAE produce siluetas promedio: convierte sandalias en botines y bolsos en prendas superiores.
- Ambos pierden texturas y logotipos. Las curvas del AE muestran que entrenamiento y validación bajan juntos, sin sobreajuste.

**Resultado de generación:** El VAE produce siluetas reconocibles desde z ~ N(0, I): calzado, prendas superiores y pantalones o vestidos. Pero son oscuras y borrosas: su intensidad media es 0.129, frente a 0.267 en imágenes reales. Ninguna muestra alcanza la nitidez de una imagen real.

**Evidencia de diversidad:**
- La distancia media entre pares de las 16 muestras es 3.67, frente a 11.66 en 16 imágenes reales.
- Las muestras se agrupan en 3 o 4 prototipos y tienen solo 12 vecinos de entrenamiento distintos.
- No es un colapso total (hay más de una clase), pero la diversidad es baja.
- Los vecinos están a una distancia media de 2.32, incluso menor que la de las imágenes de prueba (3.89). Sin embargo, la comparación visual indica que no son copias: son promedios difusos parecidos a prendas oscuras y lisas.

**Comportamiento del espacio latente:**
- La KL se estabiliza en torno a 6.2 en entrenamiento y es de 6.34 en prueba, lo que indica que el latente se usa y no colapsa.
- La interpolación de (−2, −1) a (2, 1) recorre de forma gradual botín → prenda superior → pantalón, señal de que el espacio es continuo.
- Los puntos intermedios mezclan clases y no son prendas plausibles. Con 2 dimensiones, las 10 clases se solapan.

**Costo computacional:**

| | Tiempo de entrenamiento (CPU i7-1165G7) | Parámetros | Tamaño en disco |
|---|---|---|---|
| AE | 11.2–18.5 s | 25.9 mil | 339 KB |
| VAE | 16.7–34.4 s | 202.5 mil | 853 KB (codificador + decodificador) |

El tiempo varía con la carga del equipo; las métricas no. La inferencia de la app (un punto latente) es inmediata. El costo no justifica usar GPU en este laboratorio.

**Riesgo o limitación:**
- Las reconstrucciones y muestras son borrosas y poco diversas, y hay confusión entre clases (sandalia ↔ botín, bolso ↔ prenda superior).
- La diversidad y la memoria se midieron sobre solo 16 muestras.
- La distancia L2 en píxeles no es una métrica perceptual ni una prueba de privacidad.
- Una imagen sintética no es automáticamente original, privada ni libre de sesgo; el modelo hereda la distribución de Fashion-MNIST.

**Decisión sobre uso previsto:**
- Se aprueba solo como demostración académica para explorar el espacio latente con inferencia local.
- El AE queda como referencia de reconstrucción y el VAE como el modelo que alimenta la app.
- No es apto para generar datos sintéticos de reemplazo ni para ningún uso comercial.
