# Publicación para LinkedIn

## Español

¿Cuánto va a vender cada tienda de un supermercado ecuatoriano las próximas dos semanas? 🛒🇪🇨

Construí un pronóstico de demanda con 3 millones de registros reales de Corporación Favorita (54 tiendas, 33 familias, 2013–2017, dataset público de Kaggle):

🔹 Pipeline Medallion (bronze → silver → gold) en SQL, idempotente y con 8 pruebas de calidad.
🔹 Un modelo LightGBM global para 1,782 series que baja el error (WAPE) de 17.0% a 12.8% frente a repetir la última semana.
🔹 Una app en Streamlit (ES/EN) donde eliges tienda y familia y ves el pronóstico, la banda de error y el stock recomendado según el nivel de servicio.

Lo que más me sorprendió:
📅 La quincena se nota después del pago: los días 1–3 venden 8% más; el día de pago, no.
🏖️ Feriado nacional: +12%. Feriado local: −3.6% en la tienda de esa ciudad (la gente se va).
🏷️ Las promociones parecen duplicar las ventas, pero comparando dentro de la misma tienda y el mismo mes el efecto es de +9%. Correlación ≠ causalidad.
🔍 Antes de 2015 había meses sin registrar que inflaban el crecimiento: detectarlo cambió +33% por un +10% real.

App: https://favorita-demand-forecast-k3bm7c69sld3b67ygiwxnu.streamlit.app/
Código: https://github.com/CarlosRomero55/favorita-demand-forecast

#DataScience #BusinessIntelligence #Forecasting #Python #SQL #LightGBM #Streamlit #Retail #Ecuador

## English

How much will each store of an Ecuadorian supermarket chain sell over the next two weeks? 🛒🇪🇨

I built a demand forecast on 3 million real records from Corporación Favorita (54 stores, 33 product families, 2013–2017, public Kaggle dataset):

🔹 A Medallion pipeline (bronze → silver → gold) in SQL, idempotent, with 8 data-quality checks.
🔹 One global LightGBM model for 1,782 series that cuts the error (WAPE) from 17.0% to 12.8% versus repeating last week.
🔹 A bilingual Streamlit app: pick a store and family to see the forecast, the error band and the recommended stock for a chosen service level.

What surprised me most:
📅 Payday shows up after payday: days 1–3 sell 8% more; payday itself doesn't.
🏖️ National holidays: +12%. Local holidays: −3.6% at that city's store (people leave town).
🏷️ Promotions seem to double sales, but within the same store and month the effect is about +9%. Correlation ≠ causation.
🔍 Before 2015 some months were never recorded, which inflated growth: catching it turned an apparent +33% into a real +10%.

App: https://favorita-demand-forecast-k3bm7c69sld3b67ygiwxnu.streamlit.app/
Code: https://github.com/CarlosRomero55/favorita-demand-forecast

#DataScience #BusinessIntelligence #Forecasting #Python #SQL #LightGBM #Streamlit #Retail
