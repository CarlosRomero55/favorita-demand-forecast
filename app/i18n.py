"""Textos de la app en español e inglés. Uso: t("clave")."""
from __future__ import annotations

import streamlit as st

TEXTS: dict[str, dict[str, str]] = {
    # Navegación
    "app_title": {"es": "Favorita · Pronóstico de demanda", "en": "Favorita · Demand Forecast"},
    "nav_overview": {"es": "Resumen", "en": "Overview"},
    "nav_drivers": {"es": "Qué mueve las ventas", "en": "What drives sales"},
    "nav_explorer": {"es": "Explorador de pronóstico", "en": "Forecast explorer"},
    "nav_quality": {"es": "Calidad del modelo", "en": "Model quality"},
    "nav_method": {"es": "Metodología y datos", "en": "Methodology & data"},
    "language": {"es": "Idioma", "en": "Language"},
    "source_caption": {
        "es": "Datos: Kaggle · *Store Sales – Time Series Forecasting* (Corporación Favorita, Ecuador, 2013–2017). Proyecto de portafolio de Carlos Romero.",
        "en": "Data: Kaggle · *Store Sales – Time Series Forecasting* (Corporación Favorita, Ecuador, 2013–2017). Portfolio project by Carlos Romero.",
    },
    "assoc_note": {
        "es": "Los efectos son **asociaciones observadas** frente a días comparables (mismo año, mes y día de la semana), no efectos causales probados.",
        "en": "Effects are **observed associations** versus comparable days (same year, month and weekday), not proven causal effects.",
    },
    # Resumen
    "ov_title": {"es": "¿Cuánto va a vender cada tienda las próximas semanas?", "en": "How much will each store sell in the coming weeks?"},
    "ov_sub": {
        "es": "Pronóstico a 16 días para 54 tiendas y 33 familias de producto de una cadena de supermercados ecuatoriana, y qué tanto mueven las ventas los feriados, las promociones y la quincena.",
        "en": "16-day forecast for 54 stores and 33 product families of an Ecuadorian supermarket chain, and how much holidays, promotions and paydays move sales.",
    },
    "kpi_total": {"es": "Unidades vendidas 2013–2017", "en": "Units sold 2013–2017"},
    "kpi_daily": {"es": "Venta diaria promedio 2017", "en": "Average daily sales 2017"},
    "kpi_growth": {"es": "Crecimiento 2017 comparable", "en": "Comparable 2017 growth"},
    "kpi_growth_help": {
        "es": "Venta diaria promedio del 1-ene al 15-ago de 2017 vs. el mismo periodo de 2016, solo con las familias de registro estable.",
        "en": "Average daily sales Jan 1 – Aug 15, 2017 vs. the same period of 2016, stable-registration families only.",
    },
    "ov_all": {"es": "Todas las familias", "en": "All families"},
    "ov_stable": {"es": "{n} familias de registro estable", "en": "{n} stable-registration families"},
    "ov_reg_note": {
        "es": "Antes de mediados de 2015 varias familias tienen meses sin registrar (por ejemplo, PRODUCE casi en cero): las caídas de la línea gris no son caídas de demanda. Las comparaciones entre años usan las familias de registro estable ({s:.0%} de las ventas).",
        "en": "Before mid-2015 several families have unrecorded months (e.g. PRODUCE near zero): the dips in the grey line are not demand drops. Year-over-year comparisons use the stable-registration families ({s:.0%} of sales).",
    },
    "kpi_wape": {"es": "Error del pronóstico (WAPE)", "en": "Forecast error (WAPE)"},
    "kpi_wape_delta": {"es": "{d:+.1f} pp vs. naive estacional", "en": "{d:+.1f} pp vs. seasonal naive"},
    "ov_headline": {"es": "Hallazgo principal", "en": "Key finding"},
    "ov_headline_text": {
        "es": "El modelo global LightGBM reduce el error del pronóstico tienda–familia–día de **{b:.1%} a {m:.1%}** (WAPE) frente a repetir la última semana. Lo que más pesa es el nivel reciente de ventas; luego ajustan el fin de semana (domingo **{sun:+.0%}**), los días posteriores al pago (**{pay:+.0%}**) y los feriados nacionales (**{hol:+.0%}** en mediana).",
        "en": "The global LightGBM model cuts the store–family–day forecast error from **{b:.1%} to {m:.1%}** (WAPE) versus repeating last week. Recent sales level matters most; then weekends (Sunday **{sun:+.0%}**), the days after payday (**{pay:+.0%}**) and national holidays (**{hol:+.0%}** median) adjust it.",
    },
    "ov_chart": {"es": "Venta diaria total (promedio mensual, miles de unidades)", "en": "Total daily sales (monthly average, thousand units)"},
    "ov_more": {"es": "Explora el pronóstico de una tienda en **Explorador de pronóstico**.", "en": "Explore a store's forecast in **Forecast explorer**."},
    "units_k": {"es": "miles de unidades", "en": "thousand units"},
    # Drivers
    "dr_title": {"es": "Qué mueve las ventas", "en": "What drives sales"},
    "tab_hol": {"es": "Feriados", "en": "Holidays"},
    "tab_promo": {"es": "Promociones", "en": "Promotions"},
    "tab_pay": {"es": "Quincena", "en": "Payday"},
    "tab_eq": {"es": "Terremoto 2016", "en": "2016 earthquake"},
    "tab_season": {"es": "Estacionalidad", "en": "Seasonality"},
    "hol_national": {"es": "Feriado nacional", "en": "National holiday"},
    "hol_christmas": {"es": "Previo a Navidad (21–24 dic)", "en": "Pre-Christmas (Dec 21–24)"},
    "hol_event": {"es": "Evento nacional", "en": "National event"},
    "hol_local": {"es": "Feriado local (en la tienda de esa ciudad)", "en": "Local holiday (in that city's store)"},
    "hol_axis": {"es": "Efecto mediano vs. día normal (%)", "en": "Median effect vs. normal day (%)"},
    "hol_text": {
        "es": "En feriado nacional la cadena vende **{n:+.0%}** (mediana) frente a un día normal comparable; antes de Navidad, **{c:+.0%}**. El feriado local, medido en la tienda de esa ciudad o provincia, va al revés: **{l:+.1%}**, probablemente porque la gente sale de la ciudad.",
        "en": "On national holidays the chain sells **{n:+.0%}** (median) versus a comparable normal day; before Christmas, **{c:+.0%}**. Local holidays, measured at that city's store, go the other way: **{l:+.1%}**, likely because people leave town.",
    },
    "promo_naive": {"es": "Ingenuo (mezcla tiendas y meses)", "en": "Naive (mixes stores and months)"},
    "promo_strat": {"es": "Estratificado (misma tienda y mes)", "en": "Stratified (same store and month)"},
    "promo_axis": {"es": "Lift de promoción (%)", "en": "Promotion lift (%)"},
    "promo_text": {
        "es": "La comparación ingenua exagera: en GROCERY I sugiere **{gn:+.0%}**, pero dentro de la misma tienda y mes el lift es **{gs:+.0%}**. Ponderado por ventas, el lift estratificado es **{w:+.0%}**. Las promociones crecieron con el tiempo y se concentran en tiendas grandes: esa es la trampa de correlación vs. causalidad.",
        "en": "The naive comparison overstates: for GROCERY I it suggests **{gn:+.0%}**, but within the same store and month the lift is **{gs:+.0%}**. Sales-weighted, the stratified lift is **{w:+.0%}**. Promotions grew over time and concentrate in large stores: that is the correlation-vs-causation trap.",
    },
    "pay_axis": {"es": "Días desde el último pago (día 15 o fin de mes)", "en": "Days since last payday (15th or month end)"},
    "pay_y": {"es": "Venta vs. día normal (1 = normal)", "en": "Sales vs. normal day (1 = normal)"},
    "pay_text": {
        "es": "El sector público paga los días 15 y último de cada mes (nota del dataset). El día de pago no vende más, pero los días 1–3 posteriores venden **{p:+.0%}** frente al resto; antes del siguiente pago la venta cae.",
        "en": "The public sector pays on the 15th and last day of each month (dataset note). Payday itself doesn't sell more, but days 1–3 after sell **{p:+.0%}** versus the rest; sales dip before the next payday.",
    },
    "eq_zone": {"es": "Manabí y Esmeraldas", "en": "Manabí & Esmeraldas"},
    "eq_rest": {"es": "Resto del país", "en": "Rest of country"},
    "eq_y": {"es": "Venta diaria indexada (1 = antes del terremoto)", "en": "Indexed daily sales (1 = pre-earthquake)"},
    "eq_text": {
        "es": "Tras el terremoto de 7.8 del 16-abr-2016, las 4 semanas siguientes vendieron **{z:+.0%}** en las tiendas de Manabí y Esmeraldas y **{r:+.0%}** en el resto, frente a las 4 semanas previas (en la misma ventana de 2015: {z15:+.0%} y {r15:+.0%}). Coincide con las donaciones de ayuda que menciona la descripción del dataset.",
        "en": "After the 7.8 earthquake of Apr 16, 2016, the next 4 weeks sold **{z:+.0%}** in Manabí and Esmeraldas stores and **{r:+.0%}** elsewhere versus the prior 4 weeks (same window in 2015: {z15:+.0%} and {r15:+.0%}). Consistent with relief donations noted in the dataset description.",
    },
    "season_dow": {"es": "Índice por día de la semana", "en": "Weekday index"},
    "season_month": {"es": "Índice por mes (familias estables, 2013–2016)", "en": "Monthly index (stable families, 2013–2016)"},
    "season_text": {
        "es": "Domingo **{s:+.0%}** sobre el promedio del mes; diciembre **{d:+.0%}** sobre el promedio del año. El petróleo, clave para la economía ecuatoriana, muestra correlación de {ol:+.2f} en niveles pero solo {oy:+.2f} en variaciones interanuales: la relación es débil una vez que se quita la tendencia.",
        "en": "Sunday is **{s:+.0%}** above the monthly average; December **{d:+.0%}** above the yearly average. Oil, key to Ecuador's economy, shows a {ol:+.2f} correlation in levels but only {oy:+.2f} in year-over-year changes: weak once the trend is removed.",
    },
    "dows": {"es": "Lun,Mar,Mié,Jue,Vie,Sáb,Dom", "en": "Mon,Tue,Wed,Thu,Fri,Sat,Sun"},
    "months": {"es": "Ene,Feb,Mar,Abr,May,Jun,Jul,Ago,Sep,Oct,Nov,Dic", "en": "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec"},
    # Explorador
    "ex_title": {"es": "Explorador de pronóstico", "en": "Forecast explorer"},
    "ex_store": {"es": "Tienda", "en": "Store"},
    "ex_family": {"es": "Familia de producto", "en": "Product family"},
    "ex_service": {"es": "Nivel de servicio", "en": "Service level"},
    "ex_lead": {"es": "Tiempo de reposición (días)", "en": "Lead time (days)"},
    "ex_history": {"es": "Historia", "en": "History"},
    "ex_forecast": {"es": "Pronóstico LightGBM", "en": "LightGBM forecast"},
    "ex_naive": {"es": "Naive estacional", "en": "Seasonal naive"},
    "ex_band": {"es": "Banda de error (nivel de servicio)", "en": "Error band (service level)"},
    "ex_fc16": {"es": "Pronóstico 16 días", "en": "16-day forecast"},
    "ex_fcl": {"es": "Pronóstico próximos {l} días", "en": "Forecast next {l} days"},
    "ex_ss": {"es": "Stock de seguridad", "en": "Safety stock"},
    "ex_target": {"es": "Stock objetivo", "en": "Target stock"},
    "ex_sigma": {"es": "σ del error diario en backtest: {s:,.1f} unidades", "en": "Daily backtest error σ: {s:,.1f} units"},
    "ex_zero": {"es": "Esta serie no vendió en los 28 días previos: el pronóstico es 0.", "en": "This series had no sales in the prior 28 days: forecast is 0."},
    "ex_formula": {
        "es": "Stock objetivo = pronóstico de los próximos L días + z × σ × √L. **Heurística didáctica**, no es la política real de Favorita: supone errores independientes y normales e ignora stock en tránsito, vida útil y mínimos de pedido.",
        "en": "Target stock = forecast for the next L days + z × σ × √L. **Teaching heuristic**, not Favorita's actual policy: it assumes independent normal errors and ignores stock in transit, shelf life and order minimums.",
    },
    "ex_table": {"es": "Pronóstico diario", "en": "Daily forecast"},
    "col_date": {"es": "Fecha", "en": "Date"},
    "col_fc": {"es": "Pronóstico", "en": "Forecast"},
    "col_promo": {"es": "Productos en promoción", "en": "Items on promotion"},
    "units": {"es": "unidades", "en": "units"},
    # Calidad
    "q_title": {"es": "Calidad del modelo", "en": "Model quality"},
    "q_intro": {
        "es": "Backtest temporal con 3 cortes de 16 días (29-jun a 15-ago-2017). El modelo nunca ve la ventana que se evalúa.",
        "en": "Time-based backtest with 3 folds of 16 days (Jun 29 – Aug 15, 2017). The model never sees the evaluated window.",
    },
    "q_model": {"es": "Modelo", "en": "Model"},
    "q_bias": {"es": "Sesgo", "en": "Bias"},
    "q_fold": {"es": "Corte", "en": "Fold"},
    "q_real": {"es": "Real", "en": "Actual"},
    "q_agg": {"es": "Venta total diaria en las ventanas de backtest", "en": "Total daily sales in backtest windows"},
    "q_family": {"es": "WAPE por familia", "en": "WAPE by family"},
    "q_imp": {"es": "Importancia de variables (% del gain)", "en": "Feature importance (% of gain)"},
    "q_imp_text": {
        "es": "El nivel reciente de ventas (promedios móviles) explica la mayor parte. Promociones, día de la semana y quincena ajustan ese nivel; feriados y petróleo aportan poco en el periodo validado.",
        "en": "Recent sales level (rolling means) explains most. Promotions, weekday and payday adjust that level; holidays and oil add little in the validated period.",
    },
    "m_lgbm": {"es": "LightGBM global", "en": "Global LightGBM"},
    "m_naive": {"es": "Naive estacional", "en": "Seasonal naive"},
    "m_ma": {"es": "Promedio móvil 14 días", "en": "14-day moving average"},
    # Metodología
    "me_title": {"es": "Metodología y datos", "en": "Methodology & data"},
    "me_arch": {"es": "Arquitectura", "en": "Architecture"},
    "me_clean": {"es": "Limpieza", "en": "Cleaning"},
    "me_clean_text": {
        "es": "- Bronze: CSV tal cual con linaje (`source_file`, `loaded_at`, `batch_id`).\n- Silver: PK/FK; petróleo con forward-fill en fines de semana (marcado `is_imputed`); feriados con traslados, puentes y días de recuperación aplicados.\n- Gold: modelo estrella con `is_payday`, `days_to_payday` y feriado local por tienda (vista).\n- 8 pruebas de calidad en verde: unicidad, ventas ≥ 0, fechas continuas (solo faltan los 25-dic), metadata completa.\n- Hallazgo: antes de jul-2015 hay meses con registro incompleto (PRODUCE casi en cero, BEVERAGES a la mitad). Las comparaciones entre años usan las 18 familias estables y el modelo se entrena desde jul-2015.",
        "en": "- Bronze: raw CSVs with lineage (`source_file`, `loaded_at`, `batch_id`).\n- Silver: PK/FK; oil forward-filled on weekends (flagged `is_imputed`); holidays with transfers, bridges and make-up workdays applied.\n- Gold: star schema with `is_payday`, `days_to_payday` and per-store local holiday (view).\n- 8 data-quality checks passing: uniqueness, sales ≥ 0, continuous dates (only Dec 25 missing), complete metadata.\n- Finding: before Jul 2015 some months are incompletely recorded (PRODUCE near zero, BEVERAGES halved). Year-over-year comparisons use the 18 stable families and the model trains from Jul 2015.",
    },
    "me_model": {"es": "Modelo", "en": "Model"},
    "me_model_text": {
        "es": "LightGBM global sobre `log1p(ventas)` para 1,782 series. Lags de 16 a 42 días y promedios móviles que terminan 16 días antes (igual al horizonte, para no filtrar información), promociones, calendario, quincena, feriados nacionales y locales, metadata de la tienda y petróleo. Entrenado desde julio de 2015.",
        "en": "Global LightGBM on `log1p(sales)` for 1,782 series. Lags of 16–42 days and rolling means ending 16 days back (equal to the horizon, to avoid leakage), promotions, calendar, payday, national and local holidays, store metadata and oil. Trained from July 2015.",
    },
    "me_limits": {"es": "Limitaciones", "en": "Limitations"},
    "me_limits_text": {
        "es": "- Validación en verano 2017: sin diciembre ni feriados grandes.\n- Efectos de promociones y feriados = asociaciones, no causalidad.\n- Unidades, no dólares (el dataset no trae precios).\n- Series intermitentes (BOOKS, BABY CARE) se pronostican mal.\n- Inventario: heurística didáctica.\n- La app usa un snapshot agregado (ventas diarias desde 2016), no la base completa.",
        "en": "- Validated on summer 2017: no December or major holidays.\n- Promotion and holiday effects = associations, not causation.\n- Units, not dollars (no prices in the dataset).\n- Intermittent series (BOOKS, BABY CARE) are poorly forecast.\n- Inventory: teaching heuristic.\n- The app uses an aggregated snapshot (daily sales since 2016), not the full database.",
    },
    "me_source": {"es": "Fuente y términos", "en": "Source & terms"},
    "me_source_text": {
        "es": "Datos de la competencia de Kaggle, usados según sus reglas; los CSV no se redistribuyen en el repositorio.",
        "en": "Data from the Kaggle competition, used under its rules; the CSVs are not redistributed in the repository.",
    },
    "me_repo": {"es": "Código en GitHub", "en": "Code on GitHub"},
}


def lang() -> str:
    return st.session_state.get("lang", "es")


def t(key: str) -> str:
    return TEXTS[key][lang()]
