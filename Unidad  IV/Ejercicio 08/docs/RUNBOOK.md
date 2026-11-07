# Incident Runbook — Territorial Review DSS (sintético)

Los roles provienen de `student_inputs/raci.csv` y los umbrales de `configs/governance.yml`. La condición de retiro es la de LAB11 (`reports/lab11/DECISION_RECORD.md`).

1. **Detection and classification:** un incidente se abre por cualquiera de estas señales:

   | Señal | Fuente | Clase |
   |---|---|---|
   | Recall global < 0.68 | Monitoreo mensual; `decision.failed` contiene `recall` | Alta: condición de retiro |
   | Brecha de recall o FPR > 0.16, o brecha no medible (NaN) | `decision.failed` contiene `recall_gap` o `fpr_gap` | Alta: condición de retiro |
   | Uso fuera de alcance (elegibilidad, intervención automática, perfilado) | Auditoría del registro de accesos (R07) | Alta: condición de retiro |
   | Daño confirmado atribuible a la recomendación | Apelación o denuncia | Alta: condición de retiro |
   | Casos cerrados sin revisión registrada | Registro de casos revisados (R02) | Media |
   | Recall de G1 < 0.68 o FPR de G2 · 60+ > 0.5 con brechas aún dentro de la tolerancia | Revisión mensual del supervisor (LAB12) | Media: vigilancia reforzada |
   | Latencia > 500 ms o caída del servicio | Prueba de latencia (R05) | Baja: operar con FIFO |
   | Lote con columnas faltantes o identificadores directos | Contrato de datos (`validate_schema`) | Alta: rechazar el lote antes de predecir |
   | PSI >= 0.25 frente al entrenamiento, o proporción de ceros o nulos por zona 3 veces mayor que la referencia | `configs/monitoring.yml`; `scripts/e08_monitoring.py` | Alta: cuarentena del lote (simulacro E08) |

   El plan completo de señales, frecuencia y responsables está en `configs/monitoring.yml`.

   Cualquier puerta fallida deja la decisión en REVIEW y aparece en `failed`. Nunca se oculta (`tests/test_governance.py`).

2. **Containment authority:** quien suspende es la Dirección de Gestión de Riesgo Territorial (A de "Suspensión o retiro del sistema"). La ejecuta el Responsable de producto (R). En un incidente de clase alta, el Ingeniero de ML y el Científico de datos (R de "Respuesta a incidentes") pueden pasar el sistema de inmediato a REVIEW y a la alternativa segura del paso 5, sin esperar la decisión formal. La Dirección confirma la suspensión o la revierte. Se consulta a Asesoría legal y al Líder del equipo de datos.

3. **Evidence preservation:** antes de cualquier cambio se guardan, sin sobrescribir:
   - `reports/lab13/deployment_decision.json` y `fairness_by_group.csv` del periodo afectado;
   - el modelo serializado y el commit de git con que se entrenó;
   - `configs/governance.yml` vigente en ese momento;
   - el registro de casos revisados y el registro de accesos.

   Todo se copia a una carpeta del incidente con la fecha en formato ISO 8601 (UTC), como hace `scripts/simulate_incident.py`. Los datos no deben incluir identificadores directos (`tests/test_privacy.py`).

4. **Internal and affected-party communication:**
   - **Interno:** se informa el mismo día hábil a la Dirección (A), al Líder del equipo de datos y a Asesoría legal (C). También a los analistas territoriales y su supervisor (I), con instrucciones de operar con FIFO.
   - **Personas afectadas:** se informa a los Representantes de personas afectadas (I). El aviso explica qué ocurrió, qué casos pudieron quedar mal priorizados (por ejemplo, falsos negativos en G1) y cómo usar la vía de apelación. El supervisor independiente responde en 10 días hábiles.
   - El mensaje no atribuye causas antes del análisis: una brecha es una señal, no una prueba de discriminación.

5. **Rollback or safe baseline:** se vuelve a la revisión por orden de llegada (FIFO) con reglas explícitas y públicas: `previous_incidents >= 3` o `infrastructure_score < 0.3`. Esta alternativa tiene recall 0.859 y brecha de recall 0.084, pero marca el 73 % de la cola (FPR 0.559), así que exige más capacidad de revisión. Los casos priorizados por el modelo durante el periodo afectado se vuelven a revisar, empezando por G1. El modelo solo se reactiva con una nueva decisión GO firmada por la Dirección, después de corregir la causa y de que las puertas pasen en el valor puntual y con intervalos bootstrap aceptables.

6. **Postmortem, owner and due date:** el Científico de datos redacta `reports/lab13/INCIDENT_POSTMORTEM.md` en un plazo de 5 días hábiles desde la contención, y la Dirección de Gestión de Riesgo Territorial lo aprueba. Debe incluir:
   - cronología y señal de detección;
   - causa probable: drift (R03), variables proxy, umbral o uso indebido;
   - casos y grupos afectados;
   - acciones correctivas, cada una con responsable y fecha;
   - actualización del registro de riesgos y de esta model card.

   El cierre se verifica en la siguiente revisión mensual.
