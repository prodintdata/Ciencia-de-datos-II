# System Card · Recomendador

## Usuarios y propósito
Recomendador académico de películas (INF-8239, U03.E05) para comparar popularidad, contenido, factorización e híbrido en MovieLens Latest Small. No es un servicio en producción ni toma decisiones sobre personas.

## Catálogo y candidatos
- Catálogo evaluado: las 9,701 películas con al menos una valoración en entrenamiento (denominador de la cobertura).
- Se excluyen siempre las películas ya vistas por el usuario.
- El híbrido reordena las 100 películas mejor puntuadas por la factorización (pool colaborativo).

## Señales utilizadas
- Colaborativa: valoraciones explícitas (0.5–5) de entrenamiento.
- Contenido: TF-IDF de los géneros de `movies.csv`; perfil del usuario = promedio de sus películas ponderado por `rating - 2.5` (mínimo 0.1).
- No se usan etiquetas, texto libre ni datos personales (MovieLens no incluye demografía).

## Modelos y fallback
| Componente | Detalle |
|---|---|
| Popularidad suavizada (LAB08) | Media de la película mezclada con la media global; mínimo = percentil 80 de conteos |
| Contenido (LAB08) | Similitud coseno entre vectores TF-IDF de géneros |
| Factorización (LAB09) | SGD, media global + producto de factores latentes; lr 0.01, regularización 0.05, 12 épocas |
| Híbrido | `alpha · colaborativo + (1 - alpha) · contenido`, ambos normalizados min-max en el pool |
| Fallback (usuario nuevo) | Popularidad por cantidad de valoraciones y media; **no personalizada** |

Configuración elegida: **40 factores, alpha = 0.5** (ver `reports/pareto.csv`).

## Métricas offline
Corte temporal leave-last-out: la última valoración de cada usuario va a prueba (610 usuarios; 587 evaluables porque su película de prueba aparece en entrenamiento). Promedio de tres semillas (42, 123, 2026).

| Método | RMSE | HitRate@10 | Cobertura |
|---|---|---|---|
| Media global | 1.116 | – | – |
| Media por película | 1.050 | – | – |
| Popularidad | – | 0.043 | 1.2 % |
| Contenido puro | – | 0.002 | 7.8 % |
| Factorización (alpha = 1), 40 factores | 1.018 | 0.034 | 9.9 % |
| **Híbrido 40 factores, alpha = 0.5** | 1.018 | 0.039 | 10.8 % |

Precision@10 en este protocolo es HitRate@10 / 10, porque hay un solo ítem relevante por usuario.

## Cold start, cobertura y diversidad
- Usuario nuevo: sin vector latente ni historial; recibe el Top-10 de popularidad marcado como no personalizado.
- Usuario con 19 valoraciones (userId 53): la lista cambia casi por completo entre semillas (Jaccard medio 0.02), frente a 0.54 del usuario con 2,697 valoraciones (userId 414).
- Ítems nuevos: la factorización no puede recomendarlos; solo la señal de contenido los alcanza.
- La cobertura baja al subir alpha (más peso colaborativo) y sube con más factores.

## Riesgos y monitoreo
- Popularidad dominante: el baseline repite los mismos 10 títulos para todos.
- Burbuja de filtro: con alpha = 0 el híbrido baja a ~7 géneros distintos por lista, frente a ~11 con alpha = 1.
- Sesgo de selección y retroalimentación: solo se observa lo que la gente eligió ver; recomendar cambia lo que luego se valora.
- Sin demografía: no pueden afirmarse resultados por grupos.
- Monitoreo propuesto: HitRate y cobertura por semana, proporción de usuarios en fallback y repetición de títulos entre usuarios.
