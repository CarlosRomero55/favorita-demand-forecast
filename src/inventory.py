"""Recomendación de inventario ILUSTRATIVA (heurística didáctica, no política real de Favorita).

    stock objetivo = pronóstico de los próximos L días + stock de seguridad
    stock de seguridad = z × σ_error_diario × √L

- σ_error_diario: desviación estándar del error diario del backtest de esa tienda–familia.
- z: según el nivel de servicio (90% → 1.28, 95% → 1.64, 98% → 2.05).
- L: tiempo de reposición en días.
Supone errores diarios independientes y aproximadamente normales, lo cual es una simplificación.
"""
from __future__ import annotations

import math

from src import config


def z_for(service_level: float) -> float:
    try:
        return config.SERVICE_LEVELS[round(service_level, 2)]
    except KeyError as e:
        raise ValueError(f"Nivel de servicio no soportado: {service_level}. Usa 0.90, 0.95 o 0.98") from e


def safety_stock(sigma_daily: float, lead_time_days: int, service_level: float) -> float:
    if lead_time_days <= 0:
        raise ValueError("El tiempo de reposición debe ser positivo")
    sigma = 0.0 if sigma_daily is None or math.isnan(sigma_daily) else sigma_daily
    return z_for(service_level) * sigma * math.sqrt(lead_time_days)


def target_stock(forecast_period: float, sigma_daily: float, lead_time_days: int, service_level: float) -> float:
    return max(0.0, forecast_period) + safety_stock(sigma_daily, lead_time_days, service_level)
