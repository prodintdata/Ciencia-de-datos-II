# U04.LAB12 · Auditoría de equidad

**Sistema:** Territorial Review DSS (sintético)
**Fecha:** 2026-10-30
**Decisión:** REVIEW. Se recomienda la regresión logística solo para un piloto con revisión humana.

## 1. Dataset

| Comprobación | Resultado | Lectura |
|---|---|---|
| Distribución de `target` | 55.2 % positivos, 44.8 % negativos | El desbalance es leve. Aun así, accuracy no basta: un modelo que marque todo como positivo tendría 57.5 % de accuracy en el test con recall 1.0 y FPR 1.0. |
| Tamaño por grupo | G1 = 396 y G2 = 244 en total; en el test, G1 = 101 y G2 = 59 | G2 tiene menos soporte, por lo que sus métricas son menos estables. |
| Corte temporal | Entrenamiento hasta 2026-09-24; prueba desde 2026-09-25 (75/25) | Evalúa con casos futuros, igual que en el uso real, y evita que información del futuro entre al entrenamiento. |
| Variables excluidas | `case_id`, `received_date`, `protected_group`, `target` | Quitar `protected_group` no elimina el sesgo: `zone`, `age_band` o `previous_incidents` pueden funcionar como variables proxy. Por eso el atributo se conserva para auditar. |

## 2. Métricas globales (test, n = 160)

| Modelo | Accuracy | Recall | Precisión | FPR | Tasa de selección |
|---|---|---|---|---|---|
| Baseline: todo positivo | 0.575 | 1.000 | 0.575 | 1.000 | 1.000 |
| Regresión logística | **0.719** | **0.717** | **0.776** | **0.279** | 0.531 |
| Árbol (max_depth = 5) | 0.706 | 0.717 | 0.759 | 0.309 | 0.544 |

El baseline detecta todos los positivos, pero marca a todos los casos, así que no sirve para priorizar. Ambos modelos superan el recall mínimo de 0.68.

## 3. Métricas por grupo (`protected_group`)

| Modelo | Grupo | n | Prevalencia | Recall | FPR | Tasa de selección | Precisión |
|---|---|---|---|---|---|---|---|
| Logística | G1 | 101 | 0.49 | **0.653** | 0.250 | 0.446 | 0.711 |
| Logística | G2 | 59 | 0.73 | 0.791 | 0.375 | 0.678 | 0.850 |
| Árbol | G1 | 101 | 0.49 | **0.633** | 0.269 | 0.446 | 0.689 |
| Árbol | G2 | 59 | 0.73 | 0.814 | 0.438 | 0.712 | 0.833 |

| Brecha | Logística | Árbol | Tolerancia |
|---|---|---|---|
| Recall | **0.138** ✅ | 0.181 ❌ | <= 0.16 |
| FPR | **0.125** ✅ | 0.168 ❌ | <= 0.16 |
| Tasa de selección | 0.232 | 0.266 | Solo informativa |

**Lectura:** el recall global (0.717) aceptable oculta una falla localizada. En G1 el recall es de 0.653, por debajo de 0.68, así que el modelo pierde más casos reales en ese grupo. La brecha en la tasa de selección se explica en buena parte por la diferencia de prevalencia (0.49 frente a 0.73), por lo que no se usa como criterio principal.

## 4. Análisis interseccional (`protected_group` × `age_band`)

**Soporte mínimo:** 20 observaciones. Es un criterio propio de este informe, porque el proyecto no fija uno. Los grupos con menos casos se muestran para no ocultarlos, pero no se interpretan.

| Grupo | n | Recall (log.) | FPR (log.) | Recall (árbol) | FPR (árbol) | ¿Se interpreta? |
|---|---|---|---|---|---|---|
| G1 · 18-29 | 18 | 0.750 | 0.143 | 0.750 | 0.214 | ⚠️ No (n < 20) |
| G1 · 30-44 | 24 | 0.562 | 0.125 | 0.625 | 0.375 | Sí |
| G1 · 45-59 | 35 | **0.588** | 0.389 | 0.647 | 0.278 | Sí |
| G1 · 60+ | 24 | 0.833 | 0.250 | 0.583 | 0.250 | Sí |
| G2 · 18-29 | 11 | 0.875 | 0.000 | 1.000 | 0.000 | ⚠️ No (n < 20) |
| G2 · 30-44 | 14 | 0.667 | 0.500 | 0.833 | 1.000 | ⚠️ No (n < 20) |
| G2 · 45-59 | 8 | 1.000 | 0.000 | 0.667 | 0.000 | ⚠️ No (n < 20) |
| G2 · 60+ | 26 | 0.765 | **0.556** | 0.765 | 0.556 | Sí |

**Hallazgos con soporte suficiente:**
- **G1 · 30-44 y G1 · 45-59** tienen el recall más bajo con la logística (0.56–0.59). Ahí se concentra el daño priorizado: casos reales que no se detectan.
- **G2 · 60+** tiene una FPR de 0.556 en ambos modelos: más de la mitad de los casos negativos recibe una alerta falsa. Esto genera carga de revisión y podría llevar a un trato desigual hacia personas mayores.
- Con n de 24 a 35, una sola observación mueve el recall entre 4 y 8 puntos. Estas cifras indican dónde investigar; no son estimaciones firmes.

## 5. Costo computacional (Green AI)

| Modelo | Entrenamiento | Tamaño serializado | Límite de tamaño |
|---|---|---|---|
| Logística | 1.32 s* | 3.6 KB | 1024 KB |
| Árbol | 0.16 s | 7.9 KB | 1024 KB |

\*La primera ejecución incluye la inicialización del entorno. Ambos tiempos son despreciables.

**Justificación Green AI:** el árbol es más complejo y ocupa el doble, pero no mejora la utilidad (mismo recall, menor accuracy) y empeora las brechas. El costo adicional no está justificado, así que se prefiere la opción suficiente: la regresión logística.

## 6. Comparación y recomendación

| Criterio | Logística | Árbol |
|---|---|---|
| Utilidad (recall y accuracy) | 0.717 / 0.719 | 0.717 / 0.706 |
| Cumple las brechas (<= 0.16) | Sí | No |
| Tamaño | 3.6 KB | 7.9 KB |
| Interpretabilidad | Coeficientes explicables | Reglas explicables pero menos estables |

**Recomendación: REVIEW.** La regresión logística puede usarse en un piloto con revisión humana obligatoria, sin automatizar decisiones. Para pasar a GO se requiere:
1. Investigar el bajo recall de G1, sobre todo de G1 · 45-59: revisar los datos, las variables proxy y el umbral de decisión.
2. Revisar el exceso de alertas falsas en G2 · 60+.
3. Conseguir más datos o calcular intervalos de confianza (bootstrap) antes de comparar los grupos pequeños.
4. Mantener como respaldo la alternativa no predictiva (FIFO con reglas explícitas) definida en LAB11.

**Acción humana:** el analista revisa todos los casos que el modelo pone en la parte alta de la cola. El supervisor revisa cada mes el recall de G1 y la FPR de G2 · 60+. Si se supera la tolerancia, se aplica la condición de retiro de LAB11.

## 7. Por qué una brecha no prueba discriminación causal

Una brecha observada es una **señal que requiere investigación**, no una prueba de discriminación:
- **Prevalencias distintas:** G1 tiene 49 % de positivos y G2 73 %. Parte de la diferencia en la tasa de selección y la FPR viene de esa distribución, no necesariamente de un trato injusto del modelo.
- **Tamaño de muestra:** con 59 casos en G2 y grupos interseccionales de 8 a 35, las brechas tienen mucha variación aleatoria y no se calcularon intervalos.
- **Variables proxy:** el modelo no usa `protected_group`, pero puede reproducir diferencias a través de `zone` o `age_band`. Confirmarlo exige analizar los datos y el proceso que los generó.
- **Causalidad:** Fairlearn mide asociaciones entre grupos y errores. Para afirmar una causa se necesitaría conocer cómo se generó la etiqueta y qué ocurriría con otro umbral u otros datos.

Por eso la decisión es investigar y revisar (REVIEW), no declarar que el modelo es justo o injusto.

## Fuentes
- Fairlearn Contributors. *Performing a Fairness Assessment*, documentación oficial.
- NIST AI RMF 1.0, funciones MEASURE y MANAGE. DOI: 10.6028/NIST.AI.100-1.
