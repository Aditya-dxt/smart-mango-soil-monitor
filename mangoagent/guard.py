"""Deterministic safety guard. The learned/LLM layers may *propose*; only the guard *approves*."""
from __future__ import annotations
from dataclasses import dataclass, field
from . import config as C


@dataclass
class GuardResult:
    mm: float
    reasons: list[str] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)
    overridden: bool = False


class SafetyGuard:
    def __init__(self, max_event_mm=20.0, max_weekly_mm=60.0, rain_block_mm=8.0,
                 rain_today_block_mm=5.0, sensor_min=0.0, sensor_max=60.0):
        self.max_event_mm = max_event_mm
        self.max_weekly_mm = max_weekly_mm
        self.rain_block_mm = rain_block_mm
        self.rain_today_block_mm = rain_today_block_mm
        self.sensor_min, self.sensor_max = sensor_min, sensor_max

    def review(self, proposed_mm: float, *, theta: float | None, stage: str, rain_today: float,
               forecast_rain: float, mm_last_7d: float, sensor_ok: bool = True) -> GuardResult:
        res = GuardResult(mm=float(proposed_mm))
        lo, hi = C.TARGET_BAND[stage]
        if theta is None or not sensor_ok or not (self.sensor_min <= theta <= self.sensor_max):
            res.mm = 0.0
            res.overridden = proposed_mm > 0
            res.alerts.append("Sensor reading missing or implausible - irrigation withheld until it is checked.")
            res.reasons.append("sensor fault")
            return res
        if res.mm > 0 and (rain_today >= self.rain_today_block_mm or forecast_rain >= self.rain_block_mm):
            res.mm, res.overridden = 0.0, True
            res.reasons.append("rain today/forecast is enough")
        if res.mm > 0 and theta >= hi:
            res.mm, res.overridden = 0.0, True
            res.reasons.append("soil already at or above target band")
        if res.mm > 0 and stage == "pre_flowering" and theta > C.WILTING_POINT + 3:
            res.mm, res.overridden = 0.0, True
            res.reasons.append("pre-flowering: mild dryness is intentional")
        if res.mm > self.max_event_mm:
            res.mm, res.overridden = self.max_event_mm, True
            res.reasons.append("capped to per-event maximum")
        if res.mm > 0 and mm_last_7d + res.mm > self.max_weekly_mm:
            res.mm = max(0.0, self.max_weekly_mm - mm_last_7d)
            res.overridden = True
            res.reasons.append("weekly water budget reached")
        # emergency: severe stress outside the deliberate dry phase
        if (res.mm == 0 and theta <= C.WILTING_POINT + 2 and stage != "pre_flowering"
                and forecast_rain < self.rain_block_mm and rain_today < self.rain_today_block_mm):
            res.mm, res.overridden = 12.0, True
            res.reasons.append("emergency: near wilting point")
            res.alerts.append("Soil is near wilting point - emergency irrigation scheduled.")
        if stage == "pre_flowering" and theta <= C.WILTING_POINT + 1:
            res.alerts.append("Very dry even for pre-flowering - check trees for severe stress.")
        return res
