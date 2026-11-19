# ADR 0003 · Una rama por fase con merge --no-ff

- **Fecha:** 2026-11-19
- **Estado:** aceptado

## Decisión
Cada fase se trabaja en su propia rama (`feat/setup`, `feat/database`, `feat/ingesta`, `feat/eda`, `feat/modelo`, `feat/app`, `docs/cierre`). Al terminar la fase se sube la rama y se fusiona a `main` con `git merge --no-ff`. Las ramas no se borran, para que el historial muestre el flujo de trabajo.

Los commits siguen Conventional Commits en español y solo se hacen con `pytest -q` en verde.
