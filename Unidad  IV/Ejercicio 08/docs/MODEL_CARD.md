# Model Card — Territorial Review DSS (sintético)

**Modelo evaluado en LAB13:** regresión logística base (`scripts/lab13_governance.py`, umbral 0.50).
**Variante candidata (no recomendada todavía):** regresión logística con ExponentiatedGradient y paridad de recall (E07). Corre solo en sombra hasta resolver la brecha de FPR de noviembre.
**Decisión de gobernanza:** REVIEW (`reports/lab11/DECISION_RECORD.md`, actualización E08). Las puertas automáticas de LAB13 dan GO en el valor puntual, pero el monitoreo mensual deja ambas versiones en REVIEW (`reports/e08/fpr_gap_review.json`). La cola opera con FIFO y revisión humana de todos los casos.

## Intended use
- **Finalidad:** priorizar casos territoriales sintéticos para revisión humana. El sistema solo recomienda un orden; no decide (`student_inputs/lab11_impact.yml`).
- **Decisión asistida:** el orden en que el analista revisa la cola. La decisión final sobre cada caso siempre es humana.
- **Usuarios:** analistas territoriales capacitados y su supervisor.
- **Población afectada:** personas y hogares de las zonas cuyos casos entran en la cola, en especial grupos protegidos y personas de 60+.
- **Condición de uso:** el modelo solo se justifica si la capacidad de revisión es limitada. Con capacidad para revisar más del 70 % de la cola, las reglas explícitas sin modelo bastan y son menos invasivas (E07).

## Out-of-scope use
Están prohibidos (`configs/governance.yml`, `prohibited_uses`):
- intervención automática;
- decidir elegibilidad;
- declarar emergencias;
- perfilar personas reales;
- usar el sistema sin revisión humana de cada caso.

Los datos son sintéticos, así que tampoco se permite inferir nada sobre poblaciones reales (`docs/DATASET_CARD.md`). El uso fuera de alcance (R07) mantiene riesgo residual alto porque depende de la política de uso y no del modelo.

## Data and split
| Aspecto | Valor |
|---|---|
| Origen | Dataset sintético con semilla educativa fija (42). No contiene personas, lugares ni estadísticas reales |
| Tamaño | 640 casos: G1 = 396 y G2 = 244 |
| Prevalencia de `target` | 55.2 % positivos. En el test: G1 0.49 y G2 0.73 |
| Corte temporal | Entrenamiento hasta 2026-09-24; prueba desde 2026-09-25 (75/25). Test n = 160 (G1 = 101, G2 = 59) |
| Variables excluidas | `case_id`, `received_date`, `protected_group`, `target` |
| Identificadores directos | Prohibidos (`name`, `document_number`, `email`, `phone`), comprobado con `tests/test_privacy.py` |

`protected_group` no entra al modelo, pero se conserva para auditar. Quitarlo no elimina el sesgo, porque `zone`, `age_band` o `previous_incidents` pueden actuar como variables proxy.

## Global and subgroup evaluation
**Puertas de LAB13** (`reports/lab13/deployment_decision.json`, umbrales de `configs/governance.yml`):

| Puerta | Valor | Umbral | Resultado |
|---|---|---|---|
| Recall global | 0.717 | >= 0.68 | ✅ |
| Brecha de recall entre grupos | 0.138 | <= 0.16 | ✅ |
| Brecha de FPR entre grupos | 0.125 | <= 0.16 | ✅ |
| Latencia por caso | < 0.1 ms (0.03 ms en la última ejecución; varía entre ejecuciones) | <= 500 ms | ✅ |
| Tamaño del modelo | 3.6 KB | <= 1024 KB | ✅ |

Accuracy global: 0.719. Precisión: 0.776. FPR: 0.279. Como referencia, un baseline que marque todo como positivo tiene accuracy 0.575 con recall 1.0 y FPR 1.0, así que no sirve para priorizar.

**Por grupo** (`reports/lab13/fairness_by_group.csv`):

| Grupo | n | Recall | FPR | Precisión | Tasa de selección |
|---|---|---|---|---|---|
| G1 | 101 | **0.653** | 0.250 | 0.711 | 0.446 |
| G2 | 59 | 0.791 | 0.375 | 0.850 | 0.678 |

El recall global aceptable oculta una falla localizada: en G1 el recall es de 0.653, por debajo de 0.68, así que el modelo pierde más casos reales en ese grupo.

**Incertidumbre** (bootstrap con 1000 remuestras, `reports/e07/bootstrap_gaps.json`): el intervalo del 95 % de la brecha de recall va de 0.011 a 0.314, y el del recall de G1 de 0.522 a 0.784. Con 160 casos no se puede afirmar que la brecha esté por debajo de 0.16.

**Interseccional** (soporte mínimo de 20 casos, `reports/lab12/logistic/fairness_intersectional.csv`):
- G1 · 30-44 (recall 0.562, n = 24) y G1 · 45-59 (recall 0.588, n = 35) concentran los falsos negativos.
- G2 · 60+ tiene una FPR de 0.556 (n = 26): más de la mitad de sus negativos recibe una alerta falsa.
- 4 de los 8 cruces tienen menos de 20 casos y no se interpretan.

**Comparación con alternativas** (`reports/e07/mitigation_comparison.csv`):

| Variante | Accuracy | Recall | FPR | Brecha de recall | Brecha de FPR | Recall G1 |
|---|---|---|---|---|---|---|
| Logística base (t = 0.50) | 0.719 | 0.717 | 0.279 | 0.138 | 0.125 | 0.653 |
| ExponentiatedGradient, paridad de recall | 0.744 | 0.728 | 0.235 | 0.030 | 0.101 | 0.714 |
| Reglas sin modelo | 0.681 | 0.859 | 0.559 | 0.084 | 0.087 | 0.898 |
| Árbol, max_depth = 5 (LAB12) | 0.706 | 0.717 | 0.309 | 0.181 ❌ | 0.168 ❌ | 0.633 |

La versión mitigada reduce la brecha de recall sin perder utilidad, pero su intervalo (0.002–0.213) sigue siendo amplio. Las reglas detectan más casos, pero marcan el 73 % de la cola. El árbol se descarta porque supera las brechas toleradas.

Una brecha observada es una señal que hay que investigar, no una prueba de discriminación causal. Parte de la diferencia viene de las prevalencias distintas (0.49 frente a 0.73) y del tamaño pequeño de las muestras.

## Green AI evidence
| Modelo | Entrenamiento | Tamaño | Fuente |
|---|---|---|---|
| Logística base | < 0.2 s (0.06 s en la última ejecución); latencia < 0.1 ms por caso | 3.6 KB | `reports/lab13/deployment_decision.json` |
| Árbol (max_depth = 5) | 0.16 s | 7.9 KB | `reports/lab12/tree/global_metrics.json` |
| ExponentiatedGradient | 1.39 s (unas 11 veces la logística, 0.12 s) | — | `reports/e07/bootstrap_gaps.json` |
| Reglas sin modelo | Sin entrenamiento | — | `reports/e07/mitigation_comparison.csv` |

El árbol ocupa el doble que la logística y no mejora la utilidad, así que su costo extra no está justificado. ExponentiatedGradient cuesta más en entrenamiento, pero en términos absolutos el costo es despreciable y compra una reducción real de la brecha. Todos los modelos están muy por debajo de los límites de latencia y tamaño.

## Limitations, human oversight and appeal
**Limitaciones:**
- Test pequeño (160 casos) e intervalos de las brechas amplios. Los cruces interseccionales tienen entre 8 y 35 casos.
- G1 · 45-59 conserva un recall bajo incluso con el modelo mitigado.
- Los datos son sintéticos: los resultados no se trasladan a poblaciones reales.
- Puede haber variables proxy del grupo protegido (`zone`, `age_band`).
- El riesgo de sesgo de automatización (R02, prioridad 9) es el más probable: el analista puede aceptar el puntaje sin revisar el caso.

**Supervisión humana:**
- El analista revisa todos los casos antes de cerrarlos, y el sistema registra esa revisión.
- El supervisor revisa cada mes el recall global, el recall de G1 y la FPR de G2 · 60+.
- Si se cumple la condición de retiro, el sistema se suspende y se vuelve a FIFO con reglas explícitas (ver `docs/RUNBOOK.md`).

**Condición de retiro:** se aplica si el recall baja de 0.68, si la brecha de recall o de FPR supera 0.16, si se detecta un uso fuera de alcance o si se confirma un daño atribuible a la recomendación.

**Apelación:** la persona afectada puede pedir revisión humana a un supervisor independiente, que responde en 10 días hábiles. El responsable (R) es el supervisor independiente de apelaciones y quien rinde cuentas (A) es la Dirección de Gestión de Riesgo Territorial (`student_inputs/raci.csv`).

## Traceability and monitoring (E08)
- **Versión y evidencia:** `reports/lab13/deployment_decision.json` registra la versión (`logistic-sklearn<versión>-<commit>`), la política, las puertas y la acción humana. Los datos están descritos en `docs/DATASET_CARD.md` y `student_inputs/data_inventory.csv`.
- **Monitoreo mensual** (`reports/e08/monitoring_by_month.csv`, plan en `configs/monitoring.yml`): el GO agregado oculta fallas por mes. En octubre el recall fue de 0.643 (< 0.68). En noviembre, el único mes con al menos 20 casos por grupo, la brecha de recall fue de 0.175 (> 0.16) y el recall de G1 de 0.625. Septiembre y diciembre no tienen soporte para interpretar las brechas.
- **Variante mitigada (EG) en noviembre:** baja la brecha de recall a 0.046, pero la brecha de FPR sube a 0.186 (> 0.16): G1 tiene 6 alertas falsas en 17 negativos (0.353) y G2 1 en 6 (0.167). El intervalo bootstrap del 95 % va de 0.015 a 0.533, así que la evidencia no confirma ni descarta la brecha. En octubre su recall es 0.679 (< 0.68). **Decisión:** se mantiene REVIEW. No se cambia la tolerancia después de ver el resultado, y EG no se descarta todavía: en todo el periodo de prueba su brecha de FPR es 0.101. Se descarta si, con 20 o más negativos por grupo, la brecha de FPR sigue por encima de 0.16 (`reports/e08/fpr_gap_review.json`, `tests/test_e08.py`).
- **Deriva:** PSI máximo frente al entrenamiento de 0.084 (`previous_incidents`), por debajo del umbral de vigilancia de 0.10 (`reports/e08/drift_psi.csv`).
- **Simulacro:** un fallo de ingesta en una zona lleva el recall a 0.522 y la brecha a 0.199. La decisión pasa a REVIEW y vuelve a GO al corregir el lote (`reports/e08/POSTMORTEM.md`).

## Owner and review date
- **Propietario (Accountable):** Dirección de Gestión de Riesgo Territorial.
- **Responsable del monitoreo:** Ingeniero de ML (R) y Líder del equipo de datos (A).
- **Fecha de esta versión:** 2026-10-31.
- **Próxima revisión:** 2026-11-30 (revisión mensual del piloto), o antes si se activa la condición de retiro.
