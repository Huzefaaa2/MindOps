"""Trace‑Native RAG context agent.

This script implements a minimal service for context‑aware querying of
telemetry events.  It accepts natural language questions, retrieves
relevant logs/traces from a data store and uses OpenAI’s API to
summarise or explain them.  For demonstration purposes the
implementation below uses an in‑memory list to store example log
messages and a stubbed retrieval function.  In a production system
this would be replaced by a call to a vector database (e.g. Pinecone,
FAISS) or a time‑series/trace store (e.g. Jaeger, Elastic) and
OpenAI’s embeddings API.

Environment variables:
    OPENAI_API_KEY – the API key for OpenAI (not stored in this repo).

Run this module as a script to start a basic CLI for querying
telemetry context via the command line.
"""

from __future__ import annotations

import os
from typing import List

import openai  # type: ignore[import]


class ContextAgent:
    def __init__(self, logs: List[str] | None = None) -> None:
        self.logs = logs or []
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable not set. Please set your API key."
            )
        openai.api_key = api_key

    def add_log(self, message: str) -> None:
        """Add a log message to the context store."""
        self.logs.append(message)

    def retrieve_context(self, query: str, k: int = 5) -> List[str]:
        """Retrieve the k most relevant logs for a given query.

        This stub implementation simply returns the last k log messages.
        A real implementation would use embeddings and vector search.
        """
        return self.logs[-k:]

    def generate_answer(self, query: str) -> str:
        """Generate an answer to a natural language query using OpenAI.

        The prompt is constructed by concatenating the retrieved
        context with the user’s question.  This is a simplified form of
        Retrieval‑Augmented Generation (RAG).  For complex systems
        multiple messages or instructions may be needed.
        """
        context = self.retrieve_context(query)
        prompt = "\n".join([
            "You are an observability assistant helping to explain system events.",
            f"Context: {context}",
            f"Question: {query}",
            "Provide a concise and helpful answer based on the context."
        ])
        completion = openai.ChatCompletion.create(
            model="gpt-4",  # or another model name
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        return completion.choices[0].message["content"].strip()


def main() -> None:
    """A simple CLI for testing the ContextAgent."""
    import readline  # noqa: F401  # enable shell history
    agent = ContextAgent()
    print("ContextAgent CLI. Type logs prefixed with 'log:' and questions prefixed with 'ask:'.")
    while True:
        try:
            line = input("→ ").strip()
        except EOFError:
            break
        if line.startswith("log:"):
            agent.add_log(line[4:].strip())
            print("Log added.")
        elif line.startswith("ask:"):
            question = line[4:].strip()
            answer = agent.generate_answer(question)
            print(f"Answer: {answer}")
        else:
            print("Unknown command. Use 'log:' or 'ask:' prefix.")


if __name__ == "__main__":
    main()