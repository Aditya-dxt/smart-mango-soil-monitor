"""Explainable, forecast-aware irrigation advice (never actuates hardware)."""
from __future__ import annotations

from datetime import datetime, timezone

from mangoagent import config as C


# Starting advisory thresholds only. Calibrate to the orchard's soil, probe,
# cultivar, drainage and local extension guidance before relying on them.
MEANINGFUL_RAIN_MM = 8.0
HEAVY_RAIN_MM = 25.0
RAIN_PROBABILITY_THRESHOLD = 50.0


def recommend_irrigation(soil_moisture: float | None, month: int,
                         forecast: list[dict] | None, sensor_ok: bool = True) -> dict:
    stage = C.stage_for_month(month)
    low, high = C.TARGET_BAND[stage]
    days = forecast or []
    rain_next_48h = sum(day.get("rain_mm", 0) or 0 for day in days[:2])
    rain_week = sum(day.get("rain_mm", 0) or 0 for day in days[:7])
    rain_days = [day for day in days[:7]
                 if (day.get("rain_mm", 0) or 0) >= MEANINGFUL_RAIN_MM
                 and (day.get("rain_probability_pct") is None
                      or day["rain_probability_pct"] >= RAIN_PROBABILITY_THRESHOLD)]
    heavy_days = [day for day in days[:7] if (day.get("rain_mm", 0) or 0) >= HEAVY_RAIN_MM]

    base = {
        "available": soil_moisture is not None and sensor_ok and bool(days),
        "stage": stage,
        "soil_moisture_pct": soil_moisture,
        "target_band_pct": [low, high],
        "rain_next_48h_mm": round(rain_next_48h, 1),
        "rain_next_7d_mm": round(rain_week, 1),
        "meaningful_rain_dates": [day["date"] for day in rain_days],
        "heavy_rain_dates": [day["date"] for day in heavy_days],
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "automatic_action": False,
    }
    if soil_moisture is None or not sensor_ok:
        return {**base, "action": "check_sensor", "summary": "Check the soil sensor before deciding to irrigate."}
    if not days:
        return {**base, "available": False, "action": "recheck", "summary": "Forecast unavailable; recheck the soil and local weather before irrigation."}
    if soil_moisture >= high:
        if heavy_days:
            msg = "Do not irrigate. Soil is already at or above its target; heavy rain is forecast, so check drainage and recheck after the rain."
        else:
            msg = "Do not irrigate now. Soil is already at or above its target; recheck moisture before the next watering."
        return {**base, "action": "hold", "summary": msg}
    if heavy_days:
        return {**base, "action": "waterlogging_watch",
                "summary": "Delay irrigation and check drainage: heavy rain is forecast. Recheck soil moisture after rainfall."}
    if soil_moisture < low and rain_next_48h >= MEANINGFUL_RAIN_MM:
        return {**base, "action": "wait_and_recheck",
                "summary": "Soil is below its target, but useful rain is forecast in the next 48 hours. Consider waiting and recheck moisture after the rain."}
    if soil_moisture < low and rain_days:
        return {**base, "action": "plan_irrigation",
                "summary": "Soil is below its target. Rain is forecast later this week; check moisture daily and irrigate only if it remains below target before then."}
    if soil_moisture < low:
        return {**base, "action": "irrigation_may_be_needed",
                "summary": "Soil is below its target and meaningful rain is not forecast this week. Consider irrigation using local crop guidance, then recheck moisture."}
    return {**base, "action": "monitor", "summary": "Soil is within its target band. Monitor moisture and the updated forecast before the next irrigation."}
