"""Optional live weather via Open-Meteo (free, no key). Falls back to manual values."""
import json, urllib.request


def fetch_open_meteo(lat: float, lon: float, timeout: float = 8.0) -> dict | None:
    url = ("https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s"
           "&daily=precipitation_sum,et0_fao_evapotranspiration&past_days=1&forecast_days=2"
           "&timezone=auto" % (lat, lon))
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            d = json.load(r)["daily"]
        return {"rain_today": float(d["precipitation_sum"][1] or 0),
                "forecast_rain": float(d["precipitation_sum"][2] or 0),
                "et0": float(d["et0_fao_evapotranspiration"][1] or 3.0)}
    except Exception:
        return None
