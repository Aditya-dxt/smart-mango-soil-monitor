"""Synthetic daily weather generator (monsoonal subtropical climate)."""
from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np


@dataclass
class Day:
    doy: int
    month: int
    temp: float          # mean air temperature, deg C
    rh: float            # mean relative humidity, %
    rain: float          # mm
    forecast_rain: float  # mm forecast for the *next* day (noisy)
    et0: float           # reference evapotranspiration, mm/day


_MONTH_STARTS = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])


def month_of(doy: int) -> int:
    return int(np.searchsorted(_MONTH_STARTS, doy, side="left"))


def generate_year(rng: np.random.Generator, days: int = 365) -> list[Day]:
    out: list[Day] = []
    rains = np.zeros(days + 1)
    for d in range(days + 1):
        m = month_of((d % 365) + 1)
        monsoon = m in (7, 8, 9)
        p, mean = (0.45, 14.0) if monsoon else ((0.05, 6.0) if m in (12, 1, 2) else (0.04, 7.0))
        rains[d] = rng.exponential(mean) if rng.random() < p else 0.0
    for d in range(days):
        doy = d + 1
        m = month_of(doy)
        monsoon = m in (7, 8, 9)
        t = 24.5 + 10.5 * math.sin(2 * math.pi * (doy - 55) / 365) + rng.normal(0, 1.5)
        rh = 50 + (25 if monsoon else 0) + rng.normal(0, 8) - 0.6 * (t - 25)
        rh = float(np.clip(rh + (12 if rains[d] > 0 else 0), 15, 98))
        ra = 11 + 4 * math.sin(2 * math.pi * (doy - 80) / 365)
        trange = 13 - (5 if monsoon else 0) + rng.normal(0, 1)
        et0 = 0.0023 * (t + 17.8) * math.sqrt(max(trange, 1.0)) * ra
        et0 *= float(np.clip(1 - 0.3 * (rh - 50) / 50, 0.6, 1.3))
        nxt = rains[d + 1]
        fc = nxt * (0.7 + 0.6 * rng.random()) if nxt > 0 else (3.0 if rng.random() < 0.1 else 0.0)
        out.append(Day(doy, m, float(t), rh, float(rains[d]), float(fc), float(max(et0, 0.3))))
    return out
