"""Test and benchmark the 7-column synthetic soil dataset against Bhoomi-IQ ML models.

Columns:
- Nitrogen
- Phosphorous
- Potassium
- Soil moisture
- Ph
- Soil temprature
- Soil humidity
"""
from __future__ import annotations
import csv, json, time, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mangoagent import config as C
from mangoagent.env import Obs, STATE_DIM
from mangoagent.dqn import DQNAgent
from mangoagent.guard import SafetyGuard
from mangoagent.feasibility import evaluate_mango_feasibility


def run_benchmark(csv_path: str = "data/synthetic_soil_dataset_5000.csv"):
    file_path = Path(csv_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    print("=" * 75)
    print("BHOOMI-IQ ML EVALUATION: 7-PARAMETER SOIL SENSOR DATASET")
    print(f"Dataset: {file_path} ({file_path.stat().st_size / 1024:.1f} KB)")
    print("=" * 75)

    with open(file_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    num_samples = len(reader)
    print(f"[+] Loaded {num_samples} records.")
    print(f"[+] Columns present ({len(reader[0])}): {list(reader[0].keys())}")

    # 1. Double-DQN Model
    dqn = DQNAgent(STATE_DIM, len(C.ACTIONS_MM), seed=42)
    weights_path = ROOT / "results" / "dqn_weights.npz"
    if weights_path.exists():
        dqn.load(weights_path)
        print(f"[+] Loaded trained DQN weights from {weights_path}")
    guard = SafetyGuard()

    # 2. Benchmark DQN Inference & Guard Review
    t0 = time.perf_counter()
    dqn_actions = []
    guard_approved = []
    guard_overrides = 0
    guard_reasons = {}

    for row in reader:
        theta = float(row["Soil moisture"])
        temp = float(row["Soil temprature"])
        humidity = float(row["Soil humidity"])
        # Reconstruct observation
        obs = Obs(
            theta=theta,
            stage="flowering", # testing at active growth stage
            temp=temp,
            rh=humidity,
            rain_today=0.0,
            forecast_rain=0.0,
            et0=3.2,
            days_since_irrigation=3
        )
        s_vec = obs.vector()
        q_vals = dqn.q_values(s_vec)
        pred_act_idx = int(np.argmax(q_vals))
        pred_mm = C.ACTIONS_MM[pred_act_idx]
        dqn_actions.append(pred_mm)

        rev = guard.review(
            proposed_mm=pred_mm,
            theta=theta,
            stage="flowering",
            rain_today=0.0,
            forecast_rain=0.0,
            mm_last_7d=12.0
        )
        guard_approved.append(rev.mm)
        if rev.overridden:
            guard_overrides += 1
            for r in rev.reasons:
                guard_reasons[r] = guard_reasons.get(r, 0) + 1

    t_dqn_total = time.perf_counter() - t0
    throughput = num_samples / t_dqn_total
    latency_us = (t_dqn_total / num_samples) * 1e6

    # 3. Benchmark Cultivar Feasibility ML Engine
    t0_f = time.perf_counter()
    top_varieties = {}
    health_alerts = 0

    for row in reader:
        f_res = evaluate_mango_feasibility(
            soil_type="Alluvial Loam",
            ph=float(row["Ph"]),
            nitrogen=float(row["Nitrogen"]),
            phosphorus=float(row["Phosphorous"]),
            potassium=float(row["Potassium"]),
            moisture=float(row["Soil moisture"]),
            air_temp=float(row["Soil temprature"]),
            humidity=float(row["Soil humidity"])
        )
        top_name = f_res["top_pick"]
        top_varieties[top_name] = top_varieties.get(top_name, 0) + 1
        if any("toxicity" in n or "deficient" in n or "lockup" in n for n in f_res["soil_health_notes"]):
            health_alerts += 1

    t_feas_total = time.perf_counter() - t0_f

    action_counts = {f"{mm}mm": dqn_actions.count(mm) for mm in C.ACTIONS_MM}
    action_pct = {k: f"{v / num_samples * 100:.1f}%" for k, v in action_counts.items()}

    print("\n" + "-" * 75)
    print("1. DOUBLE-DQN REINFORCEMENT LEARNING INFERENCE ON SOIL DATASET")
    print("-" * 75)
    print(f"  • Throughput                : {throughput:,.1f} samples/second")
    print(f"  • Latency per Sample        : {latency_us:.2f} µs")
    print(f"  • Action Distribution       : {action_pct}")
    print(f"  • Guard Safety Overrides    : {guard_overrides / num_samples * 100:.1f}% of decisions reviewed")

    print("\n" + "-" * 75)
    print("2. MANGO CULTIVAR FEASIBILITY ENGINE RESULTS (5,000 RECORDS)")
    print("-" * 75)
    print(f"  • Soil Health Diagnostic Warnings : {health_alerts} records flagged with nutrient notes")
    print("  • Cultivar Recommendations Across 5,000 Soil Profiles:")
    for variety, count in sorted(top_varieties.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"     - {variety:35s} : {count:4d} times ({count/num_samples*100:5.1f}%)")
    print("=" * 75)

    summary = {
        "dataset_records": num_samples,
        "columns": list(reader[0].keys()),
        "dqn_throughput_samples_per_sec": round(throughput, 1),
        "dqn_latency_us": round(latency_us, 2),
        "dqn_action_distribution": action_pct,
        "guard_override_rate_pct": round(guard_overrides / num_samples * 100, 2),
        "cultivar_distribution": top_varieties
    }

    report_file = ROOT / "results" / "ml_dataset_test_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"[+] Benchmark report saved to {report_file}")
    return summary


if __name__ == "__main__":
    run_benchmark()
