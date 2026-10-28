"""FastAPI service: telemetry ingest, agent decisions, valve commands, dashboard."""
from __future__ import annotations
import asyncio, os, statistics
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from mangoagent import config as C
from mangoagent.agent import OrchardAgent, sensor_stuck
from mangoagent.dqn import DQNAgent
from mangoagent.env import STATE_DIM
from mangoagent.llm_advisor import make_advisor
from mangoagent.policies import DQNPolicy, ThresholdRule
from mangoagent.feasibility import evaluate_mango_feasibility
from mangoagent.chatbot import answer_query
from .db import DB
from .mqtt_bridge import MqttBridge
from .weather_provider import fetch_open_meteo

ROOT = Path(__file__).resolve().parents[1]


class Telemetry(BaseModel):
    node_id: str
    zone: str = "zone1"
    soil_moisture: float = Field(..., description="VWC %")
    soil_temp: Optional[float] = None
    air_temp: float
    humidity: float = Field(..., ge=0, le=100)
    battery: Optional[float] = None
    nitrogen: Optional[float] = Field(None, description="Soil Nitrogen (mg/kg)")
    phosphorus: Optional[float] = Field(None, description="Soil Phosphorus (mg/kg)")
    potassium: Optional[float] = Field(None, description="Soil Potassium (mg/kg)")
    ph: Optional[float] = Field(None, ge=3.0, le=10.0, description="Soil pH")
    soil_type: Optional[str] = Field("Alluvial Loam", description="Soil texture type")
    ts: Optional[str] = None


class ChatIn(BaseModel):
    message: str
    zone: str = "zone1"
    context: Optional[dict] = None


class WeatherIn(BaseModel):
    rain_today: float = 0.0
    forecast_rain: float = 0.0
    et0: float = 3.0
    month: Optional[int] = Field(None, ge=1, le=12, description="override calendar month (demo/testing)")


class ValveIn(BaseModel):
    zone: str = "zone1"
    minutes: int = Field(..., ge=0, le=240)


def load_policy(weights: Path):
    if weights.exists():
        a = DQNAgent(STATE_DIM, len(C.ACTIONS_MM))
        a.load(weights)
        return DQNPolicy(a), "dqn"
    return ThresholdRule(), "threshold-fallback"


def create_app(db_path: str | None = None, weights: str | None = None, autorun: bool = True) -> FastAPI:
    db = DB(db_path or os.getenv("DB_PATH", "data/orchard.db"))
    policy, policy_name = load_policy(Path(weights or ROOT / "results" / "dqn_weights.npz"))
    state = {"weather": WeatherIn().model_dump()}
    api_key = os.getenv("API_KEY")  # optional shared secret for write endpoints
    bridge = MqttBridge(lambda p: ingest(Telemetry(**p)))

    def ref_now(zone: str) -> datetime:
        """Reference time = newest sensor timestamp (falls back to the wall clock)."""
        rows = db.telemetry(zone, 1)
        if rows:
            return datetime.fromisoformat(rows[-1]["ts"]).replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc)

    def send_valve(zone: str, minutes: int, source: str = "agent"):
        db.add_command(ref_now(zone).isoformat(timespec="seconds"), zone, minutes, source)
        bridge.send_command(zone, minutes)

    agent = OrchardAgent(policy, actuate=lambda z, m: send_valve(z, m, "agent"),
                         explain=make_advisor())

    def ingest(t: Telemetry):
        rec = t.model_dump()
        rec["ts"] = rec["ts"] or datetime.now(timezone.utc).isoformat(timespec="seconds")
        db.add_telemetry(rec)
        return rec

    def last_decision_age_h(zone: str) -> float:
        for d in db.decisions(200):
            if d["zone"] == zone:
                return (datetime.now(timezone.utc) - datetime.fromisoformat(d["ts"])).total_seconds() / 3600
        return 1e9

    def run_cycle(zone: str, force: bool = False):
        if not force and last_decision_age_h(zone) < 20:
            return None
        rows = db.telemetry(zone, 96)  # ~24 h at 15-min sampling
        now_ref = ref_now(zone)
        cutoff = now_ref - timedelta(hours=24)
        recent = [r for r in rows if datetime.fromisoformat(r["ts"]).replace(tzinfo=timezone.utc) >= cutoff]
        theta = statistics.median([r["soil_moisture"] for r in recent]) if recent else None
        stuck = sensor_stuck([r["soil_moisture"] for r in rows], n=min(24, 96))
        cmds = [c for c in db.recent_commands(100)
                if c["zone"] == zone and c["minutes"] > 0]
        since = 5
        if cmds:
            since = max(0, int((now_ref - datetime.fromisoformat(cmds[0]["ts"]).replace(tzinfo=timezone.utc)).total_seconds() // 86400))
        w = dict(state["weather"])
        if os.getenv("LAT") and os.getenv("LON"):
            live = fetch_open_meteo(float(os.getenv("LAT")), float(os.getenv("LON")))
            if live:
                w = live
        d = agent.decide(
            zone, theta=theta,
            temp=statistics.mean([r["air_temp"] for r in recent]) if recent else 25.0,
            rh=statistics.mean([r["humidity"] for r in recent]) if recent else 60.0,
            rain_today=w["rain_today"], forecast_rain=w["forecast_rain"], et0=w["et0"],
            days_since_irrigation=since, month=w.get("month") or datetime.now().month,
            sensor_ok=bool(recent) and not stuck)
        if stuck:
            d.alerts.append("Soil sensor value has not changed for 24 readings - possible fault.")
        if rows and rows[-1].get("battery") and rows[-1]["battery"] < 3.4:
            d.alerts.append("Node battery low (<3.4 V).")
        db.add_decision(d.to_dict())
        return d

    async def loop():
        interval = int(os.getenv("DECISION_INTERVAL_MIN", "60")) * 60
        while True:
            await asyncio.sleep(interval)
            for z in {r["zone"] for r in db.telemetry(limit=200)}:
                try:
                    run_cycle(z)
                except Exception as e:
                    print("cycle error", z, e)

    @asynccontextmanager
    async def lifespan(app):
        bridge.start()
        task = asyncio.create_task(loop()) if autorun else None
        yield
        if task:
            task.cancel()

    app = FastAPI(title="Bhoomi-IQ - Precision Soil & Feasibility IoT", version="2.0.0", lifespan=lifespan)

    def need_key(x_api_key):
        if api_key and x_api_key != api_key:
            raise HTTPException(401, "invalid API key")

    @app.get("/api/status")
    def status():
        return {"ok": True, "policy": policy_name, "stage_now": C.stage_for_month(datetime.now().month),
                "weather": state["weather"]}

    @app.post("/api/telemetry")
    def post_telemetry(t: Telemetry, x_api_key: str | None = Header(None)):
        need_key(x_api_key)
        rec = ingest(t)
        pend = db.pending_commands(t.zone)  # HTTP-only nodes receive commands in the reply
        return {"stored": True, "ts": rec["ts"], "commands": [{"minutes": c["minutes"]} for c in pend]}

    @app.get("/api/telemetry")
    def get_telemetry(zone: str | None = None, limit: int = 500):
        return db.telemetry(zone, min(limit, 5000))

    @app.get("/api/latest")
    def latest(zone: str = "zone1"):
        rows = db.telemetry(zone, 1)
        if not rows:
            raise HTTPException(404, "no data")
        r = rows[-1]
        lo, hi = C.TARGET_BAND[C.stage_for_month(datetime.now().month)]
        r["target_band"] = [lo, hi]
        r["stage"] = C.stage_for_month(datetime.now().month)
        if not r.get("nitrogen"):
            r["nitrogen"] = 145.0
        if not r.get("phosphorus"):
            r["phosphorus"] = 28.0
        if not r.get("potassium"):
            r["potassium"] = 185.0
        if not r.get("ph"):
            r["ph"] = 6.6
        if not r.get("soil_type"):
            r["soil_type"] = "Alluvial Loam"
        return r

    @app.get("/api/mango-feasibility")
    def mango_feasibility(zone: str = "zone1", soil_type: Optional[str] = None, ph: Optional[float] = None,
                          nitrogen: Optional[float] = None, phosphorus: Optional[float] = None,
                          potassium: Optional[float] = None, moisture: Optional[float] = None,
                          air_temp: Optional[float] = None, humidity: Optional[float] = None):
        rows = db.telemetry(zone, 1)
        lr = rows[-1] if rows else {}
        st = soil_type or lr.get("soil_type") or "Alluvial Loam"
        val_ph = ph if ph is not None else (lr.get("ph") or 6.6)
        val_n = nitrogen if nitrogen is not None else (lr.get("nitrogen") or 145.0)
        val_p = phosphorus if phosphorus is not None else (lr.get("phosphorus") or 28.0)
        val_k = potassium if potassium is not None else (lr.get("potassium") or 185.0)
        val_m = moisture if moisture is not None else (lr.get("soil_moisture") or 18.0)
        val_t = air_temp if air_temp is not None else (lr.get("air_temp") or 29.5)
        val_h = humidity if humidity is not None else (lr.get("humidity") or 58.0)
        return evaluate_mango_feasibility(st, val_ph, val_n, val_p, val_k, val_m, val_t, val_h)

    @app.post("/api/chat")
    async def chat_handler(chat_in: ChatIn):
        ctx = chat_in.context or {}
        if not ctx:
            rows = db.telemetry(chat_in.zone, 1)
            if rows:
                r = rows[-1]
                ctx = {
                    "soil_type": r.get("soil_type") or "Alluvial Loam",
                    "ph": r.get("ph") or 6.6,
                    "nitrogen": r.get("nitrogen") or 145.0,
                    "phosphorus": r.get("phosphorus") or 28.0,
                    "potassium": r.get("potassium") or 185.0,
                    "soil_moisture": r.get("soil_moisture") or 18.0,
                    "air_temp": r.get("air_temp") or 29.5,
                    "humidity": r.get("humidity") or 58.0,
                    "stage": C.stage_for_month(datetime.now().month)
                }
        return await answer_query(chat_in.message, ctx)

    @app.post("/api/weather")
    def set_weather(w: WeatherIn, x_api_key: str | None = Header(None)):
        need_key(x_api_key)
        state["weather"] = w.model_dump()
        return state["weather"]

    @app.post("/api/agent/run")
    def agent_run(zone: str = "zone1", force: bool = True, x_api_key: str | None = Header(None)):
        need_key(x_api_key)
        d = run_cycle(zone, force=force)
        return d.to_dict() if d else {"skipped": "decision made within the last 20 h"}

    @app.get("/api/decisions")
    def decisions(limit: int = 50):
        return db.decisions(min(limit, 500))

    @app.post("/api/valve")
    def manual_valve(v: ValveIn, x_api_key: str | None = Header(None)):
        need_key(x_api_key)
        send_valve(v.zone, v.minutes, "manual")
        return {"queued": True, "zone": v.zone, "minutes": v.minutes}

    @app.get("/api/commands")
    def commands(limit: int = 50):
        return db.recent_commands(limit)

    dash = ROOT / "dashboard"
    if dash.exists():
        app.mount("/static", StaticFiles(directory=dash), name="static")

        @app.get("/")
        def index():
            return FileResponse(dash / "index.html")

    return app


app = create_app() if os.getenv("MANGO_AUTOSTART", "1") == "1" else None
