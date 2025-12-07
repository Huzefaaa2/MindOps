"""
llm_reasoner.py
===============

This module wraps a large language model (LLM) API to perform root
cause analysis over trace data.  Given the current incident spans and
a set of retrieved similar contexts, the LLM synthesises a concise
narrative explaining what went wrong.  The default implementation
uses the OpenAI ChatCompletion API, but the interface can be
adapted to support alternative providers by overriding the
``_call_llm`` method.

The :class:`LLMReasoner` constructs a chat prompt that instructs the
model to output a small JSON object with two keys: ``root_cause``
(a short phrase) and ``reasoning`` (a brief explanation).  If the
response cannot be parsed as JSON, the raw text is returned under
``reasoning``.
"""
from __future__ import annotations

import os
import json
from typing import List, Dict, Any, Iterable

from tenacity import retry, wait_random_exponential, stop_after_attempt

from .config import ModelConfig

# Import the OpenAI client if available.  This module is only loaded
# when needed to avoid forcing an optional dependency on users who
# substitute their own LLM provider.
try:
    import openai  # type: ignore[import]
    if os.getenv("OPENAI_API_KEY"):
        openai.api_key = os.getenv("OPENAI_API_KEY")
except ImportError:
    openai = None  # type: ignore[assignment]


class LLMReasoner:
    """Reason about the root cause of an incident using a language model."""

    def __init__(self, config: ModelConfig) -> None:
        self.config = config
        if openai is None:
            raise ImportError(
                "openai library is not installed. Please install it or modify"
                " LLMReasoner to use another provider."
            )

    def generate_root_cause(
        self,
        current_spans: Iterable[Dict[str, Any]],
        retrieved_contexts: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate a root cause hypothesis given current and historical spans.

        Args:
            current_spans: An iterable of span dictionaries representing
                the current incident.  The dictionaries should contain
                at least a ``message`` key.
            retrieved_contexts: An iterable of metadata objects returned
                from the vector store.  Each should include a ``message``
                field and any other relevant metadata.

        Returns:
            A dictionary with keys ``root_cause``, ``reasoning`` and
            ``raw`` (the raw model output).  If the model output cannot
            be parsed as JSON, ``root_cause`` will be ``"unknown"`` and
            ``reasoning`` will contain the unparsed output.
        """
        messages = self._build_prompt(current_spans, retrieved_contexts)
        response_text = self._call_llm(messages)
        # Attempt to parse the response as JSON
        try:
            parsed = json.loads(response_text)
            return {
                "root_cause": parsed.get("root_cause", "unknown"),
                "reasoning": parsed.get("reasoning", response_text),
                "raw": response_text,
            }
        except json.JSONDecodeError:
            return {
                "root_cause": "unknown",
                "reasoning": response_text,
                "raw": response_text,
            }

    def _build_prompt(
        self,
        current_spans: Iterable[Dict[str, Any]],
        retrieved_contexts: Iterable[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """Construct a chat prompt for the language model.

        The prompt includes a system message describing the task and a
        user message containing summaries of the current incident spans
        and the retrieved similar contexts.

        Returns:
            A list of chat messages conforming to the OpenAI API format.
        """
        # Summarise the current spans into a numbered list
        current_summary = "\n".join(
            f"{i+1}. {span.get('message') or span}" for i, span in enumerate(current_spans)
        )
        # Summarise retrieved contexts similarly
        context_summary = "\n".join(
            f"{i+1}. {ctx.get('message') or ctx}" for i, ctx in enumerate(retrieved_contexts)
        )
        system_prompt = (
            "You are an SRE assistant for cloud applications. You are given a set "
            "of trace span summaries from a current incident and a set of summaries "
            "from past similar incidents. Analyse the current spans, compare them "
            "to the past context and identify the most likely root cause of the "
            "incident. Provide your answer as a JSON object with two fields: "
            "`root_cause` (a concise phrase) and `reasoning` (a brief paragraph)."
        )
        user_message = (
            "Current incident spans:\n"
            f"{current_summary}\n\n"
            "Retrieved similar contexts:\n"
            f"{context_summary}\n"
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """Call the OpenAI ChatCompletion API with retries.

        Args:
            messages: A list of message dicts to send to the API.

        Returns:
            The content of the assistant's reply as a string.
        """
        response = openai.ChatCompletion.create(
            model=self.config.openai_model_name,
            messages=messages,
            temperature=self.config.openai_temperature,
        )
        return response["choices"][0]["message"]["content"].strip()