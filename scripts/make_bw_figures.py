"""Black-and-white versions of the evaluation figures (for print/monochrome documents)."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mangoagent.env import OrchardEnv, STATE_DIM
from mangoagent.dqn import DQNAgent
from mangoagent.policies import NoIrrigation, FixedSchedule, ThresholdRule, DQNPolicy
from mangoagent.guard import SafetyGuard
from mangoagent import config as C

OUT = Path("results")


class GuardedDQN:
    """DQN proposal reviewed by the deterministic safety guard (the deployed 'agentic' policy)."""
    name = "Agentic (DQN + guard)"
    def __init__(self, dqn):
        self.dqn, self.guard, self.hist = dqn, SafetyGuard(), []
    def reset(self): self.hist = []
    def propose(self, obs):
        a = self.dqn.propose(obs)
        g = self.guard.review(C.ACTIONS_MM[a], theta=obs.theta, stage=obs.stage,
                              rain_today=obs.rain_today, forecast_rain=obs.forecast_rain,
                              mm_last_7d=sum(self.hist[-7:]))
        idx = int(np.argmin([abs(x - g.mm) for x in C.ACTIONS_MM]))
        self.hist.append(C.ACTIONS_MM[idx])
        return idx


def run(policy, seeds):
    rows = []
    for s in seeds:
        env = OrchardEnv(seed=s)
        obs = env.reset()
        if hasattr(policy, "reset"): policy.reset()
        done, total = False, 0.0
        traj = []
        while not done:
            a = policy.propose(obs)
            traj.append((obs.theta, C.ACTIONS_MM[a], obs.rain_today))
            obs, r, done, _ = env.step(a)
            total += r
        L = env.log
        rows.append(dict(ret=total, water=L["water"], in_band=100 * L["in_band"] / 365,
                         stress=100 * L["stress"] / 365, wet=100 * L["wet"] / 365,
                         drain=L["drain"], events=L["events"]))
    return rows, traj


def main():
    dqn = DQNAgent(STATE_DIM, len(C.ACTIONS_MM))
    dqn.load(OUT / "dqn_weights.npz")
    policies = [NoIrrigation(), FixedSchedule(), ThresholdRule(), DQNPolicy(dqn), GuardedDQN(DQNPolicy(dqn))]
    seeds = list(range(5000, 5030))
    summary, trajs = {}, {}
    for p in policies:
        rows, traj = run(p, seeds)
        trajs[p.name] = traj
        summary[p.name] = {k: [float(np.mean([r[k] for r in rows])), float(np.std([r[k] for r in rows]))]
                           for k in rows[0]}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    with open(OUT / "summary.csv", "w") as f:
        f.write("policy,in_band_pct,stress_pct,wet_pct,water_mm,drainage_mm,events,return\n")
        for n, m in summary.items():
            f.write(f"{n},{m['in_band'][0]:.1f},{m['stress'][0]:.1f},{m['wet'][0]:.1f},"
                    f"{m['water'][0]:.0f},{m['drain'][0]:.0f},{m['events'][0]:.0f},{m['ret'][0]:.1f}\n")
    print(f"{'policy':26s} in-band% stress% wet%  water  drain  events")
    for n, m in summary.items():
        print(f"{n:26s} {m['in_band'][0]:7.1f} {m['stress'][0]:7.1f} {m['wet'][0]:5.1f} "
              f"{m['water'][0]:6.0f} {m['drain'][0]:6.0f} {m['events'][0]:6.0f}")

    names = list(summary)
    fig, ax = plt.subplots(1, 3, figsize=(14, 4))
    for a, key, title in zip(ax, ["in_band", "water", "drain"],
                             ["Days inside target band (%)", "Irrigation water (mm/yr)", "Deep drainage loss (mm/yr)"]):
        a.bar(range(len(names)), [summary[n][key][0] for n in names],
              yerr=[summary[n][key][1] for n in names], color="#555555", capsize=3)
        a.set_xticks(range(len(names))); a.set_xticklabels([n.replace(" (", "\n(") for n in names], fontsize=7, rotation=20)
        a.set_title(title, fontsize=10)
    plt.tight_layout(); plt.savefig(OUT / "bw_policy_comparison.png", dpi=140); plt.close()

    # one-year trajectory for the agentic policy
    tr = np.array(trajs["Agentic (DQN + guard)"])
    th = tr[:, 0]
    days = np.arange(len(th))
    stage_by_day = [C.stage_for_month(__import__("mangoagent.weather", fromlist=["month_of"]).month_of(d + 1)) for d in days]
    lo = np.array([C.TARGET_BAND[s][0] for s in stage_by_day]); hi = np.array([C.TARGET_BAND[s][1] for s in stage_by_day])
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.fill_between(days, lo, hi, color="#d0d0d0", alpha=0.6, label="Target band")
    ax.plot(days, th, color="#000000", lw=1.2, label="Soil VWC (%)")
    ax.bar(days, tr[:, 1], color="#333333", label="Irrigation (mm)")
    ax.bar(days, tr[:, 2], bottom=0, color="#999999", alpha=0.5, label="Rain (mm)")
    ax.set_xlabel("Day of year"); ax.set_ylabel("VWC % / mm"); ax.legend(ncol=4, fontsize=8)
    ax.set_title("Agentic policy - one simulated year (last evaluation seed)")
    plt.tight_layout(); plt.savefig(OUT / "bw_agentic_year.png", dpi=140); plt.close()

    ret = np.load(OUT / "training_returns.npy")
    k = 10
    sm = np.convolve(ret, np.ones(k) / k, mode="valid")
    plt.figure(figsize=(7, 3.5)); plt.plot(sm, color="#555555")
    plt.xlabel("Episode"); plt.ylabel("Return (10-ep avg)"); plt.title("DQN training curve")
    plt.tight_layout(); plt.savefig(OUT / "bw_training_curve.png", dpi=140); plt.close()


if __name__ == "__main__":
    main()
