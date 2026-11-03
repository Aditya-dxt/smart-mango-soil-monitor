"""Tests for synthetic orchard dataset integrity and ML model validation."""
import csv
from pathlib import Path
import pytest
from mangoagent.env import Obs, STATE_DIM
from mangoagent.dqn import DQNAgent
from mangoagent import config as C
from mangoagent.feasibility import evaluate_mango_feasibility


DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "synthetic_orchard_dataset_5000.csv"


def test_synthetic_dataset_exists_and_row_count():
    assert DATASET_PATH.exists(), f"Missing dataset file at {DATASET_PATH}"
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    assert len(reader) >= 5000, f"Expected at least 5000 rows, found {len(reader)}"


def test_synthetic_dataset_schema_and_value_ranges():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    required_columns = [
        "record_id", "timestamp", "zone", "phenological_stage", "soil_type",
        "soil_moisture_vwc", "soil_temp_c", "air_temp_c", "humidity_rh",
        "rain_today_mm", "rain_forecast_mm", "et0_mm",
        "nitrogen_mg_kg", "phosphorus_mg_kg", "potassium_mg_kg", "soil_ph",
        "dqn_proposed_action_mm", "guard_approved_action_mm",
        "top_recommended_variety", "variety_feasibility_score"
    ]

    # Verify column presence
    first_row = reader[0]
    for col in required_columns:
        assert col in first_row, f"Missing column {col} in dataset"

    # Test random sampling of rows for valid physical ranges
    for row in reader[:200]:
        sm = float(row["soil_moisture_vwc"])
        assert 5.0 <= sm <= 50.0, f"Implausible soil moisture: {sm}"

        ph = float(row["soil_ph"])
        assert 4.0 <= ph <= 9.5, f"Implausible pH: {ph}"

        rh = float(row["humidity_rh"])
        assert 0.0 <= rh <= 100.0, f"Implausible humidity: {rh}"

        score = float(row["variety_feasibility_score"])
        assert 0.0 <= score <= 100.0, f"Feasibility score out of bounds: {score}"

        assert float(row["dqn_proposed_action_mm"]) in C.ACTIONS_MM
        assert float(row["guard_approved_action_mm"]) in [0.0, 6.0, 12.0, 20.0]


def test_ml_dqn_inference_on_dataset_batch():
    agent = DQNAgent(STATE_DIM, len(C.ACTIONS_MM), seed=42)
    weights = Path(__file__).resolve().parents[1] / "results" / "dqn_weights.npz"
    if weights.exists():
        agent.load(weights)

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    # Test inference on 50 sampled rows
    for row in reader[:50]:
        obs = Obs(
            theta=float(row["soil_moisture_vwc"]),
            stage=row["phenological_stage"],
            temp=float(row["air_temp_c"]),
            rh=float(row["humidity_rh"]),
            rain_today=float(row["rain_today_mm"]),
            forecast_rain=float(row["rain_forecast_mm"]),
            et0=float(row["et0_mm"]),
            days_since_irrigation=int(row["days_since_irrigation"])
        )
        s_vec = obs.vector()
        q_vals = agent.q_values(s_vec)
        assert len(q_vals) == len(C.ACTIONS_MM)
        act = agent.act(s_vec)
        assert act in [0, 1, 2, 3]


def test_feasibility_model_on_dataset_sample():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    for row in reader[:30]:
        res = evaluate_mango_feasibility(
            soil_type=row["soil_type"],
            ph=float(row["soil_ph"]),
            nitrogen=float(row["nitrogen_mg_kg"]),
            phosphorus=float(row["phosphorus_mg_kg"]),
            potassium=float(row["potassium_mg_kg"]),
            moisture=float(row["soil_moisture_vwc"]),
            air_temp=float(row["air_temp_c"]),
            humidity=float(row["humidity_rh"])
        )
        assert res["top_pick"]
        assert len(res["recommendations"]) >= 5
        assert 0.0 <= res["recommendations"][0]["score"] <= 100.0
