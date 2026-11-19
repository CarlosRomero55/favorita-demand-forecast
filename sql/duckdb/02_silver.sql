-- Silver: tablas limpias con PK y FK (DuckDB). Solo DDL; idempotente.
-- El llenado está en sql/duckdb/build_silver.sql (ejecutado por src/build_silver.py).

CREATE TABLE IF NOT EXISTS silver.stores (
    store_nbr   INTEGER PRIMARY KEY,
    city        VARCHAR NOT NULL,
    state       VARCHAR NOT NULL,
    store_type  VARCHAR NOT NULL,
    cluster     INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS silver.product_families (
    family_id   INTEGER PRIMARY KEY,
    family      VARCHAR NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS silver.daily_sales (
    date        DATE    NOT NULL,
    store_nbr   INTEGER NOT NULL REFERENCES silver.stores (store_nbr),
    family_id   INTEGER NOT NULL REFERENCES silver.product_families (family_id),
    sales       DOUBLE  NOT NULL CHECK (sales >= 0),
    onpromotion INTEGER NOT NULL CHECK (onpromotion >= 0),
    PRIMARY KEY (date, store_nbr, family_id)
);

-- Filas de test.csv: lo que hay que pronosticar (sin ventas)
CREATE TABLE IF NOT EXISTS silver.forecast_requests (
    id          BIGINT  PRIMARY KEY,
    date        DATE    NOT NULL,
    store_nbr   INTEGER NOT NULL REFERENCES silver.stores (store_nbr),
    family_id   INTEGER NOT NULL REFERENCES silver.product_families (family_id),
    onpromotion INTEGER NOT NULL,
    UNIQUE (date, store_nbr, family_id)
);

CREATE TABLE IF NOT EXISTS silver.transactions (
    date         DATE    NOT NULL,
    store_nbr    INTEGER NOT NULL REFERENCES silver.stores (store_nbr),
    transactions INTEGER NOT NULL,
    PRIMARY KEY (date, store_nbr)
);

-- Calendario completo: los fines de semana y huecos se completan con forward-fill
CREATE TABLE IF NOT EXISTS silver.oil_prices (
    date        DATE PRIMARY KEY,
    dcoilwtico  DOUBLE NOT NULL,
    is_imputed  BOOLEAN NOT NULL
);

-- Feriados con traslados aplicados:
--   is_day_off = feriado efectivo (Holiday no trasladado, Transfer, Bridge, Additional)
--   is_work_day = día laborable de recuperación (Work Day)
--   is_event = evento nacional (Mundial, Black Friday, terremoto, etc.)
CREATE TABLE IF NOT EXISTS silver.holidays (
    holiday_id   INTEGER PRIMARY KEY,
    date         DATE    NOT NULL,
    holiday_type VARCHAR NOT NULL,
    locale       VARCHAR NOT NULL,
    locale_name  VARCHAR NOT NULL,
    description  VARCHAR NOT NULL,
    transferred  BOOLEAN NOT NULL,
    is_day_off   BOOLEAN NOT NULL,
    is_work_day  BOOLEAN NOT NULL,
    is_event     BOOLEAN NOT NULL
);
