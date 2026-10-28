"""Shared configuration: phenological stages, soil constants and irrigation actions.

All numbers are *defaults* for a sandy-loam orchard in the Indo-Gangetic plain
(e.g. Kanpur, Uttar Pradesh). They must be calibrated against local soil tests,
cultivar and extension-service advice before use on a real orchard.
"""
from __future__ import annotations

STAGES = ["pre_flowering", "flowering", "fruit_dev", "pre_harvest", "post_harvest"]

# Calendar month -> stage (northern-India mango cycle; edit for other regions).
MONTH_TO_STAGE = {
    10: "pre_flowering", 11: "pre_flowering", 12: "pre_flowering", 1: "pre_flowering",
    2: "flowering", 3: "flowering",
    4: "fruit_dev", 5: "fruit_dev",
    6: "pre_harvest",
    7: "post_harvest", 8: "post_harvest", 9: "post_harvest",
}

# Target volumetric water content (VWC, %) band per stage: (low, high).
# Pre-flowering is deliberately dry: mild water stress before flowering is a
# recognised practice, while flowering/fruit-set/fruit-growth need adequate moisture.
TARGET_BAND = {
    "pre_flowering": (12.0, 20.0),
    "flowering": (22.0, 30.0),
    "fruit_dev": (24.0, 32.0),
    "pre_harvest": (19.0, 26.0),
    "post_harvest": (22.0, 30.0),
}

# Crop coefficient per stage (FAO-style Kc, simplified).
KC = {"pre_flowering": 0.70, "flowering": 0.80, "fruit_dev": 1.00,
      "pre_harvest": 0.90, "post_harvest": 0.85}

# Soil hydraulic constants (sandy loam, VWC %).
WILTING_POINT = 12.0
FIELD_CAPACITY = 32.0
SATURATION = 42.0
ROOT_ZONE_MM = 500.0          # 1 mm of water changes VWC by 100/ROOT_ZONE_MM = 0.2 %

# Discrete irrigation actions (mm of water applied per event).
ACTIONS_MM = [0.0, 6.0, 12.0, 20.0]

# Drip application rate used to convert mm -> valve minutes.
APPLICATION_RATE_MM_PER_H = 4.0


def stage_for_month(month: int) -> str:
    return MONTH_TO_STAGE[int(month)]


def mm_to_vwc(mm: float) -> float:
    return mm * 100.0 / ROOT_ZONE_MM


def vwc_to_mm(vwc: float) -> float:
    return vwc * ROOT_ZONE_MM / 100.0


def mm_to_minutes(mm: float) -> int:
    return int(round(60.0 * mm / APPLICATION_RATE_MM_PER_H))
