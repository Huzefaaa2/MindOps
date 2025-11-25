"""A simple Q‑learning agent for telemetry control.

This agent maintains a Q‑table mapping discretised states to action values.
It learns via the standard Q‑learning update rule:

    Q(s,a) ← Q(s,a) + α [r + γ max_a' Q(s',a') − Q(s,a)]

where α is the learning rate and γ is the discount factor.  The agent
selects actions using an ε‑greedy policy to balance exploration and
exploitation.  States are discretised by binning the relative cost
dimension and keeping the anomaly flag as is.

This module also exposes a basic training loop in `train_agent()` for
testing purposes.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple

from .environment import TelemetryEnv, EnvConfig


@dataclass
class AgentConfig:
    alpha: float = 0.1  # learning rate
    gamma: float = 0.95  # discount factor
    epsilon_start: float = 1.0  # exploration rate at episode 0
    epsilon_end: float = 0.1  # exploration rate at final episode
    episodes: int = 2000
    bins: Tuple[int, ...] = (10,)  # number of bins for relative cost dimension


class QLearningAgent:
    """Tabular Q‑learning agent with ε‑greedy exploration."""

    def __init__(self, env: TelemetryEnv, config: AgentConfig | None = None) -> None:
        self.env = env
        self.config = config or AgentConfig()
        # Precompute bin thresholds for discretising relative cost.
        self.bins = np.linspace(0.0, 2.0, self.config.bins[0] + 1)[1:-1]
        # Q‑table stored in a nested dict: state → action values.
        self.q_table: Dict[Tuple[int, int], np.ndarray] = {}

    def discretise_state(self, state: Tuple[float, int]) -> Tuple[int, int]:
        """Convert a continuous state to a discrete key for the Q‑table."""
        relative_cost, anomaly_flag = state
        cost_bin = int(np.digitize(relative_cost, self.bins))
        return cost_bin, anomaly_flag

    def get_action(self, state: Tuple[float, int], epsilon: float) -> int:
        """Select an action using an ε‑greedy policy."""
        state_key = self.discretise_state(state)
        if state_key not in self.q_table:
            # Initialise Q values for unseen states.
            self.q_table[state_key] = np.zeros(3)
        if np.random.random() < epsilon:
            return np.random.randint(3)
        return int(np.argmax(self.q_table[state_key]))

    def update_q(self, state: Tuple[float, int], action: int, reward: float,
                 next_state: Tuple[float, int]) -> None:
        """Apply the Q‑learning update rule."""
        state_key = self.discretise_state(state)
        next_key = self.discretise_state(next_state)
        # Lazy initialise.
        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(3)
        if next_key not in self.q_table:
            self.q_table[next_key] = np.zeros(3)
        current_q = self.q_table[state_key][action]
        next_max_q = np.max(self.q_table[next_key])
        target = reward + self.config.gamma * next_max_q
        self.q_table[state_key][action] = current_q + self.config.alpha * (target - current_q)

    def train(self) -> None:
        """Train the agent using Q‑learning in the provided environment."""
        eps_start = self.config.epsilon_start
        eps_end = self.config.epsilon_end
        for episode in range(self.config.episodes):
            state = self.env.reset()
            done = False
            # Linearly anneal epsilon.
            epsilon = eps_start - (eps_start - eps_end) * (episode / (self.config.episodes - 1))
            while not done:
                action = self.get_action(state, epsilon)
                next_state, reward, done, _ = self.env.step(action)
                self.update_q(state, action, reward, next_state)
                state = next_state

    def act(self, state: Tuple[float, int]) -> int:
        """Choose the best action (greedy) for the given state."""
        state_key = self.discretise_state(state)
        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(3)
        return int(np.argmax(self.q_table[state_key]))


def train_agent_demo() -> None:
    """Example usage: train an agent and print learned Q values."""
    env = TelemetryEnv()
    agent = QLearningAgent(env)
    agent.train()
    print("Learned Q‑table entries:")
    for state_key, values in list(agent.q_table.items())[:10]:
        print(f"state {state_key}: {values}")


if __name__ == "__main__":
    train_agent_demo()