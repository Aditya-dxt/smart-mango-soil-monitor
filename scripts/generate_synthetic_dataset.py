"""Generate 5,000 synthetic records with exact soil & environmental columns:
- Nitrogen
- Phosphorous
- Potassium
- Soil moisture
- Ph
- Soil temprature
- Soil humidity
"""
import csv
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

COLUMNS = [
    "Nitrogen",
    "Phosphorous",
    "Potassium",
    "Soil moisture",
    "Ph",
    "Soil temprature",
    "Soil humidity"
]


def generate_soil_dataset(num_records: int = 5000, seed: int = 42, filename: str = "synthetic_soil_dataset_5000.csv"):
    rng = np.random.default_rng(seed)
    records = []

    for _ in range(num_records):
        n = round(float(np.clip(rng.normal(148.0, 32.0), 50.0, 290.0)), 1)
        p = round(float(np.clip(rng.normal(28.5, 9.0), 8.0, 70.0)), 1)
        k = round(float(np.clip(rng.normal(192.0, 42.0), 75.0, 360.0)), 1)
        sm = round(float(np.clip(rng.normal(19.2, 4.2), 9.0, 38.0)), 1)
        ph = round(float(np.clip(rng.normal(6.65, 0.48), 5.0, 8.5)), 2)
        st = round(float(np.clip(rng.normal(26.2, 5.2), 14.0, 39.0)), 1)
        sh = round(float(np.clip(rng.normal(60.5, 13.5), 22.0, 95.0)), 1)

        records.append({
            "Nitrogen": n,
            "Phosphorous": p,
            "Potassium": k,
            "Soil moisture": sm,
            "Ph": ph,
            "Soil temprature": st,
            "Soil humidity": sh
        })

    out_path = DATA_DIR / filename
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(records)

    print(f"Generated {len(records)} records with exact columns: {COLUMNS}")
    print(f"Saved to {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")
    return out_path


if __name__ == "__main__":
    generate_soil_dataset(5000)
