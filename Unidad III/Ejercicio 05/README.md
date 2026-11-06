# INF-8239 · Unidad 03 · Motor recomendador reproducible (U03.E05)

Estudiante: Jhonatan Cabral (BE2322). Proyecto base y laboratorios: Edwin Ramón José Nolasco.

Consolida LAB08 (popularidad y contenido) y LAB09 (factorización, ranking offline e híbrido) sobre MovieLens Latest Small.

## Datos y licencia
MovieLens **no se redistribuye**: `data/raw/*` está en `.gitignore` y se descarga desde GroupLens con el script (unos 1 MB). Uso académico bajo las condiciones del README oficial; cite a Harper y Konstan (2015), https://doi.org/10.1145/2827872. Detalle en [docs/DATASET_CARD.md](docs/DATASET_CARD.md).

## Reproducir
```bash
uv python install 3.12
uv sync
uv run pytest -q                                   # 16 pruebas, no necesitan MovieLens
uv run python scripts/download_data.py             # imprime el SHA-256 del ZIP
uv run python scripts/audit_data.py                # reports/audit.json
uv run python scripts/lab08_content.py             # popularidad y tres consultas por contenido
uv run python scripts/lab09_hybrid.py --factors 20 --epochs 12 --alpha 0.75 --seed 42
uv run python scripts/e05_experiments.py           # 3 factores x 3 semillas x 5 alphas + baselines + Pareto
uv run python scripts/e05_profiles.py --factors 40 --alpha 0.5
uv run jupyter nbconvert --to notebook --execute --inplace notebooks/01_recomendador_movielens.ipynb
uv run streamlit run app/streamlit_app.py
```
Sin uv: `pip install -r requirements.txt` y `pip install -e .` (Python 3.12).

## Estructura
| Ruta | Contenido |
|---|---|
| `src/inf8239_u03/` | Datos y validación, recomendadores (popularidad, contenido, factorización, perfil de géneros, híbrido, fallback) y métricas (HitRate, Precision, cobertura, diversidad, Pareto) |
| `scripts/` | Descarga, auditoría, LAB08, LAB09 y experimentos del Ejercicio 05 |
| `notebooks/` | Notebook ejecutado que recalcula y verifica las cifras |
| `reports/` | Métricas, tablas, perfiles y figuras (versionados como evidencia) |
| `tests/` | Contratos de datos, contenido, factorización, híbrido y métricas |
| `docs/` | Dataset Card y System Card |
| `app/` | Aplicación Streamlit por contenido |

## Resultados principales (promedio de semillas 42, 123 y 2026)
| Método | RMSE | HitRate@10 | Cobertura |
|---|---|---|---|
| Media global | 1.116 | – | – |
| Popularidad | – | 0.043 | 1.2 % |
| Contenido puro | – | 0.002 | 7.8 % |
| Híbrido 40 factores, alpha 0.5 (elegido) | 1.018 | 0.039 | 10.8 % |

## Interpretación
Una recomendación no es una verdad: depende de los datos observados, los candidatos y el objetivo. El HitRate mide si la última película vista entra en el Top-10; las diferencias entre configuraciones son de pocos usuarios y deben leerse junto con la variación entre semillas.
