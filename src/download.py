"""Obtiene los CSV de la competencia en data/raw.

Orden de intento (ver docs/adr/0002-datos-desde-zip-local.md):
1. Un zip local pasado con --zip (o uno ya presente en data/raw).
2. La API de Kaggle: requiere kaggle.json y haber aceptado las reglas.

Uso:
    python -m src.download                       # API de Kaggle
    python -m src.download --zip ruta/al/archivo.zip
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

from src import config


def faltantes() -> list[str]:
    return [f for f in config.RAW_FILES if not (config.DATA_RAW / f).exists()]


def desde_zip(zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            if Path(name).name in config.RAW_FILES:
                destino = config.DATA_RAW / Path(name).name
                with z.open(name) as src, open(destino, "wb") as dst:
                    dst.write(src.read())


def desde_kaggle() -> None:
    cmd = [
        sys.executable, "-m", "kaggle", "competitions", "download",
        "-c", config.KAGGLE_COMPETITION, "-p", str(config.DATA_RAW),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        msg = r.stderr + r.stdout
        if "403" in msg:
            raise SystemExit(
                "Kaggle respondió 403: acepta las reglas de la competencia en "
                f"{config.KAGGLE_URL}/rules y vuelve a intentar."
            )
        raise SystemExit(f"Falló la descarga de Kaggle (¿existe ~/.kaggle/kaggle.json?):\n{msg}")
    for z in config.DATA_RAW.glob("*.zip"):
        desde_zip(z)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--zip", type=Path, help="zip oficial de la competencia")
    args = p.parse_args(argv)
    config.DATA_RAW.mkdir(parents=True, exist_ok=True)

    if not faltantes():
        print("Los 6 CSV ya están en data/raw; no se descarga nada.")
        return
    if args.zip:
        desde_zip(args.zip)
    else:
        locales = list(config.DATA_RAW.glob("*.zip"))
        desde_zip(locales[0]) if locales else desde_kaggle()

    if faltan := faltantes():
        raise SystemExit(f"Faltan archivos tras la descarga: {faltan}")
    print("Datos listos en", config.DATA_RAW)


if __name__ == "__main__":
    main()
