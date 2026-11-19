"""Orquesta el pipeline completo: descarga → bronze → silver → gold → calidad.

Es idempotente: ejecutarlo dos veces deja exactamente las mismas filas.

Uso:
    python -m src.pipeline [--zip ruta.zip] [--twice]
"""
from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

from src import build_gold, build_silver, config, db, download, load_bronze, quality

config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(config.LOGS_DIR / "pipeline.log", encoding="utf-8")],
)
log = logging.getLogger("pipeline")


def run_once() -> dict[str, int]:
    t0 = time.time()
    with db.connect() as con:
        conteos = {f"bronze.{k}": v for k, v in load_bronze.load(con).items()}
        log.info("bronze listo")
        conteos |= {f"silver.{k}": v for k, v in build_silver.build(con).items()}
        log.info("silver listo")
        conteos |= {f"gold.{k}": v for k, v in build_gold.build(con).items()}
        log.info("gold listo")
        checks = quality.run_checks(con)
        quality.write_report(con, checks, conteos)
    for c in checks:
        log.info("%s %s — %s", "OK " if c.ok else "FALLA", c.nombre, c.detalle)
    if not all(c.ok for c in checks):
        raise SystemExit("Hay pruebas de calidad en rojo; revisar docs/data_quality_report.md")
    log.info("pipeline terminado en %.1f s", time.time() - t0)
    return conteos


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--zip", type=Path)
    p.add_argument("--twice", action="store_true", help="ejecuta dos veces y verifica idempotencia")
    args = p.parse_args(argv)
    download.main(["--zip", str(args.zip)] if args.zip else [])
    primera = run_once()
    if args.twice:
        segunda = run_once()
        assert primera == segunda, f"No es idempotente: {primera} vs {segunda}"
        log.info("Idempotencia verificada: mismas filas en las dos corridas")


if __name__ == "__main__":
    main()
