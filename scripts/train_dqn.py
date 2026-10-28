"""Train the DQN irrigation policy in the orchard simulator.

Usage: python scripts/train_dqn.py [--episodes 150] [--seed 0]
"""
import argparse, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mangoagent.env import OrchardEnv, STATE_DIM
from mangoagent.dqn import DQNAgent
from mangoagent import config as C


def train(episodes=150, seed=0, out="results/dqn_weights.npz", verbose=True):
    agent = DQNAgent(STATE_DIM, len(C.ACTIONS_MM), seed=seed)
    returns = []
    t0 = time.time()
    for ep in range(episodes):
        env = OrchardEnv(seed=1000 + ep)
        obs = env.reset()
        eps = max(0.05, 1.0 - ep / (0.6 * episodes))
        total, done = 0.0, False
        while not done:
            s = obs.vector()
            a = agent.act(s, eps)
            obs2, r, done, _ = env.step(a)
            agent.remember(s, a, r, obs2.vector(), done)
            if env.t % 2 == 0:
                agent.learn()
            obs, total = obs2, total + r
        returns.append(total)
        if verbose and (ep % 10 == 0 or ep == episodes - 1):
            print(f"episode {ep:4d}  eps={eps:.2f}  return={total:8.1f}  "
                  f"in-band={env.log['in_band']:3d}d  water={env.log['water']:6.0f}mm  "
                  f"({time.time()-t0:.0f}s)")
    agent.save(out)
    np.save(Path(out).with_name("training_returns.npy"), np.array(returns))
    return agent, returns


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=150)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="results/dqn_weights.npz")
    a = ap.parse_args()
    train(a.episodes, a.seed, a.out)
