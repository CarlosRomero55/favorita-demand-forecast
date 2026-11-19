# Publicar la app en Streamlit Community Cloud (≈ 5 minutos)

La app solo lee `app/data/*.parquet` y `app/data/metadata.json`, que ya están versionados. No necesita base de datos, LightGBM ni secretos.

1. Entra a <https://share.streamlit.io> e inicia sesión con tu cuenta de GitHub (`CarlosRomero55`).
2. Haz clic en **Create app** y elige **Deploy a public app from GitHub**.
3. Completa:
   - **Repository:** `CarlosRomero55/favorita-demand-forecast`
   - **Branch:** `main`
   - **Main file path:** `app/streamlit_app.py`
   - **App URL:** por ejemplo `favorita-forecast` (queda `https://favorita-forecast.streamlit.app`).
4. En **Advanced settings**, elige Python 3.12 o superior. Las dependencias salen de `app/requirements.txt` (Streamlit busca primero el archivo junto al script principal).
5. Haz clic en **Deploy**. El primer arranque tarda 1–2 minutos.
6. Copia la URL y reemplaza el marcador `APP_URL_PENDIENTE` en `README.md` y en `portfolio.json`.

## Actualizar los datos de la app
```bash
python -m src.pipeline        # bronze → silver → gold
python -m src.model           # backtest + pronóstico
python -m src.export_snapshot # regenera app/data
pytest -q
git add app/data && git commit -m "chore(app): actualiza snapshot" && git push
```
Streamlit Cloud se redespliega solo al detectar el push a `main`.

## Probar localmente
```bash
pip install -r app/requirements.txt
streamlit run app/streamlit_app.py
```
