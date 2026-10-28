"""Pretend to be a field node: feed simulator soil/weather data into a running backend.

Usage:
  uvicorn backend.app:app --port 8000          # terminal 1
  python scripts/simulate_node.py --days 30    # terminal 2
Shows the full loop: telemetry -> agent decision -> valve command -> soil response.
"""
import argparse, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json, urllib.request
from datetime import datetime, timedelta, timezone
from mangoagent.env import OrchardEnv
from mangoagent import config as C


def post(url, body, headers=None):
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--key", default="")
    a = ap.parse_args()
    h = {"x-api-key": a.key} if a.key else {}
    env = OrchardEnv(seed=7)
    obs = env.reset()
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for d in range(a.days):
        w = env.weather[env.t]
        for k in range(4):  # a few readings per day (simulated clock)
            ts = (start + timedelta(days=d, hours=6 * k)).isoformat(timespec="seconds")
            # Natural gradual drift in soil parameters
            post(a.url + "/api/telemetry", {
                "ts": ts, "node_id": "sim", "zone": "zone1", "soil_moisture": round(env.theta, 1),
                "soil_temp": round(w.temp - 2.2, 1),
                "air_temp": round(w.temp, 1), "humidity": round(w.rh, 1), "battery": 3.92,
                "nitrogen": round(145.0 + 8.0 * (k % 2) - (d * 0.2 % 15), 1),
                "phosphorus": round(28.0 + 2.0 * (k % 3), 1),
                "potassium": round(190.0 - (d * 0.3 % 20), 1),
                "ph": round(6.65 + 0.05 * (k % 2), 2),
                "soil_type": "Alluvial Loam"
            }, h)
        post(a.url + "/api/weather", {"rain_today": w.rain, "forecast_rain": w.forecast_rain, "et0": w.et0, "month": w.month}, h)
        dec = post(a.url + "/api/agent/run?zone=zone1&force=true", {}, h)
        mm = dec["approved_mm"]
        idx = min(range(len(C.ACTIONS_MM)), key=lambda i: abs(C.ACTIONS_MM[i] - mm))
        obs, *_ = env.step(idx)
        print(f"day {d+1:3d} theta={dec['theta']} stage={dec['stage']:13s} -> {mm:4.0f} mm  {dec['explanation'][:70]}")
        time.sleep(0.05)


if __name__ == "__main__":
    main()
