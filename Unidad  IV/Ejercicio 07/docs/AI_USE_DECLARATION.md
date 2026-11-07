# Declaración de uso de IA

## Herramienta
Claude Code (Claude Opus 5.5, de Anthropic) en Visual Studio Code, octubre de 2026.

## Mi trabajo
- Instalé el entorno y ejecuté LAB11 en mi equipo (anexo de evidencias, E1–E3). Después ejecuté LAB12 con los comandos del README.
- Completé y ajusté la ficha de impacto, los interesados, el registro de riesgos y la decisión de LAB12.
- Ejecuté las pruebas y las validaciones, revisé las métricas por grupo y definí los criterios del análisis.
- Integré el proyecto en el repositorio del curso e hice los commits y el push.

## Prompts relevantes
- Explicar qué pide cada campo de LAB11 y por qué.
- Revisar mis insumos y la redacción del registro de riesgos.
- Diagnosticar el error de `lab11_impact.py` y el fallo del push.
- Proponer un análisis de mitigación con Fairlearn y sus pruebas.
- Revisar el informe contra el mandato y la rúbrica.
- Incorporar las correcciones del docente: subgrupo con menor recall, soporte por clase y validación de la alternativa elegida.

## Apoyo recibido
- Explicaciones de los requisitos.
- Propuestas de redacción, que revisé y ajusté.
- Diagnóstico de errores.
- El código del módulo de mitigación (`src/inf8239_u04/mitigation.py`, `scripts/e07_mitigation.py`, `tests/test_mitigation.py`), de la tabla de soporte por clase (`src/inf8239_u04/fairness.py`) y de la validación temporal (`scripts/e07_review.py`).
- El formato del PDF.

## Verificaciones
- Comparé las cifras del informe con los CSV y JSON generados y con la salida de consola (`reports/e07/run_log.txt`).
- Repetí el análisis de mitigación y obtuve resultados idénticos.
- Confirmé que las 14 pruebas pasan.

## Correcciones
1. El script base `lab11_impact.py` tenía un error de sintaxis: una cadena con saltos de línea reales. Se corrigió con `\n`.
2. Matizamos la lectura «la logística cumple las brechas» con intervalos de confianza bootstrap.
3. Medimos la alternativa sin modelo en lugar de solo enunciarla.
4. Tras la retroalimentación del docente: se corrigió el subgrupo con menor recall (G1 · 30-44, no G1 · 45-59), el soporte se juzga con los positivos (recall) y los negativos (FPR) de cada subgrupo, la comparación de mitigaciones se presenta como exploratoria y la alternativa elegida se validó con periodos temporales anteriores al test. Esa validación no confirma la mejora, así que ya no se afirma que sustituir el modelo mejore el sistema.

## Responsabilidad
Los valores del análisis son míos: el daño priorizado, las tolerancias, el soporte mínimo de 20 casos por clase y la decisión de modificar y limitar. Puedo explicar cada parte y asumo la responsabilidad de lo entregado.
