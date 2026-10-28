"""Orchard root-zone water-balance environment (gym-like API, numpy only)."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from . import config as C
from .weather import generate_year, Day

STATE_DIM = 1 + len(C.STAGES) + 6


@dataclass
class Obs:
    theta: float
    stage: str
    temp: float
    rh: float
    rain_today: float
    forecast_rain: float
    et0: float
    days_since_irrigation: int

    def vector(self) -> np.ndarray:
        onehot = np.zeros(len(C.STAGES))
        onehot[C.STAGES.index(self.stage)] = 1.0
        return np.concatenate([
            [(self.theta - C.WILTING_POINT) / (C.SATURATION - C.WILTING_POINT)],
            onehot,
            [self.temp / 40.0, self.rh / 100.0, self.rain_today / 30.0,
             self.forecast_rain / 20.0, min(self.days_since_irrigation, 10) / 10.0,
             self.et0 / 8.0],
        ]).astype(np.float32)


class OrchardEnv:
    """One step = one day. Action = index into ``config.ACTIONS_MM``."""

    def __init__(self, seed: int | None = None, days: int = 365):
        self.rng = np.random.default_rng(seed)
        self.days = days
        self.reset()

    def reset(self, seed: int | None = None) -> Obs:
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        self.weather: list[Day] = generate_year(self.rng, self.days)
        self.t = 0
        self.theta = float(self.rng.uniform(15, 28))
        self.since = 5
        self.log = {"water": 0.0, "in_band": 0, "stress": 0, "wet": 0, "drain": 0.0, "events": 0}
        return self._obs()

    def _obs(self) -> Obs:
        w = self.weather[min(self.t, self.days - 1)]
        return Obs(self.theta, C.stage_for_month(w.month), w.temp, w.rh, w.rain,
                   w.forecast_rain, w.et0, self.since)

    def step(self, action: int):
        o = self._obs()
        w = self.weather[self.t]
        irrigation = C.ACTIONS_MM[action]
        lo, hi = C.TARGET_BAND[o.stage]
        # water balance (mm)
        store = C.vwc_to_mm(self.theta) + w.rain + irrigation
        etc = w.et0 * C.KC[o.stage]
        avail = np.clip((self.theta - C.WILTING_POINT) / (0.6 * (C.FIELD_CAPACITY - C.WILTING_POINT)), 0, 1)
        eta = etc * avail
        store -= eta
        drain = 0.0
        fc_mm = C.vwc_to_mm(C.FIELD_CAPACITY)
        if store > fc_mm:
            drain = 0.5 * (store - fc_mm)
            store -= drain
        sat_mm = C.vwc_to_mm(C.SATURATION)
        if store > sat_mm:
            drain += store - sat_mm
            store = sat_mm
        self.theta = float(np.clip(C.mm_to_vwc(store), C.WILTING_POINT - 2, C.SATURATION))
        self.since = 0 if irrigation > 0 else self.since + 1
        # reward
        if lo <= self.theta <= hi:
            r = 1.0
        elif self.theta < lo:
            r = -(lo - self.theta) / 4.0
        else:
            r = -(self.theta - hi) / 6.0
        r -= 0.03 * irrigation
        if irrigation > 0 and o.theta > hi:
            r -= 0.5
        if irrigation > 0 and w.forecast_rain >= 8:
            r -= 0.3
        r -= 0.02 * drain
        L = self.log
        L["water"] += irrigation
        L["events"] += irrigation > 0
        L["drain"] += drain
        L["in_band"] += lo <= self.theta <= hi
        L["stress"] += self.theta < lo
        L["wet"] += self.theta > hi
        self.t += 1
        done = self.t >= self.days
        return (self._obs() if not done else o), float(r), done, {}
