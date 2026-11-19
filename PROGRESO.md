# PROGRESO

Bitácora del proyecto. Al iniciar una sesión, se lee este archivo y se continúa desde el último paso completado.

| Fecha y hora (UTC−5) | Rama | Qué se hizo | Commit | Decisiones / pendientes |
|---|---|---|---|---|
| 2026-11-19 11:39 | feat/setup | Estructura, dependencias fijadas, configuración, `.gitignore` | c46d974 | Motor DuckDB (ADR 0001); datos desde el zip oficial (ADR 0002) |
| 2026-11-19 11:40 | feat/setup | Plan con preguntas, KPIs y arquitectura; ADR 0001–0003 | ver log | — |
| 2026-11-19 11:42 | feat/database | DDL Medallion en DuckDB + scripts T-SQL (MERGE, CREATE OR ALTER) + ER | e84a7a3 | T-SQL no ejecutado en este entorno (ADR 0001) |
| 2026-11-19 11:47 | feat/ingesta | Descarga, bronze, silver, gold, calidad; pipeline corrido dos veces sin duplicar filas | 0de3d12 | 8/8 pruebas de calidad en verde; DuckDB exige vaciar tablas hijas en una transacción previa |
| 2026-11-19 11:51 | feat/eda | `src/analysis.py` y `notebooks/01_eda.ipynb` ejecutado con 10 secciones y conclusiones | ver log | Efectos medidos contra días comparables (año–mes–día de semana); promociones comparadas dentro de tienda–familia–mes |
| 2026-11-19 12:03 | feat/modelo | Features sin fuga, LightGBM global, backtest 3 cortes, pronóstico 16 días, inventario, notebook 02, model card, snapshot | ver log | RMSLE 0.404 vs 0.552 del naive; early stopping con holdout interno; TRAIN_START=2015-01-01 por la etapa de aperturas, no por memoria |
| 2026-11-19 12:16 | fix/registro-incompleto | Detección de meses con registro incompleto antes de jul-2015; EDA con familias estables; modelo reentrenado desde jul-2015 | 5c3524c | ADR 0004; RMSLE 0.405, WAPE 12.8%, sesgo −1.7% |
| 2026-11-19 12:20 | feat/app | App Streamlit ES/EN de 5 páginas, 11 pruebas con AppTest, guía de despliegue y capturas | 8844d5a | La app lee solo el snapshot; `app/requirements.txt` liviano |
| 2026-11-19 12:23 | docs/cierre | Hallazgos, README, LinkedIn, portfolio.json, guía de estudio; corrección de cifras de quincena en el EDA | ver log | — |
| 2026-11-19 12:31 | docs/app-url | URL pública de la app en README, portfolio.json y LinkedIn | ver log | — |

## Pendientes de Carlos
- ~~Publicar la app en Streamlit~~ ✅ publicada el 2026-11-19: https://favorita-demand-forecast-k3bm7c69sld3b67ygiwxnu.streamlit.app/
- Opcional: subir `submission.csv` (generado por `python -m src.model`) a Kaggle y anotar el puntaje aquí.
- Opcional: ejecutar `sql/00`–`03` en su SQL Server local para validar la versión T-SQL.
