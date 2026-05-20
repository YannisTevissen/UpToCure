"""LLM provider abstraction for UpToCure.

Wraps the OpenAI-compatible Chat Completions API so the same code can talk to:
    * OpenAI       (default — set OPENAI_API_KEY)
    * Anthropic    (via LiteLLM or an OpenAI-compatible gateway)
    * Google       (via Gemini OpenAI-compatible endpoint)
    * Local models (Ollama, LM Studio, vLLM, llama.cpp's llama-server)

Environment variables consumed:
    LLM_PROVIDER          openai | ollama | vllm | lmstudio | custom (default: openai)
    LLM_BASE_URL          override base URL of the OpenAI-compatible server
    LLM_API_KEY           override API key (Ollama accepts "ollama")
    LLM_MODEL             chat model id for generation/synthesis
    LLM_TRANSLATION_MODEL chat model id for translation (cheap & fast)
    LLM_TIMEOUT_SECONDS   per-request timeout (default 120)

Default pricing-aware choices (May 2026):
    Generation:   gpt-5            ($1.25 / $10  per 1M tokens)
    Translation:  gemini-2.5-flash-lite via OpenAI-compat endpoint
                  (override LLM_TRANSLATION_MODEL=gpt-5-nano for OpenAI only)
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Iterable

from openai import OpenAI

logger = logging.getLogger(__name__)


PROVIDER_DEFAULTS = {
    "openai":   {"base_url": "https://api.openai.com/v1",        "key_env": "OPENAI_API_KEY"},
    "ollama":   {"base_url": "http://localhost:11434/v1",        "key_env": "OLLAMA_API_KEY", "default_key": "ollama"},
    "lmstudio": {"base_url": "http://localhost:1234/v1",         "key_env": "LMSTUDIO_API_KEY", "default_key": "lm-studio"},
    "vllm":     {"base_url": "http://localhost:8000/v1",         "key_env": "VLLM_API_KEY", "default_key": "vllm"},
    "gemini":   {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                 "key_env": "GEMINI_API_KEY"},
    "anthropic":{"base_url": "https://api.anthropic.com/v1",     "key_env": "ANTHROPIC_API_KEY"},
    "custom":   {"base_url": "http://localhost:8080/v1",         "key_env": "LLM_API_KEY", "default_key": "custom"},
}


@dataclass
class LLMConfig:
    provider: str
    base_url: str
    api_key: str
    generation_model: str
    translation_model: str
    timeout: float

    @classmethod
    def from_env(cls) -> "LLMConfig":
        provider = os.environ.get("LLM_PROVIDER", "openai").lower()
        defaults = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["custom"])

        base_url = os.environ.get("LLM_BASE_URL", defaults["base_url"])
        api_key = (
            os.environ.get("LLM_API_KEY")
            or os.environ.get(defaults["key_env"], "")
            or defaults.get("default_key", "")
        )

        generation_model = os.environ.get("LLM_MODEL", "gpt-5")
        translation_model = os.environ.get(
            "LLM_TRANSLATION_MODEL",
            "gpt-5-nano" if provider == "openai" else generation_model,
        )
        timeout = float(os.environ.get("LLM_TIMEOUT_SECONDS", "120"))

        return cls(
            provider=provider,
            base_url=base_url,
            api_key=api_key,
            generation_model=generation_model,
            translation_model=translation_model,
            timeout=timeout,
        )


class LLMClient:
    """Thin wrapper around an OpenAI-compatible client with retry + logging."""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig.from_env()
        if not self.config.api_key:
            logger.warning(
                "LLM client created without an API key (provider=%s). "
                "Calls will fail until LLM_API_KEY or %s is set.",
                self.config.provider,
                PROVIDER_DEFAULTS.get(self.config.provider, {}).get("key_env", "LLM_API_KEY"),
            )
        self._client = OpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key or "missing",
            timeout=self.config.timeout,
        )

    def chat(
        self,
        messages: list[dict],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        retries: int = 3,
    ) -> str:
        """Send a chat completion and return the assistant text."""
        model_id = model or self.config.generation_model
        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                completion = self._client.chat.completions.create(
                    model=model_id,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return (completion.choices[0].message.content or "").strip()
            except Exception as exc:  # noqa: BLE001 - retry transient errors
                last_error = exc
                delay = 2 ** attempt
                logger.warning("LLM call failed (attempt %d/%d): %s. Retrying in %ds.",
                               attempt + 1, retries, exc, delay)
                time.sleep(delay)
        raise RuntimeError(f"LLM call failed after {retries} attempts: {last_error}")

    # ----- convenience helpers ------------------------------------------------

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """Translate a single markdown block while preserving formatting."""
        system = (
            "You are a professional medical translator. Translate the user's text "
            f"from {source_lang} to {target_lang}. Preserve markdown syntax EXACTLY: "
            "do not modify URLs, anchor text inside [...], code spans, headings, "
            "lists, emphasis, or whitespace. Translate proper nouns conservatively. "
            "Return only the translation, no explanations."
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ]
        return self.chat(messages, model=self.config.translation_model, temperature=0.1)

    def translate_lines(
        self,
        lines: Iterable[str],
        source_lang: str,
        target_lang: str,
        batch_size: int = 25,
    ) -> list[str]:
        """Translate a list of lines, batching to reduce overhead.

        Blank lines and lines that are pure markdown noise (---, ```...) are
        not sent to the model.
        """
        lines = list(lines)
        out: list[str | None] = [None] * len(lines)
        batch: list[tuple[int, str]] = []

        def flush() -> None:
            if not batch:
                return
            sep = "\n<<<UPTOCURE-BLOCK-SEP>>>\n"
            joined = sep.join(text for _, text in batch)
            translated = self.translate(joined, source_lang, target_lang)
            parts = translated.split(sep.strip())
            if len(parts) != len(batch):
                # Model didn't preserve the separator — fall back to line-by-line
                logger.warning("Batch translation lost separators, falling back per-line")
                for idx, text in batch:
                    out[idx] = self.translate(text, source_lang, target_lang)
            else:
                for (idx, _), part in zip(batch, parts):
                    out[idx] = part.strip("\n")
            batch.clear()

        for idx, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped in {"---", "```"} or stripped.startswith("```"):
                out[idx] = line
                continue
            batch.append((idx, line))
            if len(batch) >= batch_size:
                flush()
        flush()

        return [line if value is None else value for value, line in zip(out, lines)]
