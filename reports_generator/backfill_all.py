#!/usr/bin/env python3
"""One-shot parallel backfill: regenerate every report + fresh translations.

Run manually (not part of the scheduled pipeline):
    pdm run python backfill_all.py [--workers 8]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import threading
import unicodedata
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from costs import CostLedger, estimate_cost  # noqa: E402
from llm import LLMClient, LLMConfig  # noqa: E402
from reporter import REPORTS_ROOT, generate_report  # noqa: E402
from translator import translate_file  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backfill")
logging.getLogger("httpx").setLevel(logging.WARNING)

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(value: str) -> str:
    d = unicodedata.normalize("NFKD", value.strip())
    return _SLUG_RE.sub("-", d.encode("ascii", "ignore").decode().lower()).strip("-")


class LockedLedger(CostLedger):
    _lock = threading.Lock()

    def record(self, **kwargs):
        with self._lock:
            return super().record(**kwargs)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    config = LLMConfig.from_env()
    ledger = LockedLedger()
    en_dir = REPORTS_ROOT / "en"
    fr_dir = REPORTS_ROOT / "fr"

    data = yaml.safe_load((Path(__file__).resolve().parent / "diseases.yaml").read_text())
    diseases = [d for d in (data.get("diseases") or []) if d]
    known = {_slug(d) for d in diseases}
    for path in sorted(en_dir.glob("*.md")):
        if _slug(path.stem) not in known:
            diseases.append(path.stem)
            known.add(_slug(path.stem))

    logger.info("Backfilling %d diseases with %d workers (backend=openai-responses, model=%s)",
                len(diseases), args.workers, config.generation_model)

    done: list[str] = []
    failed: dict[str, str] = {}
    lock = threading.Lock()

    today = dt.date.today().isoformat()

    def _fresh_today(path: Path) -> bool:
        """Already regenerated today by this backend — don't pay twice on restart."""
        if not path.exists():
            return False
        head = path.read_text(encoding="utf-8")[:600]
        return f"date: '{today}'" in head or f"date: {today}" in head

    def process(disease: str) -> None:
        en_path = en_dir / f"{disease}.md"
        if not _fresh_today(en_path):
            generate_report(disease, output_dir=en_dir, config=config,
                            overwrite=True, backend="openai-responses", ledger=ledger)
        client = LLMClient(config)
        translate_file(en_dir / f"{disease}.md", fr_dir,
                       source_lang="en", target_lang="fr",
                       provider="llm", client=client, force=True)
        ledger.record(
            kind="translate", disease=disease, model=config.translation_model,
            input_tokens=client.total_input_tokens,
            output_tokens=client.total_output_tokens,
            cost_usd=estimate_cost(config.translation_model,
                                   client.total_input_tokens, client.total_output_tokens),
        )

    def run_pass(targets: list[str]) -> None:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(process, d): d for d in targets}
            for future in as_completed(futures):
                disease = futures[future]
                try:
                    future.result()
                    with lock:
                        done.append(disease)
                        failed.pop(disease, None)
                    logger.info("DONE %d/%d: %s", len(done), len(diseases), disease)
                except Exception as exc:  # noqa: BLE001
                    with lock:
                        failed[disease] = str(exc)[:200]
                    logger.exception("FAILED %s", disease)

    run_pass(diseases)
    if failed:
        logger.info("Retrying %d failure(s): %s", len(failed), sorted(failed))
        run_pass(sorted(failed))

    summary = {
        "finished": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "generated": len(done),
        "failed": failed,
        "month_spend_usd": ledger.month_total(),
    }
    Path("backfill_summary.json").write_text(json.dumps(summary, indent=2))
    logger.info("BACKFILL DONE: %d ok, %d failed, month spend $%.2f",
                len(done), len(failed), summary["month_spend_usd"])


if __name__ == "__main__":
    main()
