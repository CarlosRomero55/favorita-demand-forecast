# Guía de estudio · Favorita Demand Forecast

Por cada componente: **qué es**, **por qué se usó**, **alternativas**, **cómo verificarlo** y **3 preguntas de entrevista** con respuesta modelo.

---

## 1. Arquitectura Medallion (bronze, silver, gold)
- **Qué es:** tres capas de datos. Bronze guarda los archivos tal cual, con linaje. Silver tiene los datos limpios, tipados y con PK/FK. Gold contiene el modelo estrella y las vistas listas para negocio.
- **Por qué:** separa responsabilidades. Si una regla de limpieza cambia, se reconstruye silver/gold sin volver a descargar, y siempre se puede auditar contra el dato original.
- **Alternativas:** un solo script que limpia y modela en memoria (rápido pero poco auditable); dbt sobre un warehouse; un lakehouse con Delta/Parquet.
- **Cómo verificarlo:** `python -m src.pipeline --twice` imprime las filas por capa y verifica que la segunda corrida deja las mismas. `docs/data_quality_report.md` muestra las 8 pruebas.

**Preguntas**
1. *¿Por qué guardar los datos crudos si ya tienes los limpios?* → Para reprocesar cuando cambia una regla sin depender de la fuente, para auditar (linaje con `source_file`, `loaded_at`, `batch_id`) y para depurar diferencias entre capas.
2. *¿Qué va en gold y qué no?* → Lo que consume el negocio o el modelo: hechos al grano fecha–tienda–familia, dimensiones con atributos derivados (quincena, feriados) y vistas de KPI. No van columnas técnicas de carga ni datos sin validar.
3. *¿Por qué DuckDB y no SQL Server?* → El entorno de construcción no permitía instalar SQL Server. DuckDB mantiene la misma arquitectura sin servidor, y los scripts T-SQL equivalentes quedaron en `sql/` (ADR 0001). En una empresa usaría el motor corporativo.

## 2. Ingesta idempotente
- **Qué es:** un proceso que, ejecutado N veces, deja el mismo resultado que ejecutado una vez.
- **Por qué:** los pipelines fallan y se reintentan. Sin idempotencia, cada reintento duplica filas.
- **Alternativas:** `MERGE`/upsert por clave (lo que hacen los scripts T-SQL); borrar e insertar por lote o archivo (lo que se usa en bronze); cargas incrementales con marca de agua.
- **Cómo verificarlo:** `tests/test_pipeline.py::test_pipeline_idempotente_y_reglas` corre el pipeline dos veces sobre datos sintéticos y compara conteos.

**Preguntas**
1. *¿Cómo garantizas que no se dupliquen filas?* → Borrado por `source_file` antes de insertar en bronze, reconstrucción completa en transacción en silver/gold y PK compuesta (fecha, tienda, familia) que rechaza duplicados.
2. *¿Qué problema encontraste con las claves foráneas en DuckDB?* → DuckDB no permite borrar una tabla padre en la misma transacción en que se borraron sus hijas. Se resolvió vaciando las hijas en una transacción previa.
3. *¿BULK INSERT o pandas?* → BULK INSERT es más rápido, pero el servicio de SQL Server necesita permiso de lectura sobre la ruta. Por eso hay un plan B con pandas y `fast_executemany=True`. En DuckDB, `read_csv` cumple ese rol.

## 3. Calidad de datos y el registro incompleto
- **Qué es:** pruebas automáticas (unicidad, rangos, continuidad, integridad referencial) más un perfil de anomalías.
- **Por qué:** un modelo excelente sobre datos malos da conclusiones malas. Aquí, el total mensual mostraba caídas de hasta un tercio que no eran reales: PRODUCE casi en cero y BEVERAGES a la mitad en meses alternos antes de julio de 2015.
- **Alternativas:** Great Expectations, dbt tests, Soda; o revisiones manuales (no escalan).
- **Cómo verificarlo:** `src/quality.py` y `analysis.registration_by_family()`. El hallazgo está en el reporte, en el EDA (sección 1) y en el ADR 0004.

**Preguntas**
1. *¿Cómo detectaste el problema?* → La serie total tenía caídas que se revertían al mes siguiente. Desagregué por familia y vi meses en cero en PRODUCE. La regla formal: venta diaria de la familia igual a 0 o menor al 70% de la mediana centrada de 3 meses.
2. *¿Qué cambió por eso?* → El crecimiento de 2016 bajó de un aparente +33% a +10% comparable (18 familias estables, mismo periodo del año), el índice mensual se calcula con familias estables y el modelo se entrena desde julio de 2015.
3. *¿Por qué no rellenar los meses faltantes?* → Imputar ventas inventa datos que luego entran a las métricas. Prefiero excluir el periodo o las familias afectadas y documentarlo.

## 4. Calendario: quincena, feriados y traslados
- **Qué es:** `gold.dim_date` con `is_payday`, `days_to_payday` y `days_since_payday`, y `gold.v_store_holiday` con el feriado local o regional que aplica a cada tienda.
- **Por qué:** en Ecuador los feriados se trasladan. Un `Holiday` con `transferred=True` no es libre ese día, el `Transfer` sí, los `Bridge` también, y el `Work Day` es laborable. Además, el sector público paga el 15 y el último día del mes.
- **Alternativas:** la librería `holidays` (no trae feriados locales ni traslados de este dataset); flags solo nacionales (pierden el efecto local).
- **Cómo verificarlo:** `tests/test_pipeline.py` comprueba el traslado, el feriado local por tienda, la quincena y `days_to_payday`.

**Preguntas**
1. *¿Por qué separar feriado nacional y local?* → Tienen signos opuestos: +12% nacional frente a −3.6% local en la tienda afectada.
2. *¿Qué es un feriado trasladado?* → El gobierno mueve el descanso a otro día (normalmente para hacer un fin de semana largo). La fecha original deja de ser libre y la nueva sí.
3. *¿Cómo modelas la quincena?* → Con distancia a la fecha de pago (`days_since_payday` y `days_to_payday`), no solo con un flag, porque el efecto aparece en los días posteriores.

## 5. Correlación vs. causalidad en promociones
- **Qué es:** distinguir "las ventas son mayores cuando hay promoción" de "la promoción causa más ventas".
- **Por qué:** la comparación ingenua de GROCERY I da +121%; dentro de la misma tienda y el mismo mes da +6.5%. Las promociones crecieron con el tiempo y se concentran en tiendas grandes (confusión).
- **Alternativas:** experimentos A/B por tienda o semana (el estándar); diferencias en diferencias; modelos causales con controles; variables instrumentales.
- **Cómo verificarlo:** `analysis.promo_lift()` devuelve el lift ingenuo y el estratificado por familia.

**Preguntas**
1. *¿El modelo prueba que la promoción aumenta ventas en 43%?* → No. SHAP mide cómo el modelo usa la variable, no un efecto causal. Favorita probablemente promociona lo que ya espera vender más.
2. *¿Cómo medirías el efecto real?* → Con un experimento: asignar promociones al azar a tiendas comparables y comparar contra control, o al menos diferencias en diferencias con tiendas sin promoción.
3. *¿Por qué estratificar por tienda–familia–mes?* → Para comparar promoción contra no-promoción en condiciones similares de tamaño de tienda y temporada, lo que quita parte de la confusión, aunque no toda.

## 6. Fuga de información y lags ≥ horizonte
- **Qué es:** usar en el entrenamiento información que no estaría disponible al momento de pronosticar.
- **Por qué:** si el horizonte es de 16 días, el día 16 del pronóstico no conoce las ventas de los 15 días anteriores. Si el modelo usa `lag_1`, en validación parece excelente y en producción falla.
- **Cómo se evitó:** todos los lags son ≥ 16 días (16, 21, 28, 35 y 42) y los promedios móviles terminan en t−16. Un solo modelo sirve para todo el horizonte. El petróleo también se usa con 16 días de desfase.
- **Alternativas:** modelos directos (uno por horizonte con lags ≥ h); estrategia recursiva (se alimenta de sus propios pronósticos y acumula error).
- **Cómo verificarlo:** `tests/test_model.py::test_lags_no_usan_informacion_del_horizonte`. Además, el *early stopping* usa los 16 días previos al corte, nunca la ventana evaluada.

**Preguntas**
1. *¿Por qué no usar `lag_1`?* → No existe para los días 2 a 16 del horizonte. Habría que pronosticar recursivamente o entrenar 16 modelos.
2. *¿Dónde más puede haber fuga?* → En el *early stopping* sobre la ventana de prueba, en normalizar con estadísticas de todo el periodo, en variables exógenas futuras (petróleo) y en promedios móviles centrados.
3. *¿`onpromotion` del día no es fuga?* → No, si el plan de promociones se conoce de antemano (viene en `test.csv`). En producción requiere tener ese plan cargado a tiempo; está documentado como limitación.

## 7. Validación temporal (backtest)
- **Qué es:** evaluar en ventanas futuras respecto al entrenamiento: 3 cortes de 16 días (29-jun a 15-ago-2017).
- **Por qué:** con series de tiempo, la validación cruzada aleatoria mezcla pasado y futuro y sobreestima la exactitud.
- **Alternativas:** una sola ventana (inestable); más cortes o ventanas que se expanden; validar en temporada alta.
- **Cómo verificarlo:** `model.fold_windows()` y su prueba; `gold.fact_backtest_metrics`.

**Preguntas**
1. *¿Por qué 3 cortes y no 1?* → Para ver la variabilidad: el RMSLE va de 0.378 a 0.423 según el corte.
2. *¿Qué limita tu validación?* → Es verano: no hay diciembre ni feriados nacionales grandes, así que el error en temporada alta probablemente sea mayor.
3. *¿Cómo eliges el número de iteraciones del modelo final?* → Promedio de las mejores iteraciones de los cortes × 1.05, porque el modelo final ve un poco más de datos.

## 8. RMSLE vs. WAPE (y sesgo)
- **RMSLE:** error cuadrático sobre `log(1+y)`. Penaliza errores relativos, así que equivocarse 10 contra 20 pesa parecido a 1,000 contra 2,000. Es la métrica de la competencia y se optimiza entrenando con RMSE sobre `log1p`.
- **WAPE:** Σ|error| / Σ real. Se entiende como "me equivoco un X% del volumen" y pesa más los productos grandes. Es la métrica de negocio.
- **Sesgo:** Σ(pronóstico − real) / Σ real. Indica si se sobre- o subpronostica (−1.7% aquí: riesgo de quiebre).
- **Alternativas:** MAPE (explota con ventas cercanas a 0), MASE, *pinball loss* para cuantiles.

**Preguntas**
1. *¿Por qué no MAPE?* → Hay 31% de filas con ventas 0: MAPE se indefine o explota.
2. *¿Cuál reportas a un gerente?* → WAPE (12.8% frente a 17.0% del naive) y el sesgo. El RMSLE es para comparar modelos.
3. *¿Puede un modelo mejorar el RMSLE y empeorar el WAPE?* → Sí: el promedio móvil de 14 días tiene mejor RMSLE que el naive (0.485 frente a 0.552) pero peor WAPE (22.6% frente a 17.0%), porque acierta en series chicas y falla el patrón semanal en las grandes.

## 9. Modelo global vs. uno por serie
- **Qué es:** un único LightGBM entrenado con las 1,782 series a la vez, con tienda y familia como variables categóricas.
- **Por qué:** comparte patrones entre series (las series chicas aprenden de las grandes), se mantiene un solo modelo y escala mejor. Los ganadores de competencias de retail (Favorita 2017, M5) usaron modelos globales.
- **Alternativas:** ARIMA/ETS o Prophet por serie (1,782 modelos que mantener y peores con series cortas o intermitentes); redes neuronales globales (N-BEATS, TFT); modelos jerárquicos con reconciliación.
- **Cómo verificarlo:** comparación contra los baselines en `notebooks/02_model.ipynb`: gana en 32 de 33 familias.

**Preguntas**
1. *¿Cuándo preferirías modelos por serie?* → Con pocas series largas y estables, cuando se necesita interpretar cada serie, o cuando las series no comparten patrones.
2. *¿Por qué `log1p` como objetivo?* → Estabiliza la varianza entre series de escalas muy distintas y hace que el RMSE optimizado sea el RMSLE.
3. *¿Qué harías con BOOKS o BABY CARE?* → Son series intermitentes (más de 90% de días en cero). Usaría Croston/TSB o un modelo de dos partes (probabilidad de venta × cantidad).

## 10. Importancia de variables (gain y SHAP)
- **Gain:** cuánto reduce el error cada variable en los cortes de los árboles. Es global y rápido.
- **SHAP:** cuánto aporta cada variable a cada predicción, con dirección. Se calculó sobre una muestra de 4,000 filas.
- **Resultado para negocio:** el 89% del gain viene de promedios móviles de ventas recientes. Promociones, domingo y quincena ajustan en la dirección esperada.

**Preguntas**
1. *¿Por qué feriados aparecen con gain casi 0 si el EDA muestra +12%?* → Hay pocos feriados en dos años de entrenamiento, y en las ventanas validadas solo cae uno nacional. Además, el gain mide la reducción de error total, no el tamaño del efecto en los días raros.
2. *¿Gain o SHAP?* → Gain para un ranking rápido; SHAP para dirección y explicación por fila.
3. *¿Importancia alta significa causa?* → No. Significa que el modelo usa la variable para predecir.

## 11. Recomendación de inventario
- **Qué es:** stock objetivo = pronóstico de L días + z × σ × √L, donde σ es la desviación del error diario del backtest de esa tienda–familia.
- **Por qué:** traduce el pronóstico y su incertidumbre en una cantidad accionable según el nivel de servicio (90/95/98%).
- **Limitación:** es una heurística didáctica. Supone errores independientes y normales e ignora stock en tránsito, vida útil, mínimos de pedido y costos.
- **Cómo verificarlo:** `tests/test_model.py::test_inventario` y la página **Explorador** de la app.

**Preguntas**
1. *¿Por qué √L?* → Si los errores diarios son independientes, la varianza de la suma de L días es L·σ², y su desviación es σ√L.
2. *¿Qué pasa al subir de 95% a 98%?* → z sube de 1.64 a 2.05: el colchón crece 25% para reducir los quiebres de 5% a 2% de los ciclos.
3. *¿Cómo lo mejorarías?* → Con pronósticos por cuantiles (*pinball loss*), lead times reales, revisión periódica (s, S) y costos de quiebre frente a costos de exceso.

## 12. App y snapshot
- **Qué es:** Streamlit sobre archivos Parquet agregados (cada uno de menos de 5 MB). La app no se conecta a la base ni carga el modelo.
- **Por qué:** se publica gratis en Streamlit Community Cloud, carga rápido y no expone credenciales.
- **Alternativas:** Power BI (licencias y menos interactividad tipo "elige tienda"); Dash; una API con FastAPI más un frontend.
- **Cómo verificarlo:** `tests/test_app.py` carga las 5 páginas en ES y EN con `AppTest`.

**Preguntas**
1. *¿Por qué no conectar la app a la base?* → Requiere un servidor y credenciales, y la app solo necesita resúmenes. El snapshot desacopla el análisis de la presentación.
2. *¿Cómo actualizas la app?* → `pipeline` → `model` → `export_snapshot` → commit y push. Streamlit Cloud se redespliega solo.
3. *¿Cómo pruebas una app de Streamlit?* → Con `streamlit.testing.v1.AppTest`: corre los scripts sin navegador, interactúa con los widgets y verifica que no haya excepciones.
