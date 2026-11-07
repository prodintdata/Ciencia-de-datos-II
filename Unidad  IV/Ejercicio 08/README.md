# U04.E08 · Expediente de gobernanza y simulacro

INF-8239 Ciencia de Datos II · Unidad 04 · Jhonatan Cabral (BE2322)

Expediente individual que integra LAB13 (gobernanza y DSS responsable con Streamlit) sobre el caso sintético **Territorial Review DSS**, a partir de LAB11, LAB12 y E07. El sistema ordena casos para que una persona los revise; no autoriza decisiones automáticas sobre personas.

- **Informe de síntesis:** `U04_E08_Jhonatan_Cabral.pdf`
- **Anexo de evidencias:** `U04_E08_Evidencias_Jhonatan_Cabral.pdf`

## Decisión final
**REVIEW.** Las puertas de LAB13 dan GO en el agregado, pero el monitoreo mensual deja ambas versiones en REVIEW. El modelo base tiene recall bajo en octubre (0.643) y una brecha de recall de 0.175 en noviembre. El modelo mitigado de E07 tiene recall de 0.679 en octubre y una brecha de FPR de 0.186 en noviembre (IC 95 %: 0.015–0.533, con solo 6 negativos en G2). Se mantiene la tolerancia de 0.16 sin cambios, el modelo mitigado no se descarta todavía y corre solo en sombra, mientras la cola opera con FIFO y revisión humana de todos los casos. La justificación está en la sección 6 del informe y en `reports/e08/fpr_gap_review.json`.

## Artefactos
| Ruta | Contenido |
|---|---|
| `student_inputs/data_inventory.csv` | Inventario de campos: categoría, uso en modelo y auditoría, finalidad, minimización, retención y acceso |
| `student_inputs/retention_policy.csv` | Retención y eliminación por artefacto, con responsable y Accountable |
| `student_inputs/raci.csv` | Matriz RACI con un único Accountable por actividad |
| `student_inputs/handoffs.csv` | Traspasos entre roles: entregable, criterio de aceptación, evidencia y firma del Accountable |
| `configs/governance.yml` | Usos prohibidos, identificadores directos y umbrales de las puertas |
| `configs/monitoring.yml` | Plan de monitoreo: señales, frecuencia, responsables, umbrales y acción |
| `docs/DATASET_CARD.md` | Datasheet (Gebru et al.) |
| `docs/MODEL_CARD.md` | Model Card con trazabilidad, monitoreo y simulacro |
| `docs/RUNBOOK.md` | Runbook de incidentes |
| `docs/AI_USE_DECLARATION.md` | Declaración de uso de IA |
| `src/inf8239_u04/monitoring.py` | PSI, reporte mensual por grupo y alertas |
| `scripts/e08_monitoring.py` | Genera `reports/e08/monitoring_*.csv`, `drift_psi.csv` y `monitoring_summary.json` |
| `scripts/e08_incident_drill.py` | Simulacro reproducible; evidencia y manifiesto SHA-256 en `reports/e08/incident_drill/` |
| `reports/e08/POSTMORTEM.md` | Postmortem del simulacro con acciones, responsables y fechas |
| `reports/e08/run_log.txt` | Salida de consola de todos los comandos |
| `reports/lab13/` | Decisión por puertas con recomendación trazable, métricas por grupo y postmortem de LAB13 |
| `reports/lab11/`, `reports/lab12/`, `reports/e07/` | Evidencia previa: riesgos, auditoría y mitigación |
| `app.py` | Tablero Streamlit: propósito, límites, métricas, grupos, puertas, recomendación y acción humana |
| `tests/` | 32 pruebas: datos, privacidad, equidad, modelo, gobernanza, app, mitigación e inventario, retención, traspasos, monitoreo y simulacro (`test_e08.py`) |
| `scripts/build_e08_pdf.py` | Genera los dos PDF a partir de los archivos anteriores |
| `requirements.txt` | Dependencias exportadas con `uv export` para Streamlit Community Cloud |

## Reproducir
```bash
uv sync --frozen
uv run pytest -q
uv run python scripts/lab13_governance.py
uv run python scripts/e08_monitoring.py
uv run python scripts/e08_incident_drill.py
uv run streamlit run app.py
uv run --with reportlab --with pillow python scripts/build_e08_pdf.py
```

**Antes de reproducir:**
- No ejecute `scripts/lab11_impact.py` sin respaldo: reescribe `reports/lab11/DECISION_RECORD.md` con la plantilla. Si ocurre, recupérelo con `git checkout -- reports/lab11/DECISION_RECORD.md`.
- Los resultados son deterministas (semilla 42 y corte temporal fijo). Solo cambian los tiempos, las marcas de fecha y el commit dentro de la versión del modelo.

Los datos son sintéticos y didácticos. No representan personas, territorios ni estadísticas reales de la República Dominicana.
