# Trace‑Native RAG Contextual Layer

The RAG (Retrieval‑Augmented Generation) contextual layer provides
AI‑assisted analysis of telemetry data.  It listens to logs, traces
and metrics, retrieves relevant context and then queries a large
language model (LLM) to generate human‑friendly explanations or
summaries.  This allows SREs and developers to ask natural language
questions about recent incidents, anomalies and performance spikes.

This directory contains a simple service that exposes a gRPC API for
querying telemetry context.  Under the hood it uses the OpenAI API
(`openai` Python package) to perform retrieval‑augmented generation.
API keys should be supplied via environment variables and never
committed to the repository.