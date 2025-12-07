# Trace‑Native RAG for Root Cause (T‑RAG)

T‑RAG is the second project in the **MindOps** initiative.  Whereas CAAT (project 1) focuses on dynamic telemetry collection and cost control, **T‑RAG** tackles the next stage: **rapid, AI‑assisted root cause analysis (RCA)** using live traces, logs and metrics.  This project provides a reference implementation of a trace‑native retrieval‑augmented generation (RAG) service that integrates seamlessly with the observability pipeline established in CAAT.

## Motivation

Modern cloud architectures are built from hundreds of microservices interacting in complex ways.  When an incident occurs, developers and SREs often spend hours digging through logs, metrics dashboards and tracing tools to understand what went wrong.  T‑RAG accelerates this workflow by:

* Treating **distributed traces** as first‑class context for reasoning.  Instead of only querying documentation, the RAG engine retrieves actual span data, error stacks and metrics around the time of the incident.
* Maintaining a **vector memory store** of past incidents and telemetry patterns.  Relevant historical contexts are surfaced automatically, enabling time‑aware reasoning.
* Using a **Large Language Model (LLM)** to synthesize the retrieved context into a concise explanation of the root cause, expressed in plain language and returned as structured JSON.

## Directory Structure

```
projects/t_rag/
│
├── README.md         # You are here – overview and usage instructions
├── requirements.txt   # Python dependencies for the T‑RAG service
├── examples/
│   └── sample_trace.json  # Example trace to test the service end‑to‑end
└── src/
    └── t_rag/
        ├── __init__.py
        ├── config.py        # Configuration dataclass for the service
        ├── trace_loader.py  # Load and summarize traces from JSON/OTLP
        ├── vector_memory.py # In‑memory vector store with nearest‑neighbour search
        ├── llm_reasoner.py  # Wrapper around the OpenAI API to produce RCA
        └── service.py       # CLI entrypoint orchestrating the pipeline
```

## Dependencies and Integration

T‑RAG builds upon several components of **Project 1 – CAAT**:

* **Telemetry Pipeline**: T‑RAG expects telemetry (logs, metrics and traces) to be collected and exposed via OpenTelemetry collectors.  You can reuse the OTEL deployment and eBPF probes from CAAT.
* **RAG Contextual Layer**: CAAT includes a rudimentary RAG service for contextual explanations.  T‑RAG evolves this into a dedicated RCA system with deeper tracing support and vector memory.  You may still reuse parts of the CAAT RAG layer (e.g. authentication utilities).
* **RL Telemetry Optimizer & Budget Engine**: These components are not required to run T‑RAG, but running them in tandem ensures that the right traces are sampled and retained, improving RCA accuracy.  T‑RAG can consume the sampling policies emitted by the RL optimizer via shared configuration or API.

T‑RAG is otherwise self‑contained; you can deploy it independently or alongside CAAT.  The service exposes a simple CLI and can be wrapped in a REST API or Kubernetes deployment as needed.

## Quickstart

1. **Install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Prepare an OpenAI API key:** set the `OPENAI_API_KEY` environment variable.  You can also override the model and temperature in `config.py` or via command‑line options.

3. **Run the service on a sample trace:**
   ```bash
   python -m t_rag.service --trace examples/sample_trace.json
   ```
   The script will load the spans, embed them, populate the vector store, retrieve similar spans (none in the first run) and ask the LLM to infer a root cause.  The result is printed as JSON with `root_cause` and `reasoning` fields.

4. **Integrate with your observability stack:** hook the service into your alerting pipeline so that when an incident triggers, the relevant spans and logs are passed to T‑RAG.  See `service.py` for guidance on programmatic usage.

## Next Steps

This reference implementation uses an in‑memory vector store and relies on the OpenAI API.  For production use, consider:

* **Persistent Vector Storage**: Replace `vector_memory.py` with a database‐backed store (e.g. Pinecone, Weaviate, OpenSearch) to retain embeddings across restarts.
* **Streaming Ingestion**: Implement a listener that continually ingests spans, logs and metrics into the vector store.
* **Multiple Agents**: Extend `llm_reasoner.py` to orchestrate multiple specialized agents (trace summarization, log analysis, metrics anomaly detection) and synthesize their outputs.
* **Deployment**: Package the service as a Docker container and expose a gRPC or REST endpoint.  Consider adding Helm charts similar to those in CAAT for Kubernetes deployment.

Contributions are welcome!  Please open issues or pull requests if you’d like to improve T‑RAG or integrate with other tools.