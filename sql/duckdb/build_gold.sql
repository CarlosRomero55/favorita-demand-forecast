-- Llena las dimensiones y fact_sales de gold desde silver (DuckDB). Idempotente.
-- fact_forecast y fact_backtest_metrics las llena src/model.py y no se tocan aquí.
-- Igual que en silver: primero se vacía la tabla hija en su propia transacción.
BEGIN TRANSACTION;
DELETE FROM gold.fact_sales;
COMMIT;

BEGIN TRANSACTION;
DELETE FROM gold.dim_store;
DELETE FROM gold.dim_family;
DELETE FROM gold.dim_date;

INSERT INTO gold.dim_store
SELECT store_nbr, city, state, store_type, cluster,
       state IN ('Manabi', 'Esmeraldas') AS is_earthquake_zone
FROM silver.stores;

INSERT INTO gold.dim_family SELECT family_id, family FROM silver.product_families;

INSERT INTO gold.dim_date
WITH cal AS (
    SELECT CAST(d AS DATE) AS date
    FROM generate_series(DATE '2013-01-01', DATE '2017-08-31', INTERVAL 1 DAY) t(d)
), base AS (
    SELECT date, last_day(date) AS eom,
           CASE WHEN day(date) <= 15 THEN make_date(year(date), month(date), 15) ELSE last_day(date) END AS next_pay,
           CASE WHEN day(date) >= 15 THEN make_date(year(date), month(date), 15)
                ELSE last_day(date - INTERVAL 1 MONTH) END AS prev_pay
    FROM cal
), nat AS (
    SELECT date,
           bool_or(is_day_off) AS off_, bool_or(is_event) AS ev_, bool_or(is_work_day) AS wd_,
           string_agg(description, ' | ' ORDER BY description) AS names
    FROM silver.holidays WHERE locale = 'National' GROUP BY date
)
SELECT b.date, year(b.date), month(b.date), day(b.date),
       isodow(b.date) - 1 AS day_of_week,
       weekofyear(b.date),
       isodow(b.date) IN (6, 7),
       b.date = b.eom,
       day(b.date) = 15 OR b.date = b.eom AS is_payday,
       date_diff('day', b.date, b.next_pay),
       date_diff('day', b.prev_pay, b.date),
       coalesce(n.off_, false), coalesce(n.ev_, false), coalesce(n.wd_, false),
       n.names, o.dcoilwtico
FROM base b
LEFT JOIN nat n USING (date)
LEFT JOIN silver.oil_prices o USING (date);

INSERT INTO gold.fact_sales
SELECT date, store_nbr, family_id, sales, onpromotion FROM silver.daily_sales;

COMMIT;
