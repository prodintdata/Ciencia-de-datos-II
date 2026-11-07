# Datasheet — `territorial_risk_synthetic.csv`

Sigue la estructura de *Datasheets for Datasets* (Gebru et al., 2021). Cada cifra se puede reproducir con `uv run python scripts/describe_dataset.py` o con el inventario `student_inputs/data_inventory.csv`.

## Motivación
- **Para qué se creó:** practicar contratos de datos, evaluación temporal, auditoría por subgrupo y gobernanza en INF-8239, Unidad 04.
- **Quién lo creó:** el proyecto base del curso (INF8239_U04_Gobernanza_DSS_Proyecto_Base_uv), con una semilla educativa fija.
- **Qué no es:** no contiene personas, lugares, tasas ni estadísticas oficiales de la República Dominicana.

## Composición
| Aspecto | Valor |
|---|---|
| Instancias | 640 casos territoriales sintéticos; `case_id` único |
| Columnas | 9 (detalle en `student_inputs/data_inventory.csv`) |
| Periodo | `received_date` del 2026-01-01 al 2026-12-27 |
| Zonas | Sur 164, Este 164, Oeste 157, Norte 155 |
| Grupo protegido | G1 396, G2 244 |
| Tramo de edad | 60+ 179, 30-44 163, 45-59 150, 18-29 148 |
| Etiqueta `target` | 55.2 % positivos (prevalencia en la prueba: G1 0.49, G2 0.73) |
| Faltantes | 0 |
| Identificadores directos | Ninguno; `name`, `document_number`, `email` y `phone` están prohibidos y el contrato los rechaza |

- **Datos sensibles:** `protected_group` (solo para auditar, fuera del modelo) y `age_band` (edad ya generalizada en tramos).
- **Posibles proxies:** `zone` y `age_band` pueden reproducir diferencias entre grupos.

## Proceso de recolección
Generación sintética con semilla 42. No hubo consentimiento porque no hay personas reales. Con datos reales se necesitaría una base legal (consentimiento, Ley 172-13, art. 5.4, salvo las excepciones del art. 27) y un aviso a las personas sobre finalidad, destinatarios, responsable y derechos (art. 5.3). Si `protected_group` revelara origen racial o étnico, sería un dato especialmente protegido (art. 6.8 y art. 75).

## Preprocesamiento
- Se ordena por `received_date`.
- Corte temporal 75/25: entrenamiento hasta el 2026-09-24 (480 casos) y prueba desde el 2026-09-25 (160 casos).
- Al modelo entran `zone`, `age_band`, `previous_incidents`, `infrastructure_score` y `exposure`, con one-hot y escalado.
- Excluidas: `case_id`, `received_date`, `protected_group` y `target`.

## Usos
- **Previsto:** priorizar casos sintéticos para revisión humana y practicar la auditoría.
- **Prohibido:** perfilar personas reales, inferir sobre poblaciones reales, decidir elegibilidad, intervenir automáticamente o declarar emergencias (`configs/governance.yml`).
- **Riesgo conocido:** con 160 casos de prueba, las brechas por grupo tienen intervalos amplios (bootstrap en `reports/e07/bootstrap_gaps.json`).

## Distribución
En el repositorio del curso, solo con fines educativos. No se publica ningún dato personal.

## Mantenimiento y retención
- **Responsable:** Ingeniero de datos (R) y Líder del equipo de datos (A), según "Calidad y privacidad de datos" en `student_inputs/raci.csv`.
- **Retención:** mientras dure el piloto y 12 meses tras el retiro; luego borrado seguro y conservación solo de métricas agregadas (`student_inputs/retention_policy.csv`).
- **Monitoreo:** deriva por PSI frente al entrenamiento y regla de calidad por zona (`configs/monitoring.yml`, `reports/e08/`).
