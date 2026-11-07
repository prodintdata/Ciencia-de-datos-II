# Postmortem del simulacro E08: fallo de ingesta en la zona Oeste

> Simulacro reproducible: `uv run python scripts/e08_incident_drill.py`. Datos sintéticos; ninguna persona real afectada. Procedimiento de `docs/RUNBOOK.md`; roles de `student_inputs/raci.csv`. Toda cifra sale de `reports/e08/incident_drill/`.

## Resumen
| Campo | Valor |
|---|---|
| Escenario | Una migración de la fuente deja `previous_incidents` en 0 para todos los casos de la zona Oeste (41 casos del lote) |
| Ejecución | 2026-11-01T01:08:39Z (`timeline.json`; manifiesto creado a las 01:08:40Z) |
| Versión | `logistic-sklearn1.9.1-054494c`; SHA-256 del modelo en `manifest.json` |
| Clase | Alta: el recall cae por debajo de 0.68 y la brecha de recall supera 0.16 (condición de retiro de LAB11) |
| Resultado | REVIEW con puertas fallidas `recall` y `recall_gap`; recuperación verificada (GO con el lote corregido) |

## Impacto medido
| Métrica | Lote correcto | Lote con fallo | Umbral |
|---|---|---|---|
| Recall global | 0.717 | **0.522** | >= 0.68 |
| Brecha de recall | 0.138 | **0.199** | <= 0.16 |
| Brecha de FPR | 0.125 | 0.058 | <= 0.16 |
| Recall G1 | 0.653 | **0.429** | vigilancia 0.68 |
| Recall G2 | 0.791 | 0.628 | — |

El fallo no tocó ningún atributo protegido y aun así perjudicó más a G1: G1 pesa más en Oeste (24 de 41 casos) y el modelo depende de `previous_incidents`. Un error técnico neutral puede producir un daño desigual.

## Cronología
Los pasos automáticos se ejecutaron en el mismo segundo. Los pasos humanos tienen el plazo del Runbook.

| Paso | Qué ocurrió | Responsable (RACI) | Plazo |
|---|---|---|---|
| Contrato | Un lote con la columna `email` se rechazó antes de predecir | Ingeniero de datos | Automático |
| Detección sin etiquetas | PSI global de `previous_incidents` = 0.194 (solo vigilancia). Proporción de ceros en Oeste: 5.2 % en la referencia frente a 100 % en el lote | Ingeniero de ML | Automático, por lote |
| Detección con etiquetas | Decisión REVIEW; `failed = [recall, recall_gap]` | Ingeniero de ML | Cuando los casos revisados tienen resultado |
| Contención | REVIEW, cola en FIFO y lote en cuarentena | Ingeniero de ML; Científico de datos | Inmediato |
| Confirmación | La Dirección confirma la suspensión, tras consultar a Asesoría legal y al Líder del equipo de datos | Dirección de Gestión de Riesgo Territorial | Mismo día hábil |
| Evidencia | Configuración, RACI, decisiones y perfil agregado del lote, con hashes SHA-256 | Científico de datos | Antes de cualquier cambio |
| Comunicación | Interna y a representantes de personas afectadas (ver abajo) | Responsable de producto | Mismo día hábil |
| Recuperación | Lote corregido en la fuente: GO de nuevo; reactivación solo con firma de la Dirección | Ingeniero de datos | Tras corregir la causa |

## Detección: qué funcionó y qué no
- **Funcionó:** el contrato de datos y las puertas con etiquetas. La falla quedó visible en `failed` y no se ocultó.
- **No bastó:** el PSI global (0.194) quedó por debajo del umbral de acción (0.25). El fallo de una zona se diluye en el total, igual que el recall global ocultaba el de G1.
- **PSI por zona: útil pero ruidoso.** Oeste da 8.22, pero Norte (0.27) y Sur (0.38) también superan 0.25 sin ningún fallo, porque cada zona tiene de 35 a 45 casos (`batch_profile.csv`).
- **La señal limpia fue la regla de calidad de datos:** la proporción de ceros por zona pasó de 0.05 a 1.00 solo en Oeste. Es la acción correctiva 1.

## Preservación de evidencia
`reports/e08/incident_drill/` guarda `governance.yml`, `monitoring.yml`, `raci.csv`, las decisiones antes, durante y después, la equidad por grupo durante el incidente, el perfil agregado del lote y `timeline.json`. `manifest.json` registra el SHA-256 de cada archivo y del modelo, más la versión con commit. Por minimización no se guardan filas de casos, solo agregados.

## Comunicación
- **Interna:** Dirección (A), Líder del equipo de datos y Asesoría legal (C); analistas y su supervisor (I), con instrucción de operar con FIFO.
- **Personas afectadas:** aviso a sus representantes. Explica que hubo un fallo de datos en una zona, que algunos casos pudieron quedar mal priorizados y cómo apelar (supervisor independiente, 10 días hábiles).
- No se atribuyen causas antes del análisis.

## Causa raíz
Cambio de esquema en la fuente sin prueba de calidad por segmento. El contrato verifica columnas y tipos, pero no la distribución de los valores.

## Acciones correctivas
| # | Acción | Responsable (A) | Fecha límite |
|---|---|---|---|
| 1 | Regla de calidad: proporción de ceros y nulos por zona frente a la referencia; rechazar el lote si se multiplica por 3 o más | Ingeniero de datos (Líder del equipo de datos) | 2026-11-13 |
| 2 | Re-revisar los casos de Oeste priorizados durante el periodo, empezando por G1 | Analistas territoriales (Supervisor de analistas) | 2026-11-13 |
| 3 | Monitoreo de PSI por zona solo con n >= 100 o agregando varios lotes, para evitar falsos positivos | Ingeniero de ML (Líder del equipo de datos) | 2026-11-20 |
| 4 | Aviso previo de migraciones en la fuente al equipo de datos | Responsable de producto (Dirección) | 2026-11-20 |
| 5 | Actualizar el registro de riesgos (R03), la Model Card y el Runbook | Científico de datos (Dirección) | 2026-11-27 |
| 6 | Decidir la reactivación con nueva firma | Dirección de Gestión de Riesgo Territorial | 2026-11-30 |

## Aprobación
Redacta el Científico de datos y aprueba la Dirección de Gestión de Riesgo Territorial. El cierre se verifica en la revisión mensual del 2026-11-30.
