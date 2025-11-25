# Telemetry Budget Engine

The telemetry budget engine predicts how much telemetry data will be
generated in the future and how that translates into cost.  It uses
classical time‑series models (ARIMA) and deep learning models (LSTM)
to forecast telemetry volume based on historical trends.  These
forecasts are used by the RL policy engine to avoid cost overruns and
trigger adaptive sampling when necessary.

This directory contains simple examples of how to perform such
forecasting using Python.  The code is written with minimal
dependencies so that it runs in most Python environments.  For real
deployments you may wish to integrate with existing observability
data sources (e.g. Prometheus, Elastic) and use more sophisticated
models.