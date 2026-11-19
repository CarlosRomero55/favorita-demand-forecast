"""Pruebas de calidad de datos sobre silver/gold y reporte en Markdown."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src import config


@dataclass
class Check:
    nombre: str
    ok: bool
    detalle: str


def run_checks(con) -> list[Check]:
    q = lambda s: con.execute(s).fetchone()  # noqa: E731
    checks: list[Check] = []

    dup = q("""SELECT count(*) FROM (SELECT date, store_nbr, family_id FROM silver.daily_sales
               GROUP BY ALL HAVING count(*) > 1)""")[0]
    checks.append(Check("Unicidad fecha–tienda–familia", dup == 0, f"{dup} combinaciones duplicadas"))

    neg = q("SELECT count(*) FROM silver.daily_sales WHERE sales < 0")[0]
    checks.append(Check("Ventas ≥ 0", neg == 0, f"{neg} filas con ventas negativas"))

    # Fechas continuas: los únicos huecos permitidos son los 25 de diciembre (tiendas cerradas)
    faltantes = [r[0] for r in con.execute("""
        SELECT CAST(d AS DATE) FROM generate_series(
            (SELECT min(date) FROM silver.daily_sales), (SELECT max(date) FROM silver.daily_sales), INTERVAL 1 DAY) t(d)
        EXCEPT SELECT DISTINCT date FROM silver.daily_sales ORDER BY 1""").fetchall()]
    solo_navidad = all(f.month == 12 and f.day == 25 for f in faltantes)
    checks.append(Check(
        "Fechas continuas (salvo 25 de diciembre)", solo_navidad,
        f"{len(faltantes)} fechas ausentes: {', '.join(str(f) for f in faltantes)}",
    ))

    sin_meta = q("""SELECT count(DISTINCT store_nbr) FROM silver.daily_sales
                    WHERE store_nbr NOT IN (SELECT store_nbr FROM silver.stores)""")[0]
    checks.append(Check("Todas las tiendas con metadata", sin_meta == 0, f"{sin_meta} tiendas sin metadata"))

    n_tiendas, n_fam = q("SELECT count(*) FROM silver.stores")[0], q("SELECT count(*) FROM silver.product_families")[0]
    incompletos = q(f"""SELECT count(*) FROM (SELECT date FROM silver.daily_sales GROUP BY date
                        HAVING count(*) <> {n_tiendas * n_fam})""")[0]
    checks.append(Check("Panel completo por día (tiendas × familias)", incompletos == 0,
                        f"{incompletos} días sin las {n_tiendas}×{n_fam} combinaciones"))

    oil_nulos = q("SELECT count(*) FROM silver.oil_prices WHERE dcoilwtico IS NULL")[0]
    checks.append(Check("Petróleo sin nulos tras forward-fill", oil_nulos == 0, f"{oil_nulos} nulos"))

    req_ok = q("""SELECT count(*) FROM silver.forecast_requests r
                  LEFT JOIN silver.stores s USING (store_nbr) WHERE s.store_nbr IS NULL""")[0]
    checks.append(Check("Filas de test con tienda válida", req_ok == 0, f"{req_ok} filas sin tienda"))

    gold_vs_silver = q("SELECT (SELECT count(*) FROM gold.fact_sales) - (SELECT count(*) FROM silver.daily_sales)")[0]
    checks.append(Check("gold.fact_sales cuadra con silver", gold_vs_silver == 0, f"diferencia {gold_vs_silver}"))
    return checks


def perfil(con) -> dict:
    """Cifras descriptivas para el reporte (todas salen de los datos)."""
    r = con.execute("""
        SELECT min(date), max(date), count(*),
               sum(CASE WHEN sales = 0 THEN 1 ELSE 0 END) / count(*) AS share_zero
        FROM silver.daily_sales""").fetchone()
    zero_series = con.execute("""
        SELECT count(*) FROM (SELECT store_nbr, family_id FROM silver.daily_sales
                              GROUP BY ALL HAVING sum(sales) = 0)""").fetchone()[0]
    oil_imp = con.execute("SELECT avg(is_imputed::INT) FROM silver.oil_prices").fetchone()[0]
    tx_missing = con.execute("""
        SELECT count(*) FROM (SELECT date, store_nbr FROM silver.daily_sales GROUP BY ALL HAVING sum(sales) > 0)
        a ANTI JOIN silver.transactions t USING (date, store_nbr)""").fetchone()[0]
    store_closed_days = con.execute("""
        SELECT count(*) FROM (SELECT date, store_nbr FROM silver.daily_sales GROUP BY ALL HAVING sum(sales) = 0)""").fetchone()[0]
    hol = con.execute("""SELECT sum(transferred::INT), sum(is_day_off::INT), sum(is_work_day::INT), sum(is_event::INT)
                     FROM silver.holidays""").fetchone()
    return {
        "min_date": r[0], "max_date": r[1], "rows": r[2], "share_zero": r[3],
        "zero_series": zero_series, "oil_imputed": oil_imp, "tx_missing": tx_missing,
        "store_closed_days": store_closed_days, "hol_transferred": hol[0], "hol_day_off": hol[1],
        "hol_work_day": hol[2], "hol_event": hol[3],
    }


def write_report(con, checks: list[Check], conteos: dict[str, int]) -> str:
    p = perfil(con)
    lineas = [
        "# Reporte de calidad de datos",
        "",
        f"Generado automáticamente por `src/pipeline.py` el {datetime.now():%Y-%m-%d %H:%M}.",
        "",
        "## Pruebas",
        "",
        "| Prueba | Resultado | Detalle |",
        "|---|---|---|",
        *[f"| {c.nombre} | {'✅' if c.ok else '❌'} | {c.detalle} |" for c in checks],
        "",
        "## Filas por tabla",
        "",
        "| Tabla | Filas |",
        "|---|---:|",
        *[f"| `{t}` | {n:,} |" for t, n in conteos.items()],
        "",
        "## Perfil de los datos",
        "",
        f"- Periodo de ventas: {p['min_date']} a {p['max_date']} ({p['rows']:,} filas fecha–tienda–familia).",
        f"- {p['share_zero']:.1%} de las filas tienen ventas en cero.",
        f"- {p['zero_series']} series tienda–familia nunca registran ventas (por ejemplo, familias que una tienda no vende).",
        f"- {p['store_closed_days']:,} combinaciones fecha–tienda con ventas totales en cero (tienda cerrada o aún no abierta).",
        f"- {p['tx_missing']:,} combinaciones fecha–tienda con ventas pero sin registro en transactions.",
        f"- Petróleo: {p['oil_imputed']:.1%} de los días del calendario se completaron con forward-fill (fines de semana y feriados de EE. UU.).",
        f"- Feriados: {p['hol_transferred']} feriados trasladados (no cuentan como libres ese día), "
        f"{p['hol_day_off']} registros que sí son días libres, {p['hol_work_day']} días de recuperación (Work Day) "
        f"y {p['hol_event']} eventos.",
        "",
        "## Reglas de limpieza aplicadas",
        "",
        "- Bronze guarda los CSV tal cual, con `source_file`, `loaded_at` y `batch_id`.",
        "- Familias normalizadas en `silver.product_families` con clave sustituta `family_id`.",
        "- Petróleo en calendario completo con forward-fill, y back-fill para el 1-ene-2013; columna `is_imputed`.",
        "- Feriados: `transferred = True` deja de ser feriado ese día; `Transfer`, `Bridge` y `Additional` sí son libres; `Work Day` es laborable.",
        "- Los 25 de diciembre no existen en train (tiendas cerradas): se aceptan como hueco esperado.",
    ]
    texto = "\n".join(lineas) + "\n"
    (config.DOCS_DIR / "data_quality_report.md").write_text(texto, encoding="utf-8")
    return texto
