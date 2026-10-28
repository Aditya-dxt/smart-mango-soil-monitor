"""Irrigation policies: baselines and the learned DQN policy.

Every policy exposes ``propose(obs) -> action index`` into ``config.ACTIONS_MM``.
"""
from __future__ import annotations
import numpy as np
from . import config as C
from .env import Obs


class NoIrrigation:
    name = "No irrigation"
    def propose(self, obs: Obs) -> int: return 0


class FixedSchedule:
    """Calendar irrigation: 12 mm every 3 days all year, ignoring weather and soil."""
    name = "Fixed schedule"
    def __init__(self, every=3, idx=2): self.every, self.idx, self.k = every, idx, 0
    def propose(self, obs: Obs) -> int:
        self.k += 1
        return self.idx if self.k % self.every == 0 else 0


class ThresholdRule:
    """Irrigate to the stage band when below its lower bound (classic sensor rule)."""
    name = "Threshold rule"
    def propose(self, obs: Obs) -> int:
        lo, hi = C.TARGET_BAND[obs.stage]
        if obs.theta >= lo:
            return 0
        need = C.vwc_to_mm((lo + hi) / 2 - obs.theta)
        return int(np.argmin([abs(a - need) for a in C.ACTIONS_MM[1:]])) + 1


class DQNPolicy:
    name = "DQN"
    def __init__(self, agent): self.agent = agent
    def propose(self, obs: Obs) -> int:
        return self.agent.act(obs.vector(), eps=0.0)
    def q_values(self, obs: Obs): return self.agent.q_values(obs.vector())
