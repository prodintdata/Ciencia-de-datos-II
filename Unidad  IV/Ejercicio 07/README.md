# U04.E07 · Evaluación de impacto y auditoría de equidad

INF-8239 Ciencia de Datos II · Unidad 04 · Jhonatan Cabral (BE2322)

Expediente individual que integra LAB11 (evaluación de impacto ético) y LAB12 (auditoría de equidad con Fairlearn) sobre el caso sintético **Territorial Review DSS**: un sistema que ordena casos para que una persona los revise. El sistema no autoriza decisiones automáticas sobre personas.

- **Informe de síntesis:** `U04_E07_Jhonatan_Cabral.pdf`
- **Anexo de evidencias:** `U04_E07_Evidencias_Jhonatan_Cabral.pdf`

## Decisión final
**Modificar y limitar.** El modelo base no se despliega tal como está. La versión mitigada (regresión logística con restricción de paridad de recall) se usa solo en un piloto limitado, con revisión humana de todos los casos, apelación y la condición de retiro definida en LAB11. La justificación está en el informe (sección 5) y en `reports/lab11/DECISION_RECORD.md`.

## Artefactos
| Ruta | Contenido |
|---|---|
| `student_inputs/lab11_impact.yml` | Finalidad, decisión asistida, usuarios, población afectada, propietario, alternativa no predictiva, usos prohibidos, condición de retiro y apelación |
| `student_inputs/stakeholders.csv` | Partes interesadas: beneficio, daño, poder y participación |
| `student_inputs/risk_register.csv` | Registro de 8 riesgos con control, responsable, evidencia y riesgo residual |
| `reports/lab11/` | Riesgos priorizados, resumen NIST AI RMF y registro de decisión |
| `student_inputs/lab12_decision.yml` | Daño prioritario, métrica, tolerancia, evidencia, limitación y recomendación |
| `reports/lab12/` | Métricas globales, por grupo e interseccionales de la logística y el árbol, e informe de auditoría (`AUDIT_REPORT.md`) |
| `src/inf8239_u04/mitigation.py` | Variación del umbral, ExponentiatedGradient (paridad de recall) e intervalos bootstrap |
| `scripts/e07_mitigation.py` | Comparación de mitigaciones y cálculo de la incertidumbre |
| `reports/e07/` | `mitigation_comparison.csv`, `bootstrap_gaps.json`, `expgrad_intersectional.csv` y `run_log.txt` (salida real de consola) |
| `tests/` | 12 pruebas: datos, privacidad, impacto, equidad, modelo, gobernanza, app y mitigación |
| `docs/AI_USE_DECLARATION.md` | Declaración de uso de IA |

`docs/MODEL_CARD.md`, `docs/RUNBOOK.md` y `scripts/lab13_governance.py` pertenecen a LAB13 y todavía no forman parte de este expediente.

## Reproducir
```bash
uv sync --frozen
uv run pytest -q
uv run python scripts/check_environment.py
uv run python scripts/describe_dataset.py
uv run python scripts/lab12_audit.py --model logistic
uv run python scripts/lab12_audit.py --model tree
uv run python scripts/validate_lab12_decision.py
uv run python scripts/e07_mitigation.py
```

**Antes de reproducir:**
- No ejecute `scripts/lab11_impact.py` sin respaldo: reescribe `reports/lab11/DECISION_RECORD.md` con la plantilla. Si ocurre, recupere el archivo con `git checkout -- reports/lab11/DECISION_RECORD.md`.
- Los resultados son deterministas: todo usa la semilla 42 y un corte temporal fijo. Solo varían los tiempos de entrenamiento.

Los datos son sintéticos y didácticos. No representan personas, territorios ni estadísticas reales de la República Dominicana.
