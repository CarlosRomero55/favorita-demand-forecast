# Model card · `lightgbm_global` v1

## Uso previsto
Pronóstico diario de unidades vendidas por tienda y familia de producto para los próximos 16 días, como insumo para planificar la reposición. Es un proyecto de portafolio con datos públicos; no es un sistema en producción de Corporación Favorita.

## Datos
- Fuente: competencia de Kaggle *Store Sales – Time Series Forecasting* (Corporación Favorita, Ecuador).
- Entrenamiento: 2015-07-01 a 2017-08-15, 1,782 series tienda–familia (54 tiendas × 33 familias), 1,381,050 filas en el modelo final. Antes de julio de 2015 hay meses con registro incompleto (PRODUCE casi en cero, BEVERAGES a la mitad; ver ADR 0004). También se excluyen los 25 de diciembre (tiendas cerradas).
- Pronóstico: 2017-08-16 a 2017-08-31 (28,512 filas de `test.csv`).

## Modelo
- LightGBM de regresión sobre `log1p(sales)` (RMSE en log = RMSLE), con un único modelo global para todas las series.
- 37 variables:
  - Lags de 16, 21, 28, 35 y 42 días.
  - Promedios móviles de 7 a 112 días que terminan 16 días antes.
  - Promociones del día y su desvío frente a lo habitual.
  - Calendario y quincena.
  - Feriados nacionales y locales por tienda.
  - Metadata de la tienda.
  - Petróleo con desfase de 16 días.
- Regla anti-fuga: ninguna variable usa ventas posteriores al día T−16, así que un modelo sirve para todo el horizonte.
- Series sin ventas en los 28 días previos al corte → pronóstico 0.
- Hiperparámetros: `learning_rate=0.05`, `num_leaves=255`, `min_data_in_leaf=100`, `feature_fraction=0.8`, `bagging_fraction=0.8`. El modelo final usa 273 iteraciones (promedio de las mejores iteraciones de los cortes × 1.05).

## Evaluación (backtest, 3 cortes de 16 días: 29-jun a 15-ago-2017)
El *early stopping* de cada corte usa los 16 días previos al corte, nunca la ventana evaluada.

| Modelo | RMSLE | WAPE | Sesgo |
|---|---:|---:|---:|
| **LightGBM global** | **0.405** | **12.8%** | −1.7% |
| Naive estacional (mismo día de la semana, última semana) | 0.552 | 17.0% | −3.1% |
| Promedio móvil 14 días | 0.485 | 22.6% | −0.6% |

- Mejora frente al naive estacional: −27% de RMSLE y −25% de WAPE. Gana en los 3 cortes y en 32 de 33 familias (la excepción es BOOKS).
- En las 5 familias más grandes, el WAPE va de 8.7% (PRODUCE) a 19.0% (CLEANING).
- A nivel cadena, el error absoluto del total diario es 4.5%.

## Importancia de variables
89% del *gain* en promedios móviles: el nivel reciente de la serie domina. SHAP confirma la dirección esperada de los ajustes: más promociones que lo habitual (+43% aprox.), domingo (+10%) y días 1–3 tras el pago (+2%). Feriados y petróleo aportan muy poco.

## Limitaciones y riesgos
- Validación solo en verano de 2017, sin diciembre ni feriados nacionales grandes; el error en temporada alta probablemente sea mayor.
- Sesgo negativo leve (−1.7%): si se usa sin colchón, tiende al quiebre de stock.
- El efecto de las promociones es una asociación aprendida, no causal. Además, el modelo necesita conocer las promociones de antemano.
- Los shocks únicos (terremoto de 2016) no se pueden anticipar.
- Las series intermitentes (BOOKS, BABY CARE, HOME APPLIANCES) se pronostican mal; convendría un método específico (Croston/TSB).
- Todo está en unidades, no en dólares.
- La recomendación de inventario de la app es una heurística didáctica (z × σ × √L), no una política real.

## Reproducir
`python -m src.pipeline && python -m src.model` (unos 4 minutos en 2 núcleos). Genera `gold.fact_forecast`, `gold.fact_backtest_metrics`, `models/lightgbm_global_v1.txt` y `submission.csv`.
