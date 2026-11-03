"""Generate a realistic 5,000-record synthetic dataset for Bhoomi-IQ ML models.

Features included per record:
1. Soil Chemistry & Texture: N, P, K, pH, Soil Type, Moisture (VWC %), Soil Temp
2. Meteorology (IMD Lucknow calibrated): Air Temp, Humidity, Rain Today, Rain Forecast, ET0
3. Crop Phenology: Month, Day, Phenological Stage, Target Moisture Band (lo, hi)
4. ML Inference Ground Truth:
   - Double-DQN Q-values (Q0, Q6, Q12, Q20)
   - DQN Proposed Irrigation Action (mm)
   - Safety Guard Approved Action (mm) & Valve Duration (min)
   - Guard Reason / Intervention Status
   - Top Recommended Mango Variety
   - Variety Feasibility Score (0-100) & Feasibility Status
"""
import os, sys, csv
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mangoagent import config as C
from mangoagent.env import Obs, STATE_DIM
from mangoagent.dqn import DQNAgent
from mangoagent.guard import SafetyGuard
from mangoagent.feasibility import evaluate_mango_feasibility, VARIETY_DATABASE


SOIL_TYPES = [
    "Alluvial Loam",
    "Laterite Soil",
    "Red Sandy Loam",
    "Medium Black Soil",
    "Clayey Loam"
]

ZONES = ["zone1", "zone2", "zone3", "zone4"]


def generate_dataset(num_records: int = 5000, seed: int = 42, output_path: str = "data/synthetic_orchard_dataset_5000.csv"):
    rng = np.random.default_rng(seed)

    # 1. Load trained DQN model
    dqn = DQNAgent(STATE_DIM, len(C.ACTIONS_MM), seed=seed)
    weights_path = ROOT / "results" / "dqn_weights.npz"
    if weights_path.exists():
        dqn.load(weights_path)
    guard = SafetyGuard()

    records = []
    base_date = datetime(2025, 1, 1, 8, 0, 0)

    print(f"Generating {num_records} synthetic records using seed={seed}...")

    # We will simulate consecutive daily & multi-zone seasonal readings
    current_moistures = {z: float(rng.uniform(16.0, 22.0)) for z in ZONES}
    recent_irrigations = {z: [0.0] * 7 for z in ZONES}
    days_since_irr = {z: 3 for z in ZONES}

    for i in range(num_records):
        day_offset = i // len(ZONES)
        zone = ZONES[i % len(ZONES)]
        node_id = f"node_{zone}"
        dt = base_date + timedelta(days=day_offset, hours=2 * (i % len(ZONES)))
        month = dt.month
        stage = C.stage_for_month(month)
        lo_band, hi_band = C.TARGET_BAND[stage]

        # Soil type (correlated with zone / regional distribution)
        soil_type = SOIL_TYPES[(i % len(SOIL_TYPES))]

        # Weather simulation calibrated by season
        if month in [12, 1, 2]: # Winter / Pre-flowering & flowering
            air_temp = float(rng.normal(21.0, 3.5))
            humidity = float(rng.normal(55.0, 8.0))
            rain_prob = 0.08
            et0 = float(rng.normal(2.6, 0.4))
        elif month in [3, 4, 5]: # Summer / Fruit development
            air_temp = float(rng.normal(36.0, 4.0))
            humidity = float(rng.normal(42.0, 10.0))
            rain_prob = 0.12
            et0 = float(rng.normal(5.8, 0.8))
        elif month in [6, 7, 8, 9]: # Monsoon / Post-harvest & pre-harvest
            air_temp = float(rng.normal(32.0, 2.8))
            humidity = float(rng.normal(78.0, 8.0))
            rain_prob = 0.45
            et0 = float(rng.normal(4.2, 0.6))
        else: # Autumn (Oct, Nov)
            air_temp = float(rng.normal(27.0, 3.0))
            humidity = float(rng.normal(60.0, 7.0))
            rain_prob = 0.15
            et0 = float(rng.normal(3.5, 0.5))

        air_temp = round(max(8.0, min(47.0, air_temp)), 1)
        humidity = round(max(15.0, min(98.0, humidity)), 1)
        et0 = round(max(1.0, min(9.0, et0)), 2)

        is_raining = rng.random() < rain_prob
        rain_today = round(float(rng.exponential(14.0)), 1) if is_raining else 0.0
        forecast_rain = round(float(rng.exponential(12.0)), 1) if rng.random() < (rain_prob * 1.1) else 0.0

        # Soil temperature (ambient lag)
        soil_temp = round(air_temp - float(rng.uniform(1.2, 3.5)), 1)

        # Dynamic Soil Moisture simulation
        theta = current_moistures[zone]
        # Natural drying through evapotranspiration Kc * ET0
        kc = C.KC[stage]
        daily_loss_mm = kc * et0
        daily_loss_vwc = C.mm_to_vwc(daily_loss_mm)
        rain_gain_vwc = C.mm_to_vwc(rain_today * 0.75)

        theta = theta - daily_loss_vwc + rain_gain_vwc + float(rng.normal(0, 0.2))
        theta = round(max(C.WILTING_POINT - 2.0, min(C.SATURATION, theta)), 1)

        # Soil chemistry NPK & pH (typical natural variations with soil type affinity)
        if soil_type == "Laterite Soil":
            ph = round(float(rng.normal(6.1, 0.35)), 2)
            nitrogen = round(float(rng.normal(135, 18)), 1)
            phosphorus = round(float(rng.normal(24, 6)), 1)
            potassium = round(float(rng.normal(205, 25)), 1)
        elif soil_type == "Medium Black Soil":
            ph = round(float(rng.normal(7.4, 0.35)), 2)
            nitrogen = round(float(rng.normal(160, 20)), 1)
            phosphorus = round(float(rng.normal(27, 7)), 1)
            potassium = round(float(rng.normal(220, 28)), 1)
        elif soil_type == "Alluvial Loam":
            ph = round(float(rng.normal(6.7, 0.3)), 2)
            nitrogen = round(float(rng.normal(155, 22)), 1)
            phosphorus = round(float(rng.normal(32, 8)), 1)
            potassium = round(float(rng.normal(195, 22)), 1)
        elif soil_type == "Red Sandy Loam":
            ph = round(float(rng.normal(6.4, 0.4)), 2)
            nitrogen = round(float(rng.normal(130, 20)), 1)
            phosphorus = round(float(rng.normal(26, 6)), 1)
            potassium = round(float(rng.normal(180, 25)), 1)
        else: # Clayey Loam
            ph = round(float(rng.normal(7.0, 0.4)), 2)
            nitrogen = round(float(rng.normal(170, 25)), 1)
            phosphorus = round(float(rng.normal(29, 7)), 1)
            potassium = round(float(rng.normal(210, 30)), 1)

        ph = max(4.8, min(8.6, ph))
        nitrogen = max(40.0, min(320.0, nitrogen))
        phosphorus = max(8.0, min(75.0, phosphorus))
        potassium = max(60.0, min(360.0, potassium))

        # 2. ML DQN Agent Inference
        obs = Obs(
            theta=theta,
            stage=stage,
            temp=air_temp,
            rh=humidity,
            rain_today=rain_today,
            forecast_rain=forecast_rain,
            et0=et0,
            days_since_irrigation=days_since_irr[zone]
        )
        s_vec = obs.vector()
        q_vals = dqn.q_values(s_vec)
        dqn_act_idx = int(np.argmax(q_vals))
        dqn_action_mm = float(C.ACTIONS_MM[dqn_act_idx])

        # 3. Deterministic Safety Guard Review
        mm_7d = sum(recent_irrigations[zone])
        review = guard.review(
            proposed_mm=dqn_action_mm,
            theta=theta,
            stage=stage,
            rain_today=rain_today,
            forecast_rain=forecast_rain,
            mm_last_7d=mm_7d
        )
        approved_mm = float(review.mm)
        guard_reason = "; ".join(review.reasons) if review.reasons else "Proposal approved"
        is_override = (approved_mm != dqn_action_mm)
        valve_mins = C.mm_to_minutes(approved_mm)

        # Update environment state for next step
        if approved_mm > 0:
            theta += C.mm_to_vwc(approved_mm)
            days_since_irr[zone] = 0
        else:
            days_since_irr[zone] = min(15, days_since_irr[zone] + 1)

        current_moistures[zone] = round(theta, 1)
        recent_irrigations[zone].pop(0)
        recent_irrigations[zone].append(approved_mm)

        # 4. Cultivar Feasibility ML Engine
        feas_res = evaluate_mango_feasibility(
            soil_type=soil_type,
            ph=ph,
            nitrogen=nitrogen,
            phosphorus=phosphorus,
            potassium=potassium,
            moisture=theta,
            air_temp=air_temp,
            humidity=humidity
        )
        top_variety = feas_res["top_pick"]
        top_rec = feas_res["recommendations"][0]
        top_score = top_rec["score"]
        top_status = top_rec["status"]
        soil_note = feas_res["soil_health_notes"][0] if feas_res["soil_health_notes"] else "Soil parameters balanced"

        record = {
            "record_id": i + 1,
            "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "node_id": node_id,
            "zone": zone,
            "month": month,
            "phenological_stage": stage,
            "soil_type": soil_type,
            "soil_moisture_vwc": theta,
            "target_moisture_min": lo_band,
            "target_moisture_max": hi_band,
            "soil_temp_c": soil_temp,
            "air_temp_c": air_temp,
            "humidity_rh": humidity,
            "rain_today_mm": rain_today,
            "rain_forecast_mm": forecast_rain,
            "et0_mm": et0,
            "days_since_irrigation": days_since_irr[zone],
            "nitrogen_mg_kg": nitrogen,
            "phosphorus_mg_kg": phosphorus,
            "potassium_mg_kg": potassium,
            "soil_ph": ph,
            "dqn_q0_val": round(float(q_vals[0]), 3),
            "dqn_q6_val": round(float(q_vals[1]), 3),
            "dqn_q12_val": round(float(q_vals[2]), 3),
            "dqn_q20_val": round(float(q_vals[3]), 3),
            "dqn_proposed_action_mm": dqn_action_mm,
            "guard_approved_action_mm": approved_mm,
            "valve_duration_mins": valve_mins,
            "guard_overridden": is_override,
            "guard_reason": guard_reason,
            "top_recommended_variety": top_variety,
            "variety_feasibility_score": top_score,
            "variety_feasibility_status": top_status,
            "soil_diagnostic_note": soil_note
        }
        records.append(record)

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

    print(f"Successfully generated {len(records)} records saved to {out_file} ({out_file.stat().st_size / 1024:.1f} KB).")
    return records


if __name__ == "__main__":
    generate_dataset(5000, seed=42)
