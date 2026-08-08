"""Pluggable research backends for report generation.

Select with RESEARCH_BACKEND (or the --backend CLI flag):

    smolagents        CodeAgent loop with free DuckDuckGo search (default,
                      works with any OpenAI-compatible provider).
    openai-responses  One OpenAI Responses API call using the hosted
                      `web_search` tool. OpenAI only. More robust unattended.
    deep-research     OpenAI deep-research model (o4-mini-deep-research) with
                      autonomous search, capped via DEEP_RESEARCH_MAX_TOOL_CALLS.

Every backend returns a ResearchResult with the markdown body plus token/search
usage so the caller can compute cost and enforce the monthly budget.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass

from costs import estimate_cost
from llm import LLMConfig

logger = logging.getLogger(__name__)

DEFAULT_BACKEND = "smolagents"
BACKENDS = ("smolagents", "openai-responses", "deep-research")

# Deep-research and web-search runs routinely take several minutes.
LONG_CALL_TIMEOUT_SECONDS = float(os.environ.get("RESEARCH_TIMEOUT_SECONDS", "1800"))


@dataclass
class ResearchResult:
    markdown: str
    backend: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    search_calls: int = 0

    @property
    def cost_usd(self) -> float:
        return estimate_cost(
            self.model, self.input_tokens, self.output_tokens, self.search_calls
        )


def backend_from_env() -> str:
    backend = os.environ.get("RESEARCH_BACKEND", DEFAULT_BACKEND).lower()
    if backend not in BACKENDS:
        raise ValueError(f"Unknown RESEARCH_BACKEND={backend!r}, expected one of {BACKENDS}")
    return backend


def run_research(prompt: str, config: LLMConfig, backend: str | None = None) -> ResearchResult:
    backend = (backend or backend_from_env()).lower()
    if backend == "smolagents":
        return _run_smolagents(prompt, config)
    if backend == "openai-responses":
        return _run_openai_responses(prompt, config)
    if backend == "deep-research":
        return _run_deep_research(prompt, config)
    raise ValueError(f"Unknown backend {backend!r}, expected one of {BACKENDS}")


# ----- smolagents (agent loop + free DuckDuckGo search) --------------------------

_REASONING_MODELS_WITHOUT_STOP = re.compile(
    r"^("
    r"o3[-\d]*"
    r"|o4-mini[-\d]*"
    r"|gpt-5(\.\d+)?(-\w+)*(-\d{4}-\d{2}-\d{2})?"
    r")$"
)


def _patch_smolagents_stop_support() -> None:
    """Teach smolagents that GPT-5 family and o-series models reject `stop`.

    smolagents <= 1.17 only filters out `o3` and `o4-mini`; newer OpenAI
    reasoning models also return HTTP 400 when `stop` is sent.
    """
    from smolagents import models as smolagents_models

    original = smolagents_models.supports_stop_parameter

    def patched(model_id: str) -> bool:
        model_name = (model_id or "").split("/")[-1]
        if _REASONING_MODELS_WITHOUT_STOP.match(model_name):
            return False
        return original(model_id)

    smolagents_models.supports_stop_parameter = patched


def _build_agent(model_id: str, api_base: str, api_key: str):
    """Lazy import smolagents so the module is importable without it installed."""
    _patch_smolagents_stop_support()

    from smolagents import CodeAgent, OpenAIServerModel
    from smolagents.default_tools import (
        DuckDuckGoSearchTool,
        VisitWebpageTool,
    )

    model = OpenAIServerModel(model_id=model_id, api_base=api_base, api_key=api_key)
    return CodeAgent(
        tools=[DuckDuckGoSearchTool(), VisitWebpageTool()],
        model=model,
        max_steps=12,
        additional_authorized_imports=["json", "re"],
    )


def _smolagents_usage(agent) -> tuple[int, int]:
    """Best-effort token counts across smolagents versions (0 if unavailable)."""
    monitor = getattr(agent, "monitor", None)
    input_tokens = int(getattr(monitor, "total_input_token_count", 0) or 0)
    output_tokens = int(getattr(monitor, "total_output_token_count", 0) or 0)
    if input_tokens or output_tokens:
        return input_tokens, output_tokens
    counts = getattr(monitor, "get_total_token_counts", None)
    if callable(counts):
        try:
            totals = counts()
            if isinstance(totals, dict):
                return int(totals.get("input", 0) or 0), int(totals.get("output", 0) or 0)
            return int(getattr(totals, "input_tokens", 0) or 0), int(getattr(totals, "output_tokens", 0) or 0)
        except Exception:  # noqa: BLE001 - usage is best-effort
            logger.debug("Could not read smolagents token counts", exc_info=True)
    return 0, 0


def _run_smolagents(prompt: str, config: LLMConfig) -> ResearchResult:
    agent = _build_agent(
        model_id=config.generation_model,
        api_base=config.base_url,
        api_key=config.api_key,
    )
    body = str(agent.run(prompt)).strip()
    input_tokens, output_tokens = _smolagents_usage(agent)
    return ResearchResult(
        markdown=body,
        backend="smolagents",
        model=config.generation_model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


# ----- OpenAI Responses API (hosted web_search tool) ------------------------------

def _responses_client(config: LLMConfig):
    from openai import OpenAI

    return OpenAI(
        base_url=config.base_url,
        api_key=config.api_key,
        timeout=LONG_CALL_TIMEOUT_SECONDS,
    )


def _count_search_calls(response) -> int:
    calls = 0
    for item in getattr(response, "output", None) or []:
        if "web_search" in str(getattr(item, "type", "")):
            calls += 1
    return calls


def _responses_result(response, backend: str, model: str) -> ResearchResult:
    usage = getattr(response, "usage", None)
    return ResearchResult(
        markdown=(response.output_text or "").strip(),
        backend=backend,
        model=model,
        input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
        output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
        search_calls=_count_search_calls(response),
    )


def _run_openai_responses(prompt: str, config: LLMConfig) -> ResearchResult:
    if config.provider != "openai":
        raise RuntimeError("The openai-responses backend requires LLM_PROVIDER=openai")
    client = _responses_client(config)
    response = client.responses.create(
        model=config.generation_model,
        input=prompt,
        tools=[{"type": "web_search"}],
    )
    return _responses_result(response, "openai-responses", config.generation_model)


# ----- OpenAI deep-research models ------------------------------------------------

def _run_deep_research(prompt: str, config: LLMConfig) -> ResearchResult:
    if config.provider != "openai":
        raise RuntimeError("The deep-research backend requires LLM_PROVIDER=openai")
    model = os.environ.get("DEEP_RESEARCH_MODEL", "o4-mini-deep-research")
    max_tool_calls = int(os.environ.get("DEEP_RESEARCH_MAX_TOOL_CALLS", "25"))
    client = _responses_client(config)
    response = client.responses.create(
        model=model,
        input=prompt,
        tools=[{"type": "web_search_preview"}],
        # Passed via extra_body: older openai SDKs don't have the kwarg yet.
        extra_body={"max_tool_calls": max_tool_calls},
    )
    return _responses_result(response, "deep-research", model)
