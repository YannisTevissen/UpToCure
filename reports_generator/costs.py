"""Cost estimation and monthly spend ledger for the report pipeline.

Prices are USD per 1M tokens (input, output), August 2026. Unknown models fall
back to a deliberately conservative price so the budget cap can never be
undershot by a missing table entry.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# (input $/1M, output $/1M)
MODEL_PRICES: dict[str, tuple[float, float]] = {
    "gpt-5.6-sol": (5.00, 30.00),
    "gpt-5.6-terra": (2.00, 12.00),
    "gpt-5.6-luna": (0.20, 1.20),
    "gpt-5.5": (5.00, 30.00),
    "gpt-5.4-mini": (0.75, 4.50),
    "gpt-5.4-nano": (0.20, 1.25),
    "gpt-5.4": (2.50, 15.00),
    "gpt-5-mini": (0.25, 2.00),
    "gpt-5-nano": (0.05, 0.40),
    "gpt-5": (1.25, 10.00),
    "o4-mini-deep-research": (2.00, 8.00),
    "o3-deep-research": (10.00, 40.00),
}

# Hosted web_search tool on the OpenAI Responses API.
WEB_SEARCH_COST_PER_CALL = 0.01

# Charged for unknown models so budget enforcement stays conservative.
FALLBACK_PRICE = (5.00, 30.00)

# When a backend cannot report token usage (some smolagents versions), assume
# a typical agent run so the ledger overestimates rather than undercounts.
ASSUMED_INPUT_TOKENS = 80_000
ASSUMED_OUTPUT_TOKENS = 8_000


def model_price(model_id: str) -> tuple[float, float]:
    """Longest-prefix match so dated snapshots (gpt-5.6-terra-2026-07-09) resolve."""
    name = (model_id or "").split("/")[-1].lower()
    best: tuple[float, float] | None = None
    best_len = -1
    for key, price in MODEL_PRICES.items():
        if name.startswith(key) and len(key) > best_len:
            best, best_len = price, len(key)
    if best is None:
        logger.warning("No price for model %r, using conservative fallback", model_id)
        return FALLBACK_PRICE
    return best


def estimate_cost(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    search_calls: int = 0,
) -> float:
    if not input_tokens and not output_tokens:
        input_tokens, output_tokens = ASSUMED_INPUT_TOKENS, ASSUMED_OUTPUT_TOKENS
    price_in, price_out = model_price(model_id)
    tokens_usd = (input_tokens * price_in + output_tokens * price_out) / 1_000_000
    return round(tokens_usd + search_calls * WEB_SEARCH_COST_PER_CALL, 4)


# ----- ledger -------------------------------------------------------------------

def default_state_dir() -> Path:
    env = os.environ.get("UPTOCURE_STATE_DIR")
    if env:
        return Path(env)
    reports_root = os.environ.get("UPTOCURE_REPORTS_DIR")
    if reports_root:
        return Path(reports_root) / ".state"
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "UpToCure" / "reports" / ".state"


class CostLedger:
    """Monthly spend ledger persisted as one JSON file in the state dir."""

    def __init__(self, state_dir: Path | None = None):
        self.state_dir = state_dir or default_state_dir()
        self.path = self.state_dir / "cost-ledger.json"

    @staticmethod
    def month_key(when: dt.date | None = None) -> str:
        return (when or dt.date.today()).strftime("%Y-%m")

    def _load(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.exception("Corrupt ledger at %s, starting fresh", self.path)
            return {}

    def month_total(self, month: str | None = None) -> float:
        data = self._load()
        bucket = data.get(month or self.month_key()) or {}
        return float(bucket.get("total_usd", 0.0))

    def record(
        self,
        *,
        kind: str,
        disease: str,
        model: str,
        cost_usd: float,
        backend: str | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        search_calls: int = 0,
    ) -> float:
        """Append an entry and return the new month-to-date total."""
        data = self._load()
        month = self.month_key()
        bucket = data.setdefault(month, {"total_usd": 0.0, "entries": []})
        bucket["entries"].append({
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "kind": kind,
            "disease": disease,
            "model": model,
            "backend": backend,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "search_calls": search_calls,
            "cost_usd": round(cost_usd, 4),
        })
        bucket["total_usd"] = round(bucket["total_usd"] + cost_usd, 4)
        self._write(data)
        return bucket["total_usd"]

    def _write(self, data: dict) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.state_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
            os.replace(tmp, self.path)
        except OSError:
            Path(tmp).unlink(missing_ok=True)
            raise


def monthly_budget_usd() -> float:
    return float(os.environ.get("MONTHLY_BUDGET_USD", "30"))
