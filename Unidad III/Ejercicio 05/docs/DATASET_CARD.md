# Dataset Card · MovieLens

## Fuente, fecha, versión y hash
- Fuente: GroupLens Research, University of Minnesota.
- Versión: MovieLens Latest Small (`ml-latest-small`), generada el 26/09/2018 según su README.
- URL: https://files.grouplens.org/datasets/movielens/ml-latest-small.zip (configurable en `.env.example`).
- Descarga: 15/10/2026 con `scripts/download_data.py`.
- SHA-256 del ZIP descargado: `696d65a3dfceac7c45750ad32df2c259311949efec81f0f144fdfb91ebc9e436`.
- Es un dataset de *desarrollo*: GroupLens advierte que puede cambiar y que no es adecuado para resultados de investigación compartidos. Por eso se registra el hash.

## Licencia y cita
Uso para investigación bajo las condiciones del README oficial: no implicar respaldo de la Universidad de Minnesota, citar el dataset, no usarlo con fines comerciales sin permiso y redistribuirlo solo bajo las mismas condiciones. Este repositorio **no redistribuye** los datos: `data/raw/*` está en `.gitignore` y cada persona los descarga con el script.

Harper, F. M., & Konstan, J. A. (2015). The MovieLens Datasets: History and Context. *ACM TiiS, 5*(4), 19. https://doi.org/10.1145/2827872

## Archivos y diccionario
| Archivo | Columnas | Uso en el proyecto |
|---|---|---|
| `ratings.csv` | userId, movieId, rating (0.5–5.0), timestamp (Unix) | Interacciones para popularidad, factorización y corte temporal |
| `movies.csv` | movieId, title, genres (separados por `|`) | Catálogo y señal de contenido (TF-IDF de géneros) |
| `tags.csv`, `links.csv` | Etiquetas libres y enlaces a IMDb/TMDb | No se usan |

## Procedimiento de descarga
```bash
uv run python scripts/download_data.py   # descarga, valida rutas del ZIP e imprime el SHA-256
uv run python scripts/audit_data.py      # contrato de columnas, claves foráneas, rango y reports/audit.json
```

## Población observada y exclusiones
- 100,836 valoraciones, 610 usuarios, 9,742 películas en catálogo (9,724 con al menos una valoración; 18 sin ninguna).
- Densidad 1.70 %: la ausencia de valoración no significa rechazo.
- Periodo: 29/03/1996 a 24/09/2018.
- Usuarios elegidos al azar entre quienes valoraron al menos 20 películas (mínimo 20, mediana 70.5, máximo 2,698).
- Sin demografía: solo identificadores anónimos.

## Calidad, sesgos y usos prohibidos
- Auditoría (`reports/audit.json`): 0 nulos, 0 pares usuario–película duplicados, 0 ratings huérfanos, ratings en [0.5, 5.0].
- Cola larga: 3,446 películas tienen una sola valoración y 6,074 tienen menos de 5. 34 películas no tienen géneros (`(no genres listed)`).
- Sesgo de selección: las personas valoran lo que eligieron ver; la distribución se concentra en 3.0–4.0 (media 3.50).
- Sesgo de supervivencia: solo entran usuarios con 20 o más valoraciones; no representa usuarios nuevos reales.
- Usos prohibidos: fines comerciales sin permiso de GroupLens, inferir atributos personales o afirmar resultados por grupos poblacionales (no hay demografía).
