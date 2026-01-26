"""Integration with Project 1 (CAAT)."""
from __future__ import annotations

from typing import List, Optional

from .utils import IntegrationStatus, IntegrationUnavailable, ensure_project_path, optional_import
from ..models import TelemetryRecommendation


_ACTION_MAP = {
    0: "decrease_sampling",
    1: "maintain_sampling",
    2: "increase_sampling",
}


class CAATAdapter:
    def __init__(self) -> None:
        ensure_project_path("caat")
        self._policy_module = optional_import("rl_policy_engine")
        try:
            self._budget_module = optional_import("telemetry_budget_engine.budget_controller")
        except IntegrationUnavailable:
            # Fall back to loading budget controller as a top-level module if packaging is missing.
            ensure_project_path("caat", "telemetry_budget_engine")
            self._budget_module = optional_import("budget_controller")

    def recommend(self,
                  telemetry_volumes: Optional[List[float]] = None,
                  anomaly_flag: bool = False,
                  current_relative_cost: Optional[float] = None) -> TelemetryRecommendation:
        budget_engine = self._budget_module.BudgetEngine()
        if telemetry_volumes:
            for volume in telemetry_volumes:
                budget_engine.update(volume)
        forecast = budget_engine.forecast_next(steps=7)
        budget_alert = budget_engine.needs_action()

        env = self._policy_module.TelemetryEnv()
        agent = self._policy_module.QLearningAgent(env)
        relative_cost = current_relative_cost
        if relative_cost is None:
            if telemetry_volumes:
                relative_cost = telemetry_volumes[-1] / budget_engine.config.target_budget
            else:
                relative_cost = 1.0
        action = agent.act((relative_cost, int(anomaly_flag)))
        sampling_action = _ACTION_MAP.get(action, "maintain_sampling")
        notes = []
        if budget_alert:
            notes.append("Telemetry forecast exceeds budget threshold.")
        return TelemetryRecommendation(
            sampling_action=sampling_action,
            budget_alert=budget_alert,
            forecast=[round(value, 4) for value in forecast],
            notes=notes,
        )


def caat_status() -> IntegrationStatus:
    try:
        ensure_project_path("caat")
        optional_import("rl_policy_engine")
        return IntegrationStatus(name="caat", status="ready")
    except IntegrationUnavailable as exc:
        return IntegrationStatus(name="caat", status="unavailable", detail=str(exc))
