"""Agentic control loop: perceive -> reason -> guard -> act -> remember.

Tools the agent can call are plain callables injected at construction, so the same
agent runs against the simulator, the HTTP/MQTT backend, or unit-test fakes.
"""
from __future__ import annotations
import statistics
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Callable, Optional
from . import config as C
from .env import Obs
from .guard import SafetyGuard


@dataclass
class Decision:
    ts: str
    zone: str
    stage: str
    theta: Optional[float]
    proposed_mm: float
    approved_mm: float
    minutes: int
    reasons: list = field(default_factory=list)
    alerts: list = field(default_factory=list)
    advisories: list = field(default_factory=list)
    explanation: str = ""

    def to_dict(self): return asdict(self)


def crop_advisories(stage: str, temp: float, rh: float) -> list[str]:
    """Heuristic orchard advisories. Validate with local extension guidance."""
    out = []
    if stage == "flowering" and temp >= 40:
        out.append("Heat stress during flowering (>=40 C): consider light cooling irrigation and shade checks.")
    if stage in ("flowering", "fruit_dev") and rh >= 85 and 20 <= temp <= 32:
        out.append("Warm, very humid weather favours fungal disease (e.g. anthracnose): scout panicles and fruit.")
    if stage == "flowering" and temp <= 10:
        out.append("Cold night risk for panicles and fruit set.")
    return out


def sensor_stuck(values: list[float], n: int = 24, tol: float = 1e-6) -> bool:
    return len(values) >= n and statistics.pstdev(values[-n:]) < tol


class OrchardAgent:
    def __init__(self, policy, guard: SafetyGuard | None = None,
                 actuate: Callable[[str, int], None] | None = None,
                 explain: Callable[[Decision], str] | None = None):
        self.policy = policy
        self.guard = guard or SafetyGuard()
        self.actuate = actuate or (lambda zone, minutes: None)
        self.explain = explain
        self.memory: deque[Decision] = deque(maxlen=500)
        self.irrigation_log: dict[str, deque] = {}

    def mm_last_7d(self, zone: str) -> float:
        return float(sum(self.irrigation_log.get(zone, [])))

    def decide(self, zone: str, *, theta: Optional[float], temp: float, rh: float,
               rain_today: float, forecast_rain: float, et0: float,
               days_since_irrigation: int, month: int, sensor_ok: bool = True) -> Decision:
        stage = C.stage_for_month(month)
        # perceive -> reason
        if theta is None:
            proposed = 0
        else:
            obs = Obs(theta, stage, temp, rh, rain_today, forecast_rain, et0, days_since_irrigation)
            proposed = self.policy.propose(obs)
        proposed_mm = C.ACTIONS_MM[proposed]
        # guard
        g = self.guard.review(proposed_mm, theta=theta, stage=stage, rain_today=rain_today,
                              forecast_rain=forecast_rain, mm_last_7d=self.mm_last_7d(zone),
                              sensor_ok=sensor_ok)
        minutes = C.mm_to_minutes(g.mm)
        d = Decision(datetime.now(timezone.utc).isoformat(timespec="seconds"), zone, stage, theta,
                     proposed_mm, g.mm, minutes, g.reasons, g.alerts,
                     crop_advisories(stage, temp, rh))
        d.explanation = self._explain(d)
        # act
        if minutes > 0:
            self.actuate(zone, minutes)
        # remember
        log = self.irrigation_log.setdefault(zone, deque([0.0] * 7, maxlen=7))
        log.append(g.mm)
        self.memory.append(d)
        return d

    def _explain(self, d: Decision) -> str:
        if self.explain:
            try:
                return self.explain(d)
            except Exception:  # advisor must never break control
                pass
        lo, hi = C.TARGET_BAND[d.stage]
        th = "n/a" if d.theta is None else f"{d.theta:.1f}%"
        base = f"Stage {d.stage}; soil moisture {th} (target {lo:.0f}-{hi:.0f}%). "
        if d.approved_mm > 0:
            base += f"Irrigating {d.approved_mm:.0f} mm (~{d.minutes} min)."
        else:
            base += "No irrigation today."
        if d.reasons:
            base += " Guard: " + "; ".join(d.reasons) + "."
        return base
