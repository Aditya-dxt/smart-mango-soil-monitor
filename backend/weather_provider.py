"""Open-Meteo forecast adapter. Network calls are made only by the backend."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone


def fetch_open_meteo(lat: float, lon: float, timeout: float = 8.0) -> dict | None:
    """Fetch a normalized seven-day outlook; return None when unavailable."""
    query = urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum,precipitation_probability_max,et0_fao_evapotranspiration",
        "forecast_days": 7,
        "timezone": "auto",
    })
    url = f"https://api.open-meteo.com/v1/forecast?{query}"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "smart-mango-soil-monitor/1.0"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
        daily = payload["daily"]
        dates = daily["time"]
        rain = daily["precipitation_sum"]
        probability = daily.get("precipitation_probability_max", [None] * len(dates))
        et0 = daily.get("et0_fao_evapotranspiration", [None] * len(dates))
        forecast = []
        for i, day in enumerate(dates):
            forecast.append({
                "date": day,
                "rain_mm": float(rain[i] or 0.0),
                "rain_probability_pct": float(probability[i]) if probability[i] is not None else None,
                "et0_mm": float(et0[i]) if et0[i] is not None else None,
            })
        return {
            "source": "Open-Meteo",
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "timezone": payload.get("timezone", "UTC"),
            "latitude": float(lat),
            "longitude": float(lon),
            "forecast": forecast,
            # Compatibility fields for the existing short-horizon safety guard.
            "rain_today": forecast[0]["rain_mm"] if forecast else 0.0,
            "forecast_rain": forecast[1]["rain_mm"] if len(forecast) > 1 else 0.0,
            "et0": forecast[0]["et0_mm"] if forecast and forecast[0]["et0_mm"] is not None else 3.0,
        }
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        return None
