"""Compare your results with the expected (published) results.

Usage (from the folder that contains this file):
    python verify_results.py path/to/your/results

It prints PASS or FAIL for every number used in the paper.
"""
import os, sys, csv

HERE = os.path.dirname(os.path.abspath(__file__))
EXPECTED = os.path.join(HERE, "expected_results")
yours = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results")

ok = True


def _read_csv_dict(filepath, is_multiheader=False, key_cols=0):
    with open(filepath, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    if not reader:
        return {}
    if is_multiheader:
        h1 = reader[0]
        h2 = reader[1]
        col_names = [f"{h1[i]}_{h2[i]}" if h1[i] else h2[i] for i in range(len(h2))]
        data_rows = reader[2:]
    else:
        col_names = reader[0]
        data_rows = reader[1:]

    records = {}
    for row in data_rows:
        if not row:
            continue
        if isinstance(key_cols, list):
            k = tuple(row[i].strip() for i in key_cols)
        else:
            k = row[key_cols].strip()
        vals = {}
        for idx, val in enumerate(row):
            if isinstance(key_cols, list) and idx in key_cols:
                continue
            if isinstance(key_cols, int) and idx == key_cols:
                continue
            col_id = col_names[idx] if idx < len(col_names) else str(idx)
            try:
                vals[col_id] = float(val)
            except ValueError:
                vals[col_id] = val
        records[k] = vals
    return records


def compare(name, key_cols, tol):
    global ok
    exp_path = os.path.join(EXPECTED, name)
    your_path = os.path.join(yours, name)
    if not os.path.exists(your_path):
        print(f"FAIL  {name}: file not found in {yours}")
        ok = False
        return

    is_multi = (name == "summary_results.csv")
    e_data = _read_csv_dict(exp_path, is_multiheader=is_multi, key_cols=key_cols)
    y_data = _read_csv_dict(your_path, is_multiheader=is_multi, key_cols=key_cols)

    file_ok = True
    for k, cols in e_data.items():
        if k not in y_data:
            print(f"FAIL  {name}: missing key {k} in results")
            file_ok = False
            continue
        for col_name, ev in cols.items():
            if not isinstance(ev, (int, float)):
                continue
            if col_name not in y_data[k]:
                print(f"FAIL  {name} {k} {col_name}: missing in your results")
                file_ok = False
                continue
            yv = y_data[k][col_name]
            good = abs(ev - yv) <= tol * max(1.0, abs(ev))
            if not good:
                print(f"FAIL  {name} {k} {col_name}: expected {ev:.2f}, got {yv:.2f}")
                file_ok = False

    ok &= file_ok
    print(f"{'PASS' if file_ok else 'CHECK'}  {name}")


compare("summary_results.csv", 0, 0.01)
compare("fault_test_summary.csv", [0, 1], 0.01)
print("\nALL RESULTS MATCH THE PAPER" if ok else "\nSome numbers differ - see FAIL lines above")
