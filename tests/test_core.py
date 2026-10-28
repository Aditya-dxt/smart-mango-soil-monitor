import numpy as np
from mangoagent import config as C
from mangoagent.env import OrchardEnv, STATE_DIM
from mangoagent.dqn import DQNAgent
from mangoagent.guard import SafetyGuard
from mangoagent.agent import OrchardAgent, crop_advisories, sensor_stuck
from mangoagent.policies import ThresholdRule, NoIrrigation
from mangoagent.weather import month_of


def test_month_boundaries():
    assert [month_of(d) for d in (1, 31, 32, 365)] == [1, 1, 2, 12]


def test_env_runs_full_year_and_bounds():
    env = OrchardEnv(seed=1); env.reset(); done = False; n = 0
    while not done:
        _, r, done, _ = env.step(0); n += 1
        assert C.WILTING_POINT - 2 <= env.theta <= C.SATURATION
    assert n == 365


def test_irrigation_raises_moisture():
    e1, e2 = OrchardEnv(seed=3), OrchardEnv(seed=3)
    e1.reset(); e2.reset(); e1.theta = e2.theta = 18.0
    e1.step(0); e2.step(3)
    assert e2.theta > e1.theta


def test_state_vector_dim():
    assert OrchardEnv(seed=0).reset().vector().shape == (STATE_DIM,)


def test_dqn_learns_simple_bandit():
    rng = np.random.default_rng(0)
    ag = DQNAgent(3, 2, seed=0, batch=16)
    s = np.array([1, 0, 0], np.float32)
    for _ in range(600):
        a = int(rng.integers(2))
        ag.remember(s, a, 1.0 if a == 1 else 0.0, s, True)
        ag.learn()
    assert ag.act(s) == 1


def test_guard_blocks_rain_and_wet_soil():
    g = SafetyGuard()
    r = g.review(12, theta=20, stage="flowering", rain_today=0, forecast_rain=10, mm_last_7d=0)
    assert r.mm == 0 and r.overridden
    r = g.review(12, theta=31, stage="flowering", rain_today=0, forecast_rain=0, mm_last_7d=0)
    assert r.mm == 0


def test_guard_sensor_fault_withholds():
    r = SafetyGuard().review(12, theta=None, stage="fruit_dev", rain_today=0, forecast_rain=0, mm_last_7d=0)
    assert r.mm == 0 and r.alerts
    r = SafetyGuard().review(12, theta=99, stage="fruit_dev", rain_today=0, forecast_rain=0, mm_last_7d=0)
    assert r.mm == 0


def test_guard_weekly_cap_and_emergency():
    g = SafetyGuard()
    r = g.review(20, theta=20, stage="fruit_dev", rain_today=0, forecast_rain=0, mm_last_7d=50)
    assert r.mm == 10
    r = g.review(0, theta=13, stage="fruit_dev", rain_today=0, forecast_rain=0, mm_last_7d=0)
    assert r.mm == 12 and any("Emergency" in a or "emergency" in a for a in r.alerts + r.reasons)


def test_pre_flowering_dryness_is_respected():
    r = SafetyGuard().review(12, theta=18, stage="pre_flowering", rain_today=0, forecast_rain=0, mm_last_7d=0)
    assert r.mm == 0


def test_agent_actuates_and_remembers():
    calls = []
    ag = OrchardAgent(ThresholdRule(), actuate=lambda z, m: calls.append((z, m)))
    d = ag.decide("z1", theta=20, temp=32, rh=50, rain_today=0, forecast_rain=0, et0=5,
                  days_since_irrigation=3, month=4)
    assert d.approved_mm > 0 and calls and calls[0][1] == d.minutes
    assert ag.mm_last_7d("z1") == d.approved_mm and len(ag.memory) == 1
    assert "Irrigating" in d.explanation


def test_agent_never_irrigates_with_no_policy_need():
    ag = OrchardAgent(NoIrrigation())
    d = ag.decide("z1", theta=27, temp=30, rh=50, rain_today=0, forecast_rain=0, et0=5,
                  days_since_irrigation=3, month=4)
    assert d.approved_mm == 0


def test_advisories_and_stuck_sensor():
    assert crop_advisories("flowering", 42, 40)
    assert crop_advisories("fruit_dev", 28, 90)
    assert sensor_stuck([20.0] * 24) and not sensor_stuck(list(np.arange(24.0)))


def test_explainer_failure_falls_back():
    def boom(d): raise RuntimeError("api down")
    ag = OrchardAgent(NoIrrigation(), explain=boom)
    d = ag.decide("z", theta=25, temp=30, rh=50, rain_today=0, forecast_rain=0, et0=4,
                  days_since_irrigation=1, month=4)
    assert d.explanation.startswith("Stage")
