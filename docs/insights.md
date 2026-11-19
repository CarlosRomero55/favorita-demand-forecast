# 5 hallazgos para un gerente de supermercado

Todas las cifras salen de `notebooks/01_eda.ipynb`, `notebooks/02_model.ipynb` y `app/data/metadata.json`. Los efectos son **asociaciones observadas** frente a días comparables (mismo año, mes y día de la semana), no efectos causales probados.

---

### 1. El fin de semana y diciembre definen la carga de trabajo
- **Dato:** el domingo vende 31% más que el promedio del mes y el sábado 22% más; el jueves es el día más flojo (−21%). Con las familias de registro estable, diciembre está 32% sobre el promedio anual y los días 21–24 de diciembre venden 24% más que un día normal comparable.
- **Interpretación:** la demanda se concentra en 2 de 7 días y en un mes del año.
- **Acción:** reponer jueves y viernes para llegar con góndola llena al fin de semana, reforzar personal sábado y domingo, y planificar diciembre con su propio pronóstico, no con el promedio del año.

### 2. La quincena se nota después del pago, no el mismo día
- **Dato:** el día de pago (15 o fin de mes) vende 3% menos que un día normal comparable. El día siguiente vende 8% más y del día 2 al 6 se mantiene entre +3% y +6%. Antes del siguiente pago cae hasta −6%. Los días 1–3 tras el pago venden 8% más que el resto.
- **Interpretación:** el gasto llega con uno o dos días de retraso respecto al pago (el sector público paga el 15 y el último día del mes, según la descripción del dataset).
- **Acción:** programar la reposición y las promociones para el 16 y el día 1, no para el día de pago.

### 3. Feriado nacional sí, feriado local no
- **Dato:** en feriado nacional la cadena vende 12% más (mediana, 46 días). En un feriado local o regional, la tienda de esa ciudad o provincia vende 3.6% menos (mediana, 354 días-tienda).
- **Interpretación:** en feriados locales la gente probablemente sale de la ciudad, así que la demanda se va a otras tiendas.
- **Acción:** no copiar el plan de feriado nacional a los locales. Para feriados locales, reducir la reposición en la tienda afectada y revisar las tiendas de destino turístico.

### 4. Las promociones mueven menos de lo que parece, y más en frescos
- **Dato:** la comparación ingenua sugiere que GROCERY I vende 121% más con promoción. Comparando dentro de la misma tienda y el mismo mes, el lift es de +6.5%. Ponderado por ventas, el lift estratificado es de +9%. En frescos es mayor: PRODUCE +20%, MEATS +21%, POULTRY +12%; en DAIRY y CLEANING, +3%.
- **Interpretación:** las promociones crecieron con el tiempo y se concentran en tiendas grandes, lo que infla la comparación simple. Es asociación, no causalidad: no sabemos cómo se eligieron los productos promocionados.
- **Acción:** medir las promociones con grupos de control (tiendas o semanas sin promoción) antes de escalarlas, y priorizar frescos, donde la respuesta observada es mayor.

### 5. Un pronóstico por tienda–familia reduce el error una cuarta parte
- **Dato:** el modelo global LightGBM tiene un WAPE de 12.8% frente a 17.0% del naive estacional (repetir la última semana) y un RMSLE de 0.405 frente a 0.552. Gana en los 3 cortes de validación y en 32 de 33 familias. El total diario de la cadena se equivoca 4.5%, con un sesgo de −1.7%.
- **Interpretación:** el nivel reciente de ventas explica la mayor parte; día de la semana, promociones y quincena ajustan. El sesgo negativo implica riesgo de quiebre si se usa sin colchón.
- **Acción:** usar el pronóstico más un stock de seguridad según el nivel de servicio. Ejemplo ilustrativo, tienda 44 (Quito) · GROCERY I, reposición de 7 días: pronóstico de 71,232 unidades y colchón de 4,668 al 95%. Para familias intermitentes (BOOKS, BABY CARE) conviene otro método.

---

**Nota de calidad de datos.** Antes de julio de 2015 hay meses con registro incompleto (PRODUCE casi en cero, BEVERAGES a la mitad). Por eso los crecimientos se calculan con las 18 familias de registro estable: +10% en 2016 y +9% en 2017 (1-ene a 15-ago vs. el mismo periodo del año anterior). Ver ADR 0004.
