# Reporte de calidad de datos

Generado automáticamente por `src/pipeline.py` el 2026-11-19 11:46.

## Pruebas

| Prueba | Resultado | Detalle |
|---|---|---|
| Unicidad fecha–tienda–familia | ✅ | 0 combinaciones duplicadas |
| Ventas ≥ 0 | ✅ | 0 filas con ventas negativas |
| Fechas continuas (salvo 25 de diciembre) | ✅ | 4 fechas ausentes: 2013-12-25, 2014-12-25, 2015-12-25, 2016-12-25 |
| Todas las tiendas con metadata | ✅ | 0 tiendas sin metadata |
| Panel completo por día (tiendas × familias) | ✅ | 0 días sin las 54×33 combinaciones |
| Petróleo sin nulos tras forward-fill | ✅ | 0 nulos |
| Filas de test con tienda válida | ✅ | 0 filas sin tienda |
| gold.fact_sales cuadra con silver | ✅ | diferencia 0 |

## Filas por tabla

| Tabla | Filas |
|---|---:|
| `bronze.train` | 3,000,888 |
| `bronze.test` | 28,512 |
| `bronze.stores` | 54 |
| `bronze.oil` | 1,218 |
| `bronze.holidays_events` | 350 |
| `bronze.transactions` | 83,488 |
| `silver.stores` | 54 |
| `silver.product_families` | 33 |
| `silver.daily_sales` | 3,000,888 |
| `silver.forecast_requests` | 28,512 |
| `silver.transactions` | 83,488 |
| `silver.oil_prices` | 1,704 |
| `silver.holidays` | 350 |
| `gold.dim_date` | 1,704 |
| `gold.dim_store` | 54 |
| `gold.dim_family` | 33 |
| `gold.fact_sales` | 3,000,888 |

## Perfil de los datos

- Periodo de ventas: 2013-01-01 a 2017-08-15 (3,000,888 filas fecha–tienda–familia).
- 31.3% de las filas tienen ventas en cero.
- 53 series tienda–familia nunca registran ventas (por ejemplo, familias que una tienda no vende).
- 7,330 combinaciones fecha–tienda con ventas totales en cero (tienda cerrada o aún no abierta).
- 118 combinaciones fecha–tienda con ventas pero sin registro en transactions.
- Petróleo: 31.0% de los días del calendario se completaron con forward-fill (fines de semana y feriados de EE. UU.).
- Feriados: 12 feriados trasladados (no cuentan como libres ese día), 277 registros que sí son días libres, 5 días de recuperación (Work Day) y 56 eventos.

## Reglas de limpieza aplicadas

- Bronze guarda los CSV tal cual, con `source_file`, `loaded_at` y `batch_id`.
- Familias normalizadas en `silver.product_families` con clave sustituta `family_id`.
- Petróleo en calendario completo con forward-fill, y back-fill para el 1-ene-2013; columna `is_imputed`.
- Feriados: `transferred = True` deja de ser feriado ese día; `Transfer`, `Bridge` y `Additional` sí son libres; `Work Day` es laborable.
- Los 25 de diciembre no existen en train (tiendas cerradas): se aceptan como hueco esperado.
