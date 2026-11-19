-- Gold: modelo estrella, pronósticos y métricas (DuckDB). Solo DDL y vistas; idempotente.
-- El llenado está en sql/duckdb/build_gold.sql (ejecutado por src/build_gold.py).

CREATE TABLE IF NOT EXISTS gold.dim_store (
    store_nbr          INTEGER PRIMARY KEY,
    city               VARCHAR NOT NULL,
    state              VARCHAR NOT NULL,
    store_type         VARCHAR NOT NULL,
    cluster            INTEGER NOT NULL,
    is_earthquake_zone BOOLEAN NOT NULL   -- Manabí o Esmeraldas
);

CREATE TABLE IF NOT EXISTS gold.dim_family (
    family_id INTEGER PRIMARY KEY,
    family    VARCHAR NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS gold.dim_date (
    date                 DATE PRIMARY KEY,
    year                 INTEGER NOT NULL,
    month                INTEGER NOT NULL,
    day                  INTEGER NOT NULL,
    day_of_week          INTEGER NOT NULL,  -- 0 = lunes ... 6 = domingo
    week_of_year         INTEGER NOT NULL,
    is_weekend           BOOLEAN NOT NULL,
    is_month_end         BOOLEAN NOT NULL,
    is_payday            BOOLEAN NOT NULL,  -- día 15 o último del mes
    days_to_payday       INTEGER NOT NULL,  -- 0 el día de pago
    days_since_payday    INTEGER NOT NULL,
    is_holiday_national  BOOLEAN NOT NULL,
    is_national_event    BOOLEAN NOT NULL,
    is_work_day          BOOLEAN NOT NULL,
    holiday_name         VARCHAR,
    oil_price            DOUBLE
);

CREATE TABLE IF NOT EXISTS gold.fact_sales (
    date        DATE    NOT NULL REFERENCES gold.dim_date (date),
    store_nbr   INTEGER NOT NULL REFERENCES gold.dim_store (store_nbr),
    family_id   INTEGER NOT NULL REFERENCES gold.dim_family (family_id),
    sales       DOUBLE  NOT NULL,
    onpromotion INTEGER NOT NULL,
    PRIMARY KEY (date, store_nbr, family_id)
);

CREATE TABLE IF NOT EXISTS gold.fact_forecast (
    date          DATE    NOT NULL,
    store_nbr     INTEGER NOT NULL,
    family_id     INTEGER NOT NULL,
    model_name    VARCHAR NOT NULL,
    model_version VARCHAR NOT NULL,
    forecast      DOUBLE  NOT NULL,
    onpromotion   INTEGER,
    created_at    TIMESTAMP NOT NULL,
    PRIMARY KEY (date, store_nbr, family_id, model_name, model_version)
);

CREATE TABLE IF NOT EXISTS gold.fact_backtest_metrics (
    model_name    VARCHAR NOT NULL,
    model_version VARCHAR NOT NULL,
    fold          INTEGER NOT NULL,
    cutoff_date   DATE    NOT NULL,
    segment       VARCHAR NOT NULL,  -- 'ALL' o el nombre de la familia
    rmsle         DOUBLE,
    wape          DOUBLE,
    bias          DOUBLE,
    n_rows        INTEGER,
    created_at    TIMESTAMP NOT NULL,
    PRIMARY KEY (model_name, model_version, fold, segment)
);

-- Feriado local o regional que aplica a cada tienda (ciudad o provincia) o nacional
CREATE OR REPLACE VIEW gold.v_store_holiday AS
SELECT d.date,
       s.store_nbr,
       d.is_holiday_national,
       EXISTS (
           SELECT 1 FROM silver.holidays h
           WHERE h.date = d.date AND h.is_day_off
             AND ((h.locale = 'Local' AND h.locale_name = s.city)
               OR (h.locale = 'Regional' AND h.locale_name = s.state))
       ) AS is_holiday_local_for_store
FROM gold.dim_date d
CROSS JOIN gold.dim_store s;

-- KPI: ventas totales diarias con calendario
CREATE OR REPLACE VIEW gold.v_kpi_daily AS
SELECT f.date, d.year, d.month, d.day_of_week, d.is_payday, d.is_holiday_national,
       SUM(f.sales) AS sales, SUM(f.onpromotion) AS items_on_promo
FROM gold.fact_sales f JOIN gold.dim_date d USING (date)
GROUP BY ALL;

-- KPI: ventas anuales y crecimiento (solo años completos tienen crecimiento comparable)
CREATE OR REPLACE VIEW gold.v_kpi_yearly AS
SELECT year, sales, n_days,
       sales / n_days AS avg_daily_sales,
       (sales / n_days) / LAG(sales / n_days) OVER (ORDER BY year) - 1 AS growth_avg_daily
FROM (SELECT year, SUM(sales) AS sales, COUNT(DISTINCT date) AS n_days
      FROM gold.v_kpi_daily GROUP BY year);

-- KPI: ventas por familia
CREATE OR REPLACE VIEW gold.v_kpi_family AS
SELECT fam.family, SUM(f.sales) AS sales,
       SUM(f.sales) / SUM(SUM(f.sales)) OVER () AS share,
       AVG(CASE WHEN f.onpromotion > 0 THEN f.sales END) AS avg_sales_promo,
       AVG(CASE WHEN f.onpromotion = 0 THEN f.sales END) AS avg_sales_no_promo
FROM gold.fact_sales f JOIN gold.dim_family fam USING (family_id)
GROUP BY fam.family;

-- KPI: ventas por tienda
CREATE OR REPLACE VIEW gold.v_kpi_store AS
SELECT s.store_nbr, s.city, s.state, s.store_type, s.cluster, SUM(f.sales) AS sales
FROM gold.fact_sales f JOIN gold.dim_store s USING (store_nbr)
GROUP BY ALL;
