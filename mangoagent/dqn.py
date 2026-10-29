"""Minimal Deep Q-Network in pure numpy (MLP, replay buffer, target network, Adam)."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np


class MLP:
    def __init__(self, sizes, rng):
        self.W, self.b = [], []
        for i, o in zip(sizes[:-1], sizes[1:]):
            self.W.append((rng.standard_normal((i, o)) * np.sqrt(2.0 / i)).astype(np.float32))
            self.b.append(np.zeros(o, dtype=np.float32))
        self.m = [np.zeros_like(p) for p in self.params()]
        self.v = [np.zeros_like(p) for p in self.params()]
        self.t = 0

    def params(self):
        return [p for pair in zip(self.W, self.b) for p in pair]

    def forward(self, x, keep=False):
        acts = [x]
        for k in range(len(self.W) - 1):
            x = np.maximum(0, x @ self.W[k] + self.b[k])
            acts.append(x)
        out = x @ self.W[-1] + self.b[-1]
        return (out, acts) if keep else out

    def train_step(self, x, dout, lr=1e-3):
        _, acts = self.forward(x, keep=True)
        grads = []
        d = dout
        for k in range(len(self.W) - 1, -1, -1):
            gW = acts[k].T @ d
            gb = d.sum(0)
            grads = [gW, gb] + grads
            if k > 0:
                d = (d @ self.W[k].T) * (acts[k] > 0)
        self.t += 1
        for i, (p, g) in enumerate(zip(self.params(), grads)):
            g = np.clip(g, -5, 5)
            self.m[i] = 0.9 * self.m[i] + 0.1 * g
            self.v[i] = 0.999 * self.v[i] + 0.001 * g * g
            mh = self.m[i] / (1 - 0.9 ** self.t)
            vh = self.v[i] / (1 - 0.999 ** self.t)
            p -= lr * mh / (np.sqrt(vh) + 1e-8)

    def copy_from(self, other):
        for a, b in zip(self.params(), other.params()):
            a[...] = b


class DQNAgent:
    def __init__(self, state_dim, n_actions, seed=0, hidden=64, gamma=0.97, lr=1e-3,
                 buffer=30000, batch=64, target_sync=400):
        self.rng = np.random.default_rng(seed)
        self.n_actions, self.gamma, self.lr, self.batch = n_actions, gamma, lr, batch
        self.q = MLP([state_dim, hidden, hidden, n_actions], self.rng)
        self.target = MLP([state_dim, hidden, hidden, n_actions], self.rng)
        self.target.copy_from(self.q)
        self.cap = buffer
        self.S = np.zeros((buffer, state_dim), np.float32)
        self.S2 = np.zeros((buffer, state_dim), np.float32)
        self.A = np.zeros(buffer, np.int64)
        self.R = np.zeros(buffer, np.float32)
        self.D = np.zeros(buffer, np.float32)
        self.n = 0
        self.ptr = 0
        self.target_sync = target_sync
        self.steps = 0

    def act(self, s, eps=0.0):
        if self.rng.random() < eps:
            return int(self.rng.integers(self.n_actions))
        return int(np.argmax(self.q.forward(s[None, :])[0]))

    def q_values(self, s):
        return self.q.forward(s[None, :])[0]

    def remember(self, s, a, r, s2, done):
        i = self.ptr
        self.S[i], self.A[i], self.R[i], self.S2[i], self.D[i] = s, a, r, s2, float(done)
        self.ptr = (self.ptr + 1) % self.cap
        self.n = min(self.n + 1, self.cap)

    def learn(self):
        if self.n < self.batch * 4:
            return
        idx = self.rng.integers(0, self.n, self.batch)
        s, a, r, s2, d = self.S[idx], self.A[idx], self.R[idx], self.S2[idx], self.D[idx]
        # Double-DQN target
        a2 = np.argmax(self.q.forward(s2), axis=1)
        q2 = self.target.forward(s2)[np.arange(self.batch), a2]
        y = r + self.gamma * (1 - d) * q2
        out = self.q.forward(s)
        err = out[np.arange(self.batch), a] - y
        huber = np.clip(err, -1, 1)
        dout = np.zeros_like(out)
        dout[np.arange(self.batch), a] = huber / self.batch
        self.q.train_step(s, dout, self.lr)
        self.steps += 1
        if self.steps % self.target_sync == 0:
            self.target.copy_from(self.q)

    # --- persistence -------------------------------------------------------
    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(path, **{f"W{i}": w for i, w in enumerate(self.q.W)},
                 **{f"b{i}": b for i, b in enumerate(self.q.b)})

    def load(self, path):
        z = np.load(path)
        k = len(self.q.W)
        if "arr_0" in z:
            for i in range(k):
                self.q.W[i][...] = z[f"arr_{i}"]
                self.q.b[i][...] = z[f"arr_{i + k}"]
        else:
            for i in range(k):
                self.q.W[i][...] = z[f"W{i}"]
                self.q.b[i][...] = z[f"b{i}"]
        self.target.copy_from(self.q)
