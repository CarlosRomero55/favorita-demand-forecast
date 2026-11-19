-- Llena silver desde bronze (DuckDB). Idempotente: vacía hijos, luego padres, y reinserta.
-- DuckDB no permite borrar un padre en la misma transacción en que se borraron sus hijos,
-- por eso los hijos se vacían en una transacción previa.
BEGIN TRANSACTION;
DELETE FROM silver.daily_sales;
DELETE FROM silver.forecast_requests;
DELETE FROM silver.transactions;
COMMIT;

BEGIN TRANSACTION;
DELETE FROM silver.stores;
DELETE FROM silver.product_families;
DELETE FROM silver.oil_prices;
DELETE FROM silver.holidays;

INSERT INTO silver.stores
SELECT DISTINCT store_nbr, trim(city), trim(state), trim(type), cluster
FROM bronze.stores;

INSERT INTO silver.product_families
SELECT row_number() OVER (ORDER BY family) AS family_id, family
FROM (SELECT DISTINCT trim(family) AS family FROM bronze.train
      UNION SELECT DISTINCT trim(family) FROM bronze.test);

INSERT INTO silver.daily_sales
SELECT b.date, b.store_nbr, f.family_id, b.sales, b.onpromotion
FROM bronze.train b
JOIN silver.product_families f ON f.family = trim(b.family);

INSERT INTO silver.forecast_requests
SELECT b.id, b.date, b.store_nbr, f.family_id, b.onpromotion
FROM bronze.test b
JOIN silver.product_families f ON f.family = trim(b.family);

INSERT INTO silver.transactions
SELECT date, store_nbr, max(transactions)
FROM bronze.transactions
GROUP BY date, store_nbr;

-- Petróleo: calendario completo; forward-fill y back-fill para el 1-ene-2013 (sin dato)
INSERT INTO silver.oil_prices
WITH cal AS (
    SELECT CAST(d AS DATE) AS date
    FROM generate_series(DATE '2013-01-01', DATE '2017-08-31', INTERVAL 1 DAY) t(d)
), j AS (
    SELECT c.date, o.dcoilwtico,
           last_value(o.dcoilwtico IGNORE NULLS) OVER (ORDER BY c.date ROWS UNBOUNDED PRECEDING) AS ffill,
           first_value(o.dcoilwtico IGNORE NULLS) OVER (ORDER BY c.date ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING) AS bfill
    FROM cal c LEFT JOIN bronze.oil o USING (date)
)
SELECT date, coalesce(ffill, bfill), dcoilwtico IS NULL
FROM j;

-- Feriados con traslados: un Holiday trasladado deja de ser feriado ese día;
-- Transfer, Bridge y Additional sí son días libres; Work Day es laborable.
INSERT INTO silver.holidays
SELECT row_number() OVER (ORDER BY date, locale, locale_name, description) AS holiday_id,
       date, type, locale, locale_name, description, transferred,
       (type = 'Holiday' AND NOT transferred) OR type IN ('Transfer', 'Bridge', 'Additional') AS is_day_off,
       type = 'Work Day' AS is_work_day,
       type = 'Event' AS is_event
FROM bronze.holidays_events;

COMMIT;
