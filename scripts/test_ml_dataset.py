"""Test and benchmark the 5,000-record synthetic orchard dataset on Bhoomi-IQ ML models.

Tests evaluated:
1. Double-DQN Inference:
   - State vector reconstruction & forward-pass verification
   - Q-value distribution, max Q-value bounds, action selection frequency
   - Latency benchmark (in microsecond/sample and throughput in samples/sec)
2. Safety Guard Intervention:
   - Review logic testing against rain, moisture saturation, and stage rules
   - Override percentage and reason distribution
3. Mango Variety Feasibility Engine:
   - Consistency check of feasibility ranking against soil types
   - Distribution of top recommended cultivars
   - Score statistics across all 5,000 records
"""
from __future__ import annotations
import csv, json, time, sys
from pathlib import Path
import numpy as np

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mangoagent import config as C
from mangoagent.env import Obs, STATE_DIM
from mangoagent.dqn import DQNAgent
from mangoagent.guard import SafetyGuard
from mangoagent.feasibility import evaluate_mango_feasibility


def run_ml_benchmark(dataset_path: str = "data/synthetic_orchard_dataset_5000.csv"):
    csv_file = Path(dataset_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"Dataset not found at {csv_file}")

    print("=" * 75)
    print(f"BHOOMI-IQ ML MODEL EVALUATION SUITE ON 5,000-RECORD DATASET")
    print(f"Dataset: {csv_file} ({csv_file.stat().st_size / 1024:.1f} KB)")
    print("=" * 75)

    # 1. Load dataset rows
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    num_samples = len(reader)
    print(f"\n[+] Loaded {num_samples} records successfully.")

    # 2. Initialize Models
    dqn = DQNAgent(STATE_DIM, len(C.ACTIONS_MM), seed=42)
    weights_path = ROOT / "results" / "dqn_weights.npz"
    if weights_path.exists():
        dqn.load(weights_path)
        print(f"[+] Loaded trained DQN weights from {weights_path}")
    else:
        print("[-] Notice: trained weights not found, using initialized weights.")

    guard = SafetyGuard()

    # 3. Double-DQN Inference Benchmark
    t0 = time.perf_counter()
    dqn_actions = []
    action_match_count = 0
    q_diffs = []
    all_max_q = []

    for row in reader:
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
        q_vals = dqn.q_values(s_vec)
        pred_act_idx = int(np.argmax(q_vals))
        pred_mm = C.ACTIONS_MM[pred_act_idx]
        dqn_actions.append(pred_mm)
        all_max_q.append(float(np.max(q_vals)))

        expected_q = [
            float(row["dqn_q0_val"]),
            float(row["dqn_q6_val"]),
            float(row["dqn_q12_val"]),
            float(row["dqn_q20_val"])
        ]
        diff = np.max(np.abs(q_vals - expected_q))
        q_diffs.append(diff)
        if abs(pred_mm - float(row["dqn_proposed_action_mm"])) < 1e-4:
            action_match_count += 1

    t_dqn_total = time.perf_counter() - t0
    dqn_throughput = num_samples / t_dqn_total
    dqn_latency_us = (t_dqn_total / num_samples) * 1e6

    # 4. Safety Guard Benchmark
    t0_g = time.perf_counter()
    guard_approved = []
    guard_overrides = 0
    guard_reasons = {}

    for row in reader:
        rev = guard.review(
            proposed_mm=float(row["dqn_proposed_action_mm"]),
            theta=float(row["soil_moisture_vwc"]),
            stage=row["phenological_stage"],
            rain_today=float(row["rain_today_mm"]),
            forecast_rain=float(row["rain_forecast_mm"]),
            mm_last_7d=float(row["days_since_irrigation"]) * 4.0 # approximate rolling history
        )
        guard_approved.append(rev.mm)
        if rev.overridden:
            guard_overrides += 1
            for r in rev.reasons:
                guard_reasons[r] = guard_reasons.get(r, 0) + 1

    t_guard_total = time.perf_counter() - t0_g

    # 5. Cultivar Feasibility ML Engine Benchmark
    t0_f = time.perf_counter()
    top_varieties = {}
    variety_match_count = 0
    score_diffs = []

    for row in reader:
        f_res = evaluate_mango_feasibility(
            soil_type=row["soil_type"],
            ph=float(row["soil_ph"]),
            nitrogen=float(row["nitrogen_mg_kg"]),
            phosphorus=float(row["phosphorus_mg_kg"]),
            potassium=float(row["potassium_mg_kg"]),
            moisture=float(row["soil_moisture_vwc"]),
            air_temp=float(row["air_temp_c"]),
            humidity=float(row["humidity_rh"])
        )
        top_name = f_res["top_pick"]
        top_varieties[top_name] = top_varieties.get(top_name, 0) + 1
        if top_name == row["top_recommended_variety"]:
            variety_match_count += 1
        score_diffs.append(abs(f_res["recommendations"][0]["score"] - float(row["variety_feasibility_score"])))

    t_feas_total = time.perf_counter() - t0_f

    # Compile Summary Results
    action_counts = {f"{mm}mm": dqn_actions.count(mm) for mm in C.ACTIONS_MM}
    action_pct = {k: f"{v / num_samples * 100:.1f}%" for k, v in action_counts.items()}

    summary = {
        "dataset_records": num_samples,
        "dqn_inference": {
            "action_match_rate_pct": round((action_match_count / num_samples) * 100, 2),
            "mean_q_error": round(float(np.mean(q_diffs)), 6),
            "max_q_error": round(float(np.max(q_diffs)), 6),
            "action_distribution": action_pct,
            "mean_max_q_value": round(float(np.mean(all_max_q)), 2),
            "throughput_samples_per_sec": round(dqn_throughput, 1),
            "latency_microseconds_per_sample": round(dqn_latency_us, 2)
        },
        "safety_guard": {
            "override_rate_pct": round((guard_overrides / num_samples) * 100, 2),
            "top_interventions": sorted(guard_reasons.items(), key=lambda x: x[1], reverse=True)
        },
        "cultivar_feasibility": {
            "variety_prediction_consistency_pct": round((variety_match_count / num_samples) * 100, 2),
            "mean_score_deviation": round(float(np.mean(score_diffs)), 4),
            "top_cultivar_distribution": sorted(top_varieties.items(), key=lambda x: x[1], reverse=True)
        }
    }

    # Print Formatted Report
    print("\n" + "-" * 75)
    print("1. DOUBLE-DQN REINFORCEMENT LEARNING INFERENCE PERFORMANCE")
    print("-" * 75)
    print(f"  • Model Match Rate           : {summary['dqn_inference']['action_match_rate_pct']}% (Exact Reproducibility)")
    print(f"  • Mean Absolute Q-Error      : {summary['dqn_inference']['mean_q_error']:.6f}")
    print(f"  • Inference Throughput       : {summary['dqn_inference']['throughput_samples_per_sec']:,} samples/second")
    print(f"  • Latency per Sample         : {summary['dqn_inference']['latency_microseconds_per_sample']} µs")
    print(f"  • Action Distribution        : {action_pct}")

    print("\n" + "-" * 75)
    print("2. SAFETY GUARD POLICY ENFORCEMENT ON DATASET")
    print("-" * 75)
    print(f"  • Guard Override Rate        : {summary['safety_guard']['override_rate_pct']}% of records safely reviewed")
    print("  • Primary Guard Interventions:")
    for reason, count in summary['safety_guard']['top_interventions'][:4]:
        print(f"     - {reason:40s} : {count:4d} times ({count/num_samples*100:5.1f}%)")

    print("\n" + "-" * 75)
    print("3. MANGO CULTIVAR FEASIBILITY ENGINE DISTRIBUTION (5,000 RECORDS)")
    print("-" * 75)
    print(f"  • Variety Consistency Rate   : {summary['cultivar_feasibility']['variety_prediction_consistency_pct']}%")
    print("  • Most Feasible Varieties Across Diverse Soils:")
    for variety, count in summary['cultivar_feasibility']['top_cultivar_distribution']:
        print(f"     - {variety:35s} : {count:4d} times ({count/num_samples*100:5.1f}%)")
    print("=" * 75)

    # Save JSON Report
    report_file = ROOT / "results" / "ml_dataset_test_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[+] Saved detailed evaluation report to {report_file}")

    return summary


if __name__ == "__main__":
    run_ml_benchmark()
