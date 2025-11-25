"""Reinforcement learning policy engine for CAAT.

This package contains the code that trains and runs the RL agent used to
adapt telemetry sampling rates and logging levels.  The agent treats
observability as a control problem: given the current system state and
budget situation, decide how aggressively to collect telemetry.
"""

from .environment import TelemetryEnv
from .policy_agent import QLearningAgent