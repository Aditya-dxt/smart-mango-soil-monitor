"""Tests for the 7-column synthetic soil dataset integrity and ML model validation."""
import csv
from pathlib import Path
from mangoagent.env import Obs, STATE_DIM
from mangoagent.dqn import DQNAgent
from mangoagent import config as C
from mangoagent.feasibility import evaluate_mango_feasibility

DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "synthetic_soil_dataset_5000.csv"
EXPECTED_COLUMNS = [
    "Nitrogen",
    "Phosphorous",
    "Potassium",
    "Soil moisture",
    "Ph",
    "Soil temprature",
    "Soil humidity"
]


def test_synthetic_dataset_exists_and_row_count():
    assert DATASET_PATH.exists(), f"Missing dataset file at {DATASET_PATH}"
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    assert len(reader) == 5000, f"Expected exactly 5000 rows, found {len(reader)}"


def test_synthetic_dataset_exact_7_columns():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
    assert header == EXPECTED_COLUMNS, f"Header mismatch. Expected {EXPECTED_COLUMNS}, got {header}"


def test_synthetic_dataset_value_ranges():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    for row in reader[:300]:
        n = float(row["Nitrogen"])
        p = float(row["Phosphorous"])
        k = float(row["Potassium"])
        sm = float(row["Soil moisture"])
        ph = float(row["Ph"])
        st = float(row["Soil temprature"])
        sh = float(row["Soil humidity"])

        assert 40.0 <= n <= 350.0, f"Invalid Nitrogen: {n}"
        assert 5.0 <= p <= 90.0, f"Invalid Phosphorous: {p}"
        assert 50.0 <= k <= 400.0, f"Invalid Potassium: {k}"
        assert 5.0 <= sm <= 50.0, f"Invalid Soil moisture: {sm}"
        assert 4.0 <= ph <= 9.5, f"Invalid pH: {ph}"
        assert 10.0 <= st <= 45.0, f"Invalid Soil temperature: {st}"
        assert 15.0 <= sh <= 100.0, f"Invalid Soil humidity: {sh}"


def test_ml_dqn_inference_on_dataset_records():
    agent = DQNAgent(STATE_DIM, len(C.ACTIONS_MM), seed=42)
    weights = Path(__file__).resolve().parents[1] / "results" / "dqn_weights.npz"
    if weights.exists():
        agent.load(weights)

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    for row in reader[:50]:
        obs = Obs(
            theta=float(row["Soil moisture"]),
            stage="fruit_dev",
            temp=float(row["Soil temprature"]),
            rh=float(row["Soil humidity"]),
            rain_today=0.0,
            forecast_rain=0.0,
            et0=4.5,
            days_since_irrigation=2
        )
        s_vec = obs.vector()
        q_vals = agent.q_values(s_vec)
        assert len(q_vals) == 4
        act = agent.act(s_vec)
        assert act in [0, 1, 2, 3]


def test_feasibility_engine_on_dataset_records():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    for row in reader[:50]:
        res = evaluate_mango_feasibility(
            soil_type="Alluvial Loam",
            ph=float(row["Ph"]),
            nitrogen=float(row["Nitrogen"]),
            phosphorus=float(row["Phosphorous"]),
            potassium=float(row["Potassium"]),
            moisture=float(row["Soil moisture"]),
            air_temp=float(row["Soil temprature"]),
            humidity=float(row["Soil humidity"])
        )
        assert res["top_pick"]
        assert 0.0 <= res["recommendations"][0]["score"] <= 100.0
