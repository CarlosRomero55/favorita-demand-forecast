-- Bronze: los CSV tal cual, más columnas de linaje. Idempotente.
-- La carga la hace src/load_bronze.py (borra el lote anterior del mismo archivo e inserta).

CREATE TABLE IF NOT EXISTS bronze.train (
    id BIGINT, date DATE, store_nbr INTEGER, family VARCHAR, sales DOUBLE, onpromotion INTEGER,
    source_file VARCHAR, loaded_at TIMESTAMP, batch_id VARCHAR
);
CREATE TABLE IF NOT EXISTS bronze.test (
    id BIGINT, date DATE, store_nbr INTEGER, family VARCHAR, onpromotion INTEGER,
    source_file VARCHAR, loaded_at TIMESTAMP, batch_id VARCHAR
);
CREATE TABLE IF NOT EXISTS bronze.stores (
    store_nbr INTEGER, city VARCHAR, state VARCHAR, type VARCHAR, cluster INTEGER,
    source_file VARCHAR, loaded_at TIMESTAMP, batch_id VARCHAR
);
CREATE TABLE IF NOT EXISTS bronze.oil (
    date DATE, dcoilwtico DOUBLE,
    source_file VARCHAR, loaded_at TIMESTAMP, batch_id VARCHAR
);
CREATE TABLE IF NOT EXISTS bronze.holidays_events (
    date DATE, type VARCHAR, locale VARCHAR, locale_name VARCHAR, description VARCHAR, transferred BOOLEAN,
    source_file VARCHAR, loaded_at TIMESTAMP, batch_id VARCHAR
);
CREATE TABLE IF NOT EXISTS bronze.transactions (
    date DATE, store_nbr INTEGER, transactions INTEGER,
    source_file VARCHAR, loaded_at TIMESTAMP, batch_id VARCHAR
);
