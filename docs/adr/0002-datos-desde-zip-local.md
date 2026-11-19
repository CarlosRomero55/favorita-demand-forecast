# ADR 0002 · Fuente de los datos: API de Kaggle o zip local

- **Fecha:** 2026-11-19
- **Estado:** aceptado

## Contexto
La descarga oficial usa `kaggle competitions download -c store-sales-time-series-forecasting`, que requiere `kaggle.json` y haber aceptado las reglas de la competencia. En este entorno no hay token de Kaggle, pero Carlos subió el zip oficial de la competencia.

## Decisión
`src/download.py` intenta, en orden:
1. Usar un zip local si se pasa `--zip RUTA` (o si ya existe en `data/raw`).
2. La API de Kaggle si hay credenciales.

En ambos casos se verifica que estén los seis CSV esperados.

## Consecuencias
Los CSV nunca se versionan (`/data/raw` está en `.gitignore`), porque son pesados y los términos de la competencia limitan su redistribución.
