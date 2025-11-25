"""Simulation environment for cost‑aware telemetry.

The environment exposes a simple reinforcement learning interface with
`reset()` and `step(action)` methods.  Each episode simulates a period
of system operation where telemetry events (e.g. logs, traces) occur
with varying rates.  The agent can choose discrete actions to adjust
sampling or logging levels.  The reward encourages capturing
important events while penalising cost overrun and missing anomalies.

This toy environment is intended for demonstration and unit testing of
the RL policy engine.  In a real deployment, the agent would
interface with live telemetry metrics and cost forecasts.
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple


@dataclass
class EnvConfig:
    max_steps: int = 100
    budget_limit: float = 1.0  # normalised budget (1.0 = 100% of budget)
    anomaly_rate: float = 0.05  # probability of anomaly per step
    base_cost: float = 0.01  # baseline cost per step when sampling at level 1


class TelemetryEnv:
    """Simple RL environment to model telemetry cost vs signal.

    State representation:
        (relative_cost, anomaly_present)

    Actions (discrete):
        0 = decrease sampling (reduce cost, risk missing anomalies)
        1 = maintain sampling
        2 = increase sampling (raise cost, better chance to catch anomalies)
    """

    def __init__(self, config: EnvConfig | None = None) -> None:
        self.config = config or EnvConfig()
        self.current_step = 0
        self.relative_cost = 0.0
        self.state = (0.0, 0)
        self.rng = np.random.default_rng()

    def reset(self) -> Tuple[float, int]:
        """Reset the environment to the initial state.

        Returns the starting state.
        """
        self.current_step = 0
        self.relative_cost = 0.0
        self.state = (0.0, 0)
        return self.state

    def step(self, action: int) -> Tuple[Tuple[float, int], float, bool, dict]:
        """Advance the environment by one time step.

        Args:
            action: The action taken by the agent (0, 1 or 2).

        Returns:
            state: The new state.
            reward: The reward for the action.
            done: Whether the episode has ended.
            info: Additional information.
        """
        assert action in (0, 1, 2), "Invalid action"
        self.current_step += 1

        # Determine if an anomaly occurs at this step.
        anomaly = int(self.rng.random() < self.config.anomaly_rate)

        # Determine cost multiplier based on action.
        if action == 0:
            sampling_multiplier = 0.5
        elif action == 1:
            sampling_multiplier = 1.0
        else:  # action == 2
            sampling_multiplier = 2.0

        # Cost incurred this step.
        step_cost = self.config.base_cost * sampling_multiplier
        self.relative_cost += step_cost

        # Reward: catch anomalies and stay under budget.
        reward = 0.0
        if anomaly:
            # If we increased sampling (action 2), high chance to catch anomaly.
            catch_prob = 0.9 if action == 2 else 0.5 if action == 1 else 0.1
            caught = self.rng.random() < catch_prob
            reward += 1.0 if caught else -1.0  # positive for catching, negative for missing
        # Cost penalty if we exceed budget.
        if self.relative_cost > self.config.budget_limit:
            reward -= (self.relative_cost - self.config.budget_limit) * 5.0

        # Construct next state: relative cost clipped to [0, 2], anomaly flag.
        self.state = (min(self.relative_cost / self.config.budget_limit, 2.0), anomaly)
        done = self.current_step >= self.config.max_steps
        return self.state, reward, done, {}