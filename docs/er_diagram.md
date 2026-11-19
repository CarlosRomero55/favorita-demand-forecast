# Diagrama entidad–relación

## Silver

```mermaid
erDiagram
  STORES ||--o{ DAILY_SALES : "store_nbr"
  PRODUCT_FAMILIES ||--o{ DAILY_SALES : "family_id"
  STORES ||--o{ FORECAST_REQUESTS : "store_nbr"
  PRODUCT_FAMILIES ||--o{ FORECAST_REQUESTS : "family_id"
  STORES ||--o{ TRANSACTIONS : "store_nbr"
  STORES {
    int store_nbr PK
    string city
    string state
    string store_type
    int cluster
  }
  PRODUCT_FAMILIES {
    int family_id PK
    string family UK
  }
  DAILY_SALES {
    date date PK
    int store_nbr PK,FK
    int family_id PK,FK
    float sales
    int onpromotion
  }
  FORECAST_REQUESTS {
    bigint id PK
    date date
    int store_nbr FK
    int family_id FK
    int onpromotion
  }
  TRANSACTIONS {
    date date PK
    int store_nbr PK,FK
    int transactions
  }
  OIL_PRICES {
    date date PK
    float dcoilwtico
    bool is_imputed
  }
  HOLIDAYS {
    int holiday_id PK
    date date
    string holiday_type
    string locale
    string locale_name
    bool is_day_off
    bool is_work_day
    bool is_event
  }
```

## Gold (modelo estrella)

```mermaid
erDiagram
  DIM_DATE ||--o{ FACT_SALES : "date"
  DIM_STORE ||--o{ FACT_SALES : "store_nbr"
  DIM_FAMILY ||--o{ FACT_SALES : "family_id"
  DIM_STORE ||--o{ FACT_FORECAST : "store_nbr"
  DIM_FAMILY ||--o{ FACT_FORECAST : "family_id"
  FACT_SALES {
    date date PK,FK
    int store_nbr PK,FK
    int family_id PK,FK
    float sales
    int onpromotion
  }
  DIM_DATE {
    date date PK
    bool is_payday
    int days_to_payday
    bool is_holiday_national
    float oil_price
  }
  DIM_STORE {
    int store_nbr PK
    string city
    string state
    bool is_earthquake_zone
  }
  DIM_FAMILY {
    int family_id PK
    string family
  }
  FACT_FORECAST {
    date date PK
    int store_nbr PK
    int family_id PK
    string model_name PK
    string model_version PK
    float forecast
  }
  FACT_BACKTEST_METRICS {
    string model_name PK
    int fold PK
    string segment PK
    float rmsle
    float wape
    float bias
  }
```

Vistas: `gold.v_store_holiday` (feriado nacional, regional o local que aplica a cada tienda), `gold.v_kpi_daily`, `gold.v_kpi_yearly`, `gold.v_kpi_family` y `gold.v_kpi_store`.
