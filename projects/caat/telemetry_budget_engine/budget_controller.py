"""Telemetry budget controller.

This module provides a simple class that monitors telemetry volume over
time and uses forecasting models to predict future usage.  When the
predicted volume approaches or exceeds a predefined budget, the
controller can notify the RL policy engine to adjust sampling.

For simplicity the implementation uses moving averages and a naive
ARIMA model from the `statsmodels` library if available.  If
`statsmodels` is not installed the controller falls back to a basic
exponential smoothing method.  LSTM models are referenced but not
implemented here due to their heavy dependencies; see
`forecast_lstm.py` for a template.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import List

import numpy as np

try:
    from statsmodels.tsa.arima.model import ARIMA  # type: ignore
    _HAS_ARIMA = True
except ImportError:
    _HAS_ARIMA = False
    warnings.warn(
        "statsmodels not available; falling back to naive forecasting", RuntimeWarning
    )


@dataclass
class BudgetConfig:
    target_budget: float = 1.0  # Normalised monthly budget (1.0 = 100%)
    window_size: int = 30  # Number of days in the training window


class BudgetEngine:
    """Telemetry budget engine for CAAT."""

    def __init__(self, config: BudgetConfig | None = None) -> None:
        self.config = config or BudgetConfig()
        self.history: List[float] = []  # daily telemetry volumes (normalised)

    def update(self, volume: float) -> None:
        """Record telemetry volume for one day (normalised to budget)."""
        self.history.append(volume)
        if len(self.history) > self.config.window_size:
            self.history.pop(0)

    def forecast_next(self, steps: int = 7) -> List[float]:
        """Forecast telemetry volume for the next `steps` days."""
        if not self.history:
            return [0.0] * steps
        data = np.array(self.history)
        if _HAS_ARIMA and len(data) >= 3:
            # Fit a simple ARIMA(1,0,0) model as a demonstration.
            model = ARIMA(data, order=(1, 0, 0))
            fit = model.fit()
            forecast = fit.forecast(steps=steps)
            return forecast.tolist()
        else:
            # Fallback: simple exponential smoothing.
            alpha = 0.5
            level = data[-1]
            forecasts = []
            for _ in range(steps):
                level = alpha * level + (1 - alpha) * data.mean()
                forecasts.append(level)
            return forecasts

    def needs_action(self) -> bool:
        """Return True if forecasted usage exceeds budget threshold."""
        forecasts = self.forecast_next(steps=14)
        max_pred = max(forecasts)
        return max_pred > self.config.target_budget