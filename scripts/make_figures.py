"""Generate all paper figures (PNG @ 800 DPI + vector PDF) from the results/ CSV files."""
import os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Patch
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mangoagent import config as C
from mangoagent.weather import generate_year

ROOT = os.path.join(os.path.dirname(__file__), "..")
RES = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "..", "figures")
os.makedirs(OUT, exist_ok=True)
DPI = 800

plt.rcParams.update({
    "font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 9,
    "axes.titlesize": 9.5, "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "legend.fontsize": 7.5, "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.8, "axes.grid": True, "grid.alpha": 0.25, "grid.linestyle": "--",
    "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
})

POL = ["No irrigation", "Fixed schedule", "Threshold rule", "DQN", "Agentic (DQN + guard)"]
POL_SHORT = ["No\nirrigation", "Fixed\nschedule", "Threshold\nrule", "DQN\nalone", "Agentic\n(DQN+guard)"]
PCOL = ["#8D99AE", "#EF476F", "#FFB703", "#118AB2", "#06D6A0"]
PEDGE = ["#5C677D", "#B5174A", "#C98A00", "#0B5E7A", "#039E75"]
STAGE_COL = ["#7B9CFF", "#FF7AA2", "#FFA94D", "#4CD07D", "#B28DFF"]


def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=DPI)
    fig.savefig(os.path.join(OUT, name + ".pdf"))
    plt.close(fig)
    print("saved", name)


# ---------------------------------------------------------------- 1. architecture diagram
def box(ax, x, y, w, h, title, lines, fc, ec, tc="white"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.025",
                                fc=fc, ec=ec, lw=1.4, zorder=2))
    ax.add_patch(FancyBboxPatch((x + 0.006, y - 0.012), w, h, boxstyle="round,pad=0.012,rounding_size=0.025",
                                fc="#00000018", ec="none", zorder=1))
    ax.text(x + w / 2, y + h - 0.045, title, ha="center", va="top", fontsize=9.5, weight="bold", color=tc, zorder=3)
    for i, ln in enumerate(lines):
        ax.text(x + w / 2, y + h - 0.105 - i * 0.052, ln, ha="center", va="top", fontsize=7.4, color=tc, zorder=3)


def arrow(ax, p, q, col="#334155", txt=None, off=(0, 0.025), rad=0.0, style="-|>", lw=1.6):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=11, lw=lw, color=col,
                                 connectionstyle=f"arc3,rad={rad}", zorder=4))
    if txt:
        ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], txt, ha="center", va="bottom",
                fontsize=6.9, color=col, style="italic", zorder=5,
                bbox=dict(fc="white", ec="none", alpha=0.85, pad=0.6))


def fig_architecture():
    fig, ax = plt.subplots(figsize=(7.16, 3.05))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off"); ax.grid(False)
    box(ax, 0.01, 0.50, 0.18, 0.44, "Field Node", ["ESP32 (ADC1)", "Capacitive soil probe", "DHT22 (T, RH)",
                                                     "Relay + 12 V solenoid", "Li-ion + solar"], "#FF6B6B", "#C92A2A")
    box(ax, 0.27, 0.62, 0.14, 0.32, "Transport", ["MQTT (Mosquitto)", "HTTP fallback", "JSON telemetry"],
        "#FFA94D", "#D9480F")
    box(ax, 0.49, 0.50, 0.18, 0.44, "Backend", ["FastAPI REST API", "Input validation", "SQLite storage",
                                                 "Scheduler", "Optional API key"], "#4D96FF", "#1C5FD4")
    box(ax, 0.76, 0.50, 0.23, 0.44, "Agent", ["Double-DQN planner", "Rule-based safety guard",
                                               "Advisories & alerts", "LLM explainer (optional)",
                                               "Decision memory"], "#9B5DE5", "#6A2CB8")
    box(ax, 0.49, 0.04, 0.18, 0.32, "Farmer Dashboard", ["Live moisture chart", "Decision log & alerts",
                                                          "Manual valve override"], "#06D6A0", "#05976F")
    box(ax, 0.76, 0.04, 0.23, 0.32, "Simulator", ["Soil-water balance", "IMD-calibrated weather",
                                                   "Training & offline tests"], "#F15BB5", "#B8277F")
    box(ax, 0.01, 0.04, 0.18, 0.32, "Orchard", ["Mango root zone", "500 mm soil layer", "Drip emitters"],
        "#8AC926", "#5A8A0F")
    arrow(ax, (0.195, 0.80), (0.265, 0.80))
    ax.text(0.23, 0.83, "data\n15 min", ha="center", va="bottom", fontsize=6.4, style="italic", color="#334155")
    arrow(ax, (0.415, 0.80), (0.485, 0.80))
    arrow(ax, (0.675, 0.80), (0.755, 0.80))
    ax.text(0.715, 0.83, "state", ha="center", va="bottom", fontsize=6.6, style="italic", color="#334155")
    arrow(ax, (0.755, 0.585), (0.675, 0.585), col="#6A2CB8")
    ax.text(0.715, 0.61, "decision", ha="center", va="bottom", fontsize=6.4, style="italic", color="#6A2CB8")
    arrow(ax, (0.485, 0.565), (0.195, 0.565), col="#6A2CB8")
    ax.text(0.34, 0.545, "valve command (minutes)", ha="center", va="top", fontsize=6.8, style="italic", color="#6A2CB8")
    arrow(ax, (0.58, 0.50), (0.58, 0.36), col="#05976F", style="<|-|>")
    ax.text(0.595, 0.43, "live data /\nmanual override", ha="left", va="center", fontsize=6.4, style="italic", color="#05976F")
    arrow(ax, (0.875, 0.36), (0.875, 0.50), col="#B8277F")
    ax.text(0.89, 0.43, "trained policy", ha="left", va="center", fontsize=6.4, style="italic", color="#B8277F")
    arrow(ax, (0.10, 0.50), (0.10, 0.36), col="#5A8A0F", style="<|-|>")
    ax.text(0.115, 0.43, "sense / irrigate", ha="left", va="center", fontsize=6.4, style="italic", color="#5A8A0F")
    ax.text(0.34, 0.20, "local fail-safe timer\ncloses valve when offline", fontsize=6.9, ha="center",
            color="#C92A2A", style="italic")
    save(fig, "fig1_architecture")


# ---------------------------------------------------------------- 2. agent loop
def fig_agent_loop():
    fig, ax = plt.subplots(figsize=(3.5, 3.3))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off"); ax.grid(False)
    steps = [("1  PERCEIVE", "24-h median VWC, T, RH, rain,\nforecast, growth stage", "#4D96FF"),
             ("2  REASON", "DQN scores 0 / 6 / 12 / 20 mm\nand proposes the best action", "#9B5DE5"),
             ("3  GUARD", "rain, band, stage, 7-day budget,\nsensor health, emergency", "#EF476F"),
             ("4  ACT", "mm $\\rightarrow$ valve minutes;\nMQTT / HTTP command", "#FFA62B"),
             ("5  REMEMBER", "log decision and reasons;\nplain-language note", "#06D6A0")]
    ys = [0.87, 0.68, 0.49, 0.30, 0.11]
    x0, w = 0.17, 0.62
    for (t, d, c), y in zip(steps, ys):
        ax.add_patch(FancyBboxPatch((x0, y - 0.07), w, 0.14, boxstyle="round,pad=0.01,rounding_size=0.03",
                                    fc=c, ec="white", lw=1.5))
        ax.text(x0 + 0.03, y + 0.03, t, fontsize=8.6, weight="bold", color="white", va="center")
        ax.text(x0 + 0.03, y - 0.03, d, fontsize=6.6, color="white", va="center", linespacing=1.05)
    for y1, y2 in zip(ys[:-1], ys[1:]):
        ax.add_patch(FancyArrowPatch((x0 + w / 2, y1 - 0.075), (x0 + w / 2, y2 + 0.075), arrowstyle="-|>",
                                     mutation_scale=10, lw=1.4, color="#334155"))
    ax.add_patch(FancyArrowPatch((x0 - 0.01, ys[-1]), (x0 - 0.01, ys[0]), arrowstyle="-|>", mutation_scale=11,
                                 lw=1.6, color="#334155", connectionstyle="arc3,rad=-0.2"))
    ax.text(0.03, 0.49, "next day", fontsize=7.4, ha="center", va="center", color="#334155", style="italic",
            rotation=90)
    ax.add_patch(FancyArrowPatch((x0 + w + 0.01, ys[2]), (x0 + w + 0.01, ys[1]), arrowstyle="-|>",
                                 mutation_scale=9, lw=1.2, color="#EF476F", linestyle="--",
                                 connectionstyle="arc3,rad=0.6"))
    ax.text(0.935, 0.585, "veto /\nclip", fontsize=6.9, color="#EF476F", ha="center", va="center", style="italic")
    save(fig, "fig2_agent_loop")


# ---------------------------------------------------------------- 3. climate + stage bands
def fig_climate_bands():
    years = [generate_year(s) for s in range(1, 201)]
    et0 = np.array([[y["et0"][y["month"] == m].sum() for m in range(1, 13)] for y in years]).mean(0)
    rain_sim = np.array([[y["rain"][y["month"] == m].sum() for m in range(1, 13)] for y in years]).mean(0)
    kc = np.array([C.KC[C.MONTH_TO_STAGE[m]] for m in range(1, 13)])
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(3.5, 3.6), sharex=True, gridspec_kw=dict(height_ratios=[1.1, 1]))
    x = np.arange(1, 13)
    a1.bar(x - 0.2, C.IMD_RAIN_MM, 0.4, color="#4D96FF", ec="#1C5FD4", lw=0.5, label="IMD normal rainfall")
    a1.bar(x + 0.2, rain_sim, 0.4, color="#9BD0FF", ec="#4D96FF", lw=0.5, label="Generator (200 yr mean)")
    a1.plot(x, et0 * kc, "-o", color="#EF476F", ms=3.2, lw=1.6, label="Crop ET ($K_c\\,ET_0$)")
    a1.plot(x, et0, "--", color="#FFA62B", lw=1.3, label="$ET_0$ (Hargreaves)")
    a1.set_ylabel("mm / month")
    a1.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), frameon=False, ncol=2, fontsize=6.6,
               columnspacing=0.8, handlelength=1.6)
    a1.text(0.02, 0.95, "(a) Lucknow climate", transform=a1.transAxes, ha="left", va="top", fontsize=8.4,
            weight="bold")
    for m in range(1, 13):
        st = C.MONTH_TO_STAGE[m]
        lo, hi = C.BANDS[st]
        a2.add_patch(plt.Rectangle((m - 0.5, lo), 1, hi - lo, fc=STAGE_COL[st], ec="white", lw=0.8, alpha=0.9))
    a2.axhline(C.FC, color="#118AB2", lw=1.0, ls="--"); a2.text(12.45, C.FC + 0.5, "FC 32%", fontsize=6.5, ha="right", color="#118AB2")
    a2.axhline(C.WP, color="#B5174A", lw=1.0, ls="--"); a2.text(12.45, C.WP - 2.3, "WP 12%", fontsize=6.5, ha="right", color="#B5174A")
    a2.axhline(C.SAT, color="#5C677D", lw=1.0, ls=":"); a2.text(12.45, C.SAT - 2.3, "SAT 42%", fontsize=6.5, ha="right", color="#5C677D")
    a2.set_ylim(8, 50); a2.set_ylabel("Target VWC band (%)")
    a2.set_xticks(x); a2.set_xticklabels(list("JFMAMJJASOND"))
    a2.text(0.01, 0.97, "(b) Stage targets", transform=a2.transAxes, ha="left", va="top", fontsize=8.4,
            weight="bold")
    a2.legend(handles=[Patch(fc=c, label=l) for c, l in zip(STAGE_COL, C.STAGE_LABELS)], ncol=3, frameon=False,
              fontsize=6.4, loc="upper center", bbox_to_anchor=(0.5, -0.12), handlelength=1.2, columnspacing=0.8)
    fig.tight_layout(h_pad=0.6)
    save(fig, "fig3_climate_bands")


# ---------------------------------------------------------------- 4. training curve
def fig_training():
    tc = pd.read_csv(os.path.join(RES, "training_curve.csv"))
    fig, ax = plt.subplots(figsize=(3.5, 2.2))
    ax.plot(tc.episode, tc.ret, color="#9BD0FF", lw=0.6, alpha=0.9, label="Episode return")
    ma = tc.ret.rolling(10, min_periods=1).mean()
    ax.plot(tc.episode, ma, color="#118AB2", lw=1.6, label="10-episode moving average")
    ax2 = ax.twinx()
    ax2.plot(tc.episode, tc.epsilon, color="#EF476F", lw=1.2, ls="--", label="$\\epsilon$ (exploration)")
    ax2.set_ylabel("$\\epsilon$", color="#EF476F"); ax2.set_ylim(0, 1.05); ax2.grid(False)
    ax2.spines["right"].set_visible(True); ax2.tick_params(axis="y", colors="#EF476F")
    ax.set_xlabel("Training episode (one synthetic year)"); ax.set_ylabel("Return")
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="lower right", frameon=True, framealpha=0.9, fontsize=6.8)
    save(fig, "fig4_training_curve")


# ---------------------------------------------------------------- 5. policy comparison
def fig_policies():
    py = pd.read_csv(os.path.join(RES, "per_year_results.csv"))
    panels = [("in_band", "Days in target band (%)"), ("below", "Days below band (%)"),
              ("water", "Irrigation water (mm/yr)"), ("drainage", "Deep drainage (mm/yr)")]
    fig, axs = plt.subplots(1, 4, figsize=(7.16, 2.25))
    for ax, (m, t) in zip(axs, panels):
        means = [py[py.policy == p][m].mean() for p in POL]
        sds = [py[py.policy == p][m].std() for p in POL]
        x = np.arange(5)
        ax.bar(x, means, 0.72, yerr=sds, color=PCOL, ec=PEDGE, lw=0.8,
               error_kw=dict(ecolor="#1F2937", lw=0.9, capsize=2.5, capthick=0.9))
        for xi, p in zip(x, POL):
            v = py[py.policy == p][m].values
            ax.scatter(np.full(len(v), xi) + np.random.default_rng(0).uniform(-0.2, 0.2, len(v)), v,
                       s=1.6, color="#1F2937", alpha=0.35, zorder=3, lw=0)
        for xi, mu in zip(x, means):
            ax.text(xi, mu, f"{mu:.0f}" if mu >= 100 else f"{mu:.1f}", ha="center", va="bottom", fontsize=6.3,
                    weight="bold", color="#111827", xytext=(0, 2), textcoords="offset points") if False else None
        ax.set_title(t, fontsize=8.6)
        ax.set_xticks(x); ax.set_xticklabels(["A", "B", "C", "D", "E"], fontsize=7.5, weight="bold")
        ax.set_ylim(bottom=0)
    fig.legend(handles=[Patch(fc=c, ec=e, label=f"{k}: {p}") for k, c, e, p in zip("ABCDE", PCOL, PEDGE, POL)],
               ncol=5, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 0.98), fontsize=7.2,
               columnspacing=1.2, handlelength=1.3)
    fig.tight_layout(w_pad=0.8)
    save(fig, "fig5_policy_comparison")


# ---------------------------------------------------------------- 6. one-year trace
def fig_year():
    t = pd.read_csv(os.path.join(RES, "trace_agentic.csv"))
    th = pd.read_csv(os.path.join(RES, "trace_threshold.csv"))
    fig, ax = plt.subplots(figsize=(7.16, 2.55))
    d = t.day.values
    for st in range(5):
        msk = t.stage.values == st
        ax.fill_between(d, t.lo, t.hi, where=msk, step="mid", color=STAGE_COL[st], alpha=0.38, lw=0)
    ax.plot(d, th.vwc, color="#FFB703", lw=1.0, alpha=0.95, label="Soil VWC – threshold rule")
    ax.plot(d, t.vwc, color="#0B3C5D", lw=1.5, label="Soil VWC – agentic (DQN + guard)")
    ax.axhline(C.WP, color="#B5174A", lw=0.8, ls="--")
    ax.text(3, C.WP - 1.9, "wilting point", fontsize=6.5, color="#B5174A")
    ax.set_ylabel("VWC (%)"); ax.set_xlabel("Day of year"); ax.set_xlim(1, 365); ax.set_ylim(0, 44)
    ax2 = ax.twinx(); ax2.grid(False); ax2.spines["right"].set_visible(True)
    ax2.bar(d, t.rain, width=1.0, color="#4D96FF", alpha=0.55, label="Rain (mm)")
    ax2.bar(d, t.irr, width=1.0, color="#EF476F", alpha=0.95, label="Irrigation (mm)")
    ax2.set_ylim(140, 0); ax2.set_ylabel("Rain / irrigation (mm)")
    mids = [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349]
    ax.set_xticks(mids); ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
                                              "Oct", "Nov", "Dec"])
    h = [Line2D([], [], color="#0B3C5D", lw=1.5), Line2D([], [], color="#FFB703", lw=1.0),
         Patch(fc="#EF476F"), Patch(fc="#4D96FF", alpha=0.55)] + [Patch(fc=c, alpha=0.5) for c in STAGE_COL]
    l = ["Agentic VWC", "Threshold-rule VWC", "Irrigation", "Rain"] + [f"Band: {s}" for s in C.STAGE_LABELS]
    ax.legend(h, l, ncol=5, fontsize=6.4, frameon=True, framealpha=0.92, loc="lower center",
              bbox_to_anchor=(0.5, 1.0), columnspacing=0.9, handlelength=1.4)
    save(fig, "fig6_year_trace")


# ---------------------------------------------------------------- 7. sensor-fault stress test
def fig_faults():
    f = pd.read_csv(os.path.join(RES, "fault_test_per_year.csv"))
    faults = list(dict.fromkeys(f.fault))
    fig, axs = plt.subplots(1, 3, figsize=(7.16, 2.15))
    specs = [("water_window", "Water applied in fault window (mm)"),
             ("drain_window", "Drainage in fault window (mm)"),
             ("inband_window", "Days in band during window (%)")]
    for ax, (m, title) in zip(axs, specs):
        x = np.arange(len(faults))
        for k, (pol, col, ec) in enumerate([("DQN", "#118AB2", "#0B5E7A"), ("Agentic (DQN + guard)", "#06D6A0", "#039E75")]):
            mu = [f[(f.fault == fl) & (f.policy == pol)][m].mean() for fl in faults]
            sd = [f[(f.fault == fl) & (f.policy == pol)][m].std() for fl in faults]
            ax.bar(x + (k - 0.5) * 0.36, mu, 0.36, yerr=sd, color=col, ec=ec, lw=0.8,
                   error_kw=dict(lw=0.8, capsize=2), label="DQN alone" if k == 0 else "Agentic (DQN + guard)")
        ax.set_xticks(x); ax.set_xticklabels([fl.replace(" (", "\n(") for fl in faults], fontsize=6.4)
        ax.set_title(title, fontsize=8.4); ax.set_ylim(bottom=0)
    axs[0].legend(frameon=False, fontsize=6.6, loc="upper right")
    fig.tight_layout(w_pad=0.8)
    save(fig, "fig7_fault_test")


if __name__ == "__main__":
    fig_architecture(); fig_agent_loop(); fig_climate_bands(); fig_training()
    fig_policies(); fig_year(); fig_faults()
