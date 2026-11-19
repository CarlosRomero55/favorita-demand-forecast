# ADR 0004 · Registro incompleto antes de mediados de 2015

- **Fecha:** 2026-11-19
- **Estado:** aceptado (reemplaza la decisión inicial de entrenar desde el 1-ene-2015)

## Contexto
Al revisar la serie mensual de la app se vieron caídas de hasta 35% que se revierten al mes siguiente (por ejemplo, feb-2014 y abr–jun-2014). Al desagregar por familia apareció la causa:
- **PRODUCE** registra prácticamente 0 en toda la cadena durante la mayoría de los meses hasta mayo de 2015, y luego salta a su nivel normal.
- **BEVERAGES** cae a la mitad en meses alternos de 2014 y en ene–abr de 2015.
- Varias familias no alimentarias (LADIESWEAR, CELEBRATION, PET SUPPLIES, PLAYERS AND ELECTRONICS, HOME CARE…) no tienen ventas antes de junio de 2015.

Estos patrones no corresponden a cambios reales de demanda. Son registros incompletos o cambios en cómo se registraba.

## Decisión
- `src/analysis.py` detecta los meses–familia anómalos: venta diaria en la cadena igual a 0 o menor al 70% de la mediana centrada de 3 meses. Define como **familias estables** las 18 que no tienen ningún mes anómalo (66% de las ventas).
- **Comparaciones entre años y meses** (crecimiento, índice mensual) → solo familias estables y el mismo periodo del año (1-ene a 15-ago).
- **Comparaciones dentro del mismo mes** (día de la semana, feriados, quincena) → todas las familias, porque la composición no cambia dentro del mes.
- **Modelo** → entrenamiento desde el 1-jul-2015 (`TRAIN_START`), cuando el registro ya es estable.
- El hallazgo queda documentado en `docs/data_quality_report.md` y en el EDA.

## Consecuencias
- El crecimiento reportado es menor y más creíble (+10% en 2016 con familias estables, frente a +33% si se compara el total en el mismo periodo).
- El modelo se entrena con menos historia, pero más limpia.
- Backtest con `TRAIN_START` 2015-01-01 vs. 2015-07-01: RMSLE 0.404 vs. 0.405, WAPE 12.8% en ambos, sesgo −2.5% vs. −1.7%. La exactitud es prácticamente la misma; se elige julio de 2015 por calidad de datos, no por la métrica.
