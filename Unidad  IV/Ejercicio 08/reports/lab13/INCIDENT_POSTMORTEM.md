# Postmortem del simulacro de incidente — Territorial Review DSS (sintético)

> Simulacro generado con `uv run python scripts/simulate_incident.py`. No hubo personas reales afectadas. El procedimiento sigue `docs/RUNBOOK.md` y los roles de `student_inputs/raci.csv`.

## Resumen
| Campo | Valor |
|---|---|
| Detectado | 2026-10-31T22:45:43Z (UTC) |
| Señal | Brecha de recall entre grupos por encima de la tolerancia (`max_recall_gap` = 0.16) |
| Clase | Alta: activa la condición de retiro de LAB11 |
| Contención | Decisión pasa a REVIEW y la cola vuelve a la alternativa segura (FIFO con reglas explícitas) |
| Estado | Simulacro cerrado; acciones correctivas abiertas con responsable y fecha |

## Cronología (simulada)
| Momento | Hecho | Responsable |
|---|---|---|
| T0 · 22:45 UTC | El monitoreo detecta la brecha de recall fuera de tolerancia; `decision.failed` contiene `recall_gap` | Ingeniero de ML |
| T0 + 15 min | Se pasa el sistema a REVIEW y a FIFO sin esperar la decisión formal (autoridad de contención del Runbook, paso 2) | Ingeniero de ML; Científico de datos |
| T0 + 30 min | Se preserva la evidencia (ver abajo) antes de cualquier cambio | Científico de datos |
| T0 + 1 h | La Dirección confirma la suspensión, tras consultar a Asesoría legal y al Líder del equipo de datos | Dirección de Gestión de Riesgo Territorial |
| Mismo día hábil | Comunicación interna y a representantes de personas afectadas | Responsable de producto |
| T0 + 5 días hábiles | Entrega de este postmortem para aprobación | Científico de datos |

## Detección
La puerta `recall_gap` de `src/inf8239_u04/governance.py` falló y la decisión cambió automáticamente a REVIEW. La falla quedó visible en `failed`; no se ocultó. En la línea base de LAB13 la brecha era 0.138, con un intervalo bootstrap del 95 % de 0.011 a 0.314 (`reports/e07/bootstrap_gaps.json`). El simulacro representa el caso en que el valor real queda en la parte alta de ese intervalo.

## Contención
- El sistema dejó de ordenar la cola y se volvió a FIFO con reglas explícitas y públicas: `previous_incidents >= 3` o `infrastructure_score < 0.3`.
- Costo de la contención: las reglas marcan cerca del 73 % de la cola (FPR 0.559), así que se pidió capacidad de revisión adicional al Supervisor de analistas.
- Ningún caso se cerró sin revisión humana durante el incidente.

## Preservación de evidencia
Se copiaron sin sobrescribir, en una carpeta del incidente con fecha ISO 8601:
- `reports/lab13/deployment_decision.json` (incluye versión del modelo, política y evidencia) y `reports/lab13/fairness_by_group.csv`;
- el modelo serializado y el commit de git con que se entrenó;
- `configs/governance.yml` vigente;
- el registro de casos revisados y el registro de accesos.

Los archivos no contienen identificadores directos (`tests/test_privacy.py`).

## Comunicación
- **Interna (mismo día hábil):** Dirección de Gestión de Riesgo Territorial (A), Líder del equipo de datos y Asesoría legal (C); Analistas territoriales y su supervisor (I), con la instrucción de operar con FIFO.
- **Personas afectadas:** aviso a los Representantes de personas afectadas con lo ocurrido, qué casos pudieron quedar mal priorizados (posibles falsos negativos en G1) y cómo apelar ante el supervisor independiente, que responde en 10 días hábiles.
- El mensaje no atribuyó causas antes del análisis: una brecha es una señal, no una prueba de discriminación.

## Rollback
Retorno a FIFO con reglas explícitas como baseline seguro. Los casos priorizados por el modelo durante el periodo afectado se vuelven a revisar, empezando por G1. El modelo solo se reactiva con una nueva decisión GO firmada por la Dirección, después de corregir la causa y de que las puertas pasen en el valor puntual y con intervalos bootstrap aceptables.

## Causa probable
Hipótesis a verificar, en orden:
1. **Drift** en la composición o prevalencia de G1 respecto del corte de entrenamiento (R03).
2. **Variables proxy** del grupo protegido (`zone`, `age_band`), que afectan más a G1 · 30-44 y G1 · 45-59, los cruces con más falsos negativos en LAB12.
3. **Umbral único de 0.50** para grupos con prevalencias distintas (0.49 frente a 0.73).
4. **Muestra pequeña** (160 casos de prueba), que vuelve inestable la brecha.

## Casos y grupos afectados
Principalmente G1, por falsos negativos: casos reales que el modelo dejó al final de la cola. Como vigilancia secundaria, G2 · 60+ por su FPR alta (0.556 en LAB12).

## Acciones correctivas
| # | Acción | Responsable | Fecha límite |
|---|---|---|---|
| 1 | Re-revisar los casos de G1 priorizados como bajos durante el periodo afectado | Analistas territoriales (A: Supervisor de analistas) | 2026-11-13 |
| 2 | Analizar drift y prevalencia por grupo frente al corte de entrenamiento | Científico de datos (A: Líder del equipo de datos) | 2026-11-13 |
| 3 | Reentrenar con ExponentiatedGradient (paridad de recall, E07) y volver a evaluar puertas e intervalos | Científico de datos (A: Líder del equipo de datos) | 2026-11-20 |
| 4 | Añadir al monitoreo mensual alertas por recall de G1 y FPR de G2 · 60+ | Ingeniero de ML (A: Líder del equipo de datos) | 2026-11-20 |
| 5 | Actualizar el registro de riesgos (R03), `docs/MODEL_CARD.md` y `docs/RUNBOOK.md` | Científico de datos (A: Dirección de Gestión de Riesgo Territorial) | 2026-11-27 |
| 6 | Decidir la reactivación o el retiro definitivo con nueva decisión firmada | Dirección de Gestión de Riesgo Territorial | 2026-11-30 |

## Aprobación y cierre
- **Redacta:** Científico de datos.
- **Aprueba:** Dirección de Gestión de Riesgo Territorial.
- **Verificación del cierre:** revisión mensual del piloto del 2026-11-30.

## Lecciones
- La puerta funcionó como se diseñó: la falla produjo REVIEW y quedó visible.
- La brecha de la línea base ya estaba cerca del límite y su intervalo lo superaba; la Model Card lo había advertido. Conviene alertar antes de que el valor puntual cruce el umbral.
- La alternativa segura es viable, pero cuesta más capacidad de revisión; esa capacidad debe estar prevista antes del piloto.
