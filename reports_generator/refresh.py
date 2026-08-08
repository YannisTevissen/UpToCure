#!/usr/bin/env python3
"""Scheduled refresh job: keeps the published reports fresh within a budget.

Designed to run unattended (systemd timer / cron) on the server. Each run:

1. Ingests user requests from the disease-requests directory: each candidate
   is validated with one cheap LLM call, deduplicated against the catalog, and
   accepted names are persisted to `requested-diseases.yaml` in the state dir.
2. Selects work in priority order: catalog diseases with no English report,
   then the stalest English reports older than REFRESH_MAX_AGE_DAYS, capped at
   REFRESH_MAX_REPORTS_PER_RUN generations per run.
3. Generates reports (skipping, then stopping, once MONTHLY_BUDGET_USD is hit)
   and translates every English report that is missing or older than its
   translation in the target languages.
4. Writes `last_run.json` to the state dir for the website's status endpoint.

Environment:
    UPTOCURE_REPORTS_DIR         content root (default: repo UpToCure/reports)
    UPTOCURE_REQUESTS_DIR        user requests (default: repo UpToCure/disease_requests)
    UPTOCURE_STATE_DIR           ledger + state (default: <reports>/.state)
    REFRESH_MAX_REPORTS_PER_RUN  generations per run (default 4)
    REFRESH_MAX_AGE_DAYS         regenerate reports older than this (default 30)
    MONTHLY_BUDGET_USD           hard cap on month spend (default 30)
    RESEARCH_BACKEND             smolagents | openai-responses | deep-research
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import re
import sys
import unicodedata
from pathlib import Path

import yaml
from dotenv import load_dotenv

from costs import CostLedger, estimate_cost, monthly_budget_usd
from llm import LLMClient, LLMConfig
from reporter import REPORTS_ROOT, generate_report
from translator import translate_file

load_dotenv()

logger = logging.getLogger("refresh")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

REPO_ROOT = Path(__file__).resolve().parent.parent
DISEASES_YAML = Path(__file__).resolve().parent / "diseases.yaml"
REQUESTS_DIR = Path(
    os.environ.get("UPTOCURE_REQUESTS_DIR", str(REPO_ROOT / "UpToCure" / "disease_requests"))
)

FRONT_MATTER_DATE_RE = re.compile(r"^date:\s*['\"]?(\d{4}-\d{2}-\d{2})", re.MULTILINE)
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.strip())
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")
    return _SLUG_RE.sub("-", ascii_only.lower()).strip("-")


def _report_date(path: Path) -> dt.date:
    """Front-matter date if present, file mtime otherwise."""
    try:
        head = path.read_text(encoding="utf-8")[:2000]
        match = FRONT_MATTER_DATE_RE.search(head)
        if match:
            return dt.date.fromisoformat(match.group(1))
    except (OSError, ValueError):
        pass
    return dt.date.fromtimestamp(path.stat().st_mtime)


# ----- catalog -------------------------------------------------------------------

def load_catalog(state_dir: Path) -> tuple[list[str], list[str]]:
    """Catalog diseases (yaml + accepted user requests) and target languages."""
    data = yaml.safe_load(DISEASES_YAML.read_text(encoding="utf-8")) or {}
    diseases = [d for d in (data.get("diseases") or []) if d]
    languages = [lang for lang in (data.get("target_languages") or []) if lang and lang != "en"]

    requested_path = state_dir / "requested-diseases.yaml"
    if requested_path.exists():
        requested = yaml.safe_load(requested_path.read_text(encoding="utf-8")) or {}
        known = {_slug(d) for d in diseases}
        for name in requested.get("diseases") or []:
            if name and _slug(name) not in known:
                diseases.append(name)
                known.add(_slug(name))
    return diseases, languages


def _save_requested(state_dir: Path, names: list[str]) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / "requested-diseases.yaml"
    existing = []
    if path.exists():
        existing = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("diseases") or []
    known = {_slug(d) for d in existing}
    for name in names:
        if _slug(name) not in known:
            existing.append(name)
            known.add(_slug(name))
    path.write_text(
        yaml.safe_dump({"diseases": existing}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


# ----- user request ingestion ------------------------------------------------------

_VALIDATION_SYSTEM = (
    "You curate the disease catalog of UpToCure, a website about medical research "
    "toward cures for rare and serious diseases. Given a user-submitted candidate, "
    "decide whether it names a real, recognized human disease or medical condition "
    "(not a joke, brand, person, or gibberish). Reply with ONLY a JSON object: "
    '{"valid": true/false, "canonical_name": "Proper English Disease Name"}.'
)


def ingest_requests(client: LLMClient, catalog: list[str], state_dir: Path,
                    ledger: CostLedger) -> list[str]:
    """Validate pending request files; return newly accepted disease names."""
    if not REQUESTS_DIR.is_dir():
        return []
    pending = sorted(REQUESTS_DIR.glob("request_*.json"))
    if not pending:
        return []

    processed_dir = REQUESTS_DIR / "processed"
    processed_dir.mkdir(exist_ok=True)
    known = {_slug(d) for d in catalog}
    accepted: list[str] = []
    tokens_before = (client.total_input_tokens, client.total_output_tokens)

    for path in pending:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            candidate = (record.get("disease") or "").strip()
        except (json.JSONDecodeError, OSError):
            logger.exception("Unreadable request file %s", path.name)
            path.rename(processed_dir / path.name)
            continue

        verdict: dict = {}
        if candidate and _slug(candidate) not in known:
            try:
                raw = client.chat(
                    [
                        {"role": "system", "content": _VALIDATION_SYSTEM},
                        {"role": "user", "content": f"Candidate: {candidate}"},
                    ],
                    model=client.config.translation_model,
                    temperature=0.0,
                )
                match = re.search(r"\{.*\}", raw, re.DOTALL)
                verdict = json.loads(match.group(0)) if match else {}
            except Exception:  # noqa: BLE001 - keep the file for the next run
                logger.exception("Validation failed for %r, retrying next run", candidate)
                continue

        name = (verdict.get("canonical_name") or "").strip()
        if verdict.get("valid") and name:
            if _slug(name) not in known:
                accepted.append(name)
                known.add(_slug(name))
                logger.info("Accepted request %r -> %r", candidate, name)
            else:
                logger.info("Request %r already in catalog", candidate)
        else:
            logger.info("Rejected request %r", candidate)
        path.rename(processed_dir / path.name)

    if accepted:
        _save_requested(state_dir, accepted)

    in_tokens = client.total_input_tokens - tokens_before[0]
    out_tokens = client.total_output_tokens - tokens_before[1]
    if in_tokens or out_tokens:
        ledger.record(
            kind="moderation",
            disease=f"{len(pending)} request(s)",
            model=client.config.translation_model,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            cost_usd=estimate_cost(client.config.translation_model, in_tokens, out_tokens),
        )
    return accepted


# ----- work selection ---------------------------------------------------------------

def select_generations(diseases: list[str], en_dir: Path, *, max_age_days: int,
                       limit: int) -> list[str]:
    """Missing reports first, then the stalest ones beyond max_age_days."""
    missing = [d for d in diseases if not (en_dir / f"{d}.md").exists()]

    cutoff = dt.date.today() - dt.timedelta(days=max_age_days)
    stale = [
        (d, _report_date(en_dir / f"{d}.md"))
        for d in diseases
        if (en_dir / f"{d}.md").exists() and _report_date(en_dir / f"{d}.md") <= cutoff
    ]
    stale.sort(key=lambda item: item[1])

    selected = missing + [d for d, _ in stale]
    return selected[:limit]


def select_translations(diseases: list[str], reports_root: Path,
                        languages: list[str]) -> list[tuple[str, str]]:
    """(disease, lang) pairs whose translation is missing or older than the EN source."""
    en_dir = reports_root / "en"
    pairs: list[tuple[str, str]] = []
    for disease in diseases:
        src = en_dir / f"{disease}.md"
        if not src.exists():
            continue
        for lang in languages:
            dst = reports_root / lang / f"{disease}.md"
            if not dst.exists() or _report_date(dst) < _report_date(src):
                pairs.append((disease, lang))
    return pairs


# ----- main -----------------------------------------------------------------------

def run(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-reports", type=int,
                    default=int(os.environ.get("REFRESH_MAX_REPORTS_PER_RUN", "4")))
    ap.add_argument("--max-age-days", type=int,
                    default=int(os.environ.get("REFRESH_MAX_AGE_DAYS", "30")))
    ap.add_argument("--backend", default=None,
                    help="Research backend override (default: RESEARCH_BACKEND env)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Only report what would be done")
    args = ap.parse_args(argv)

    reports_root = REPORTS_ROOT
    en_dir = reports_root / "en"
    en_dir.mkdir(parents=True, exist_ok=True)

    ledger = CostLedger()
    state_dir = ledger.state_dir
    budget = monthly_budget_usd()

    config = LLMConfig.from_env()
    client = LLMClient(config)

    started = dt.datetime.now(dt.timezone.utc)
    summary: dict = {
        "started": started.isoformat(timespec="seconds"),
        "generated": [],
        "translated": [],
        "requests_accepted": [],
        "budget_usd": budget,
        "stopped_by_budget": False,
        "errors": [],
    }

    diseases, languages = load_catalog(state_dir)

    # Published reports missing from the catalog (renamed/legacy entries) must
    # keep refreshing and getting translated too.
    known = {_slug(d) for d in diseases}
    for path in sorted(en_dir.glob("*.md")):
        if _slug(path.stem) not in known:
            diseases.append(path.stem)
            known.add(_slug(path.stem))

    if not args.dry_run:
        summary["requests_accepted"] = ingest_requests(client, diseases, state_dir, ledger)
        if summary["requests_accepted"]:
            diseases, languages = load_catalog(state_dir)

    to_generate = select_generations(
        diseases, en_dir, max_age_days=args.max_age_days, limit=args.max_reports,
    )
    logger.info(
        "Catalog: %d diseases, %d to generate this run (budget $%.2f, spent $%.2f)",
        len(diseases), len(to_generate), budget, ledger.month_total(),
    )

    if args.dry_run:
        translations = select_translations(diseases, reports_root, languages)
        logger.info("Dry run. Would generate: %s", to_generate)
        logger.info("Dry run. Would translate: %d file(s)", len(translations))
        return 0

    for disease in to_generate:
        if ledger.month_total() >= budget:
            logger.warning("Monthly budget $%.2f reached, stopping generation", budget)
            summary["stopped_by_budget"] = True
            break
        try:
            generate_report(
                disease, output_dir=en_dir, config=config,
                overwrite=True, backend=args.backend, ledger=ledger,
            )
            summary["generated"].append(disease)
        except Exception as exc:  # noqa: BLE001 - keep the run going
            logger.exception("Failed to generate %s", disease)
            summary["errors"].append(f"generate {disease}: {exc}")

    for disease, lang in select_translations(diseases, reports_root, languages):
        if ledger.month_total() >= budget:
            logger.warning("Monthly budget $%.2f reached, stopping translation", budget)
            summary["stopped_by_budget"] = True
            break
        src = en_dir / f"{disease}.md"
        tokens_before = (client.total_input_tokens, client.total_output_tokens)
        try:
            translate_file(
                src, reports_root / lang,
                source_lang="en", target_lang=lang,
                provider="llm", client=client, force=True,
            )
            summary["translated"].append(f"{disease} ({lang})")
        except Exception as exc:  # noqa: BLE001 - keep the run going
            logger.exception("Failed to translate %s -> %s", disease, lang)
            summary["errors"].append(f"translate {disease} ({lang}): {exc}")
            continue
        in_tokens = client.total_input_tokens - tokens_before[0]
        out_tokens = client.total_output_tokens - tokens_before[1]
        ledger.record(
            kind="translate",
            disease=disease,
            model=config.translation_model,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            cost_usd=estimate_cost(config.translation_model, in_tokens, out_tokens),
        )

    summary["finished"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    summary["month_spend_usd"] = ledger.month_total()
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "last_run.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8",
    )
    logger.info(
        "Refresh complete: %d generated, %d translated, month spend $%.2f",
        len(summary["generated"]), len(summary["translated"]), summary["month_spend_usd"],
    )
    return 0


def main(argv=None) -> None:
    sys.exit(run(argv))


if __name__ == "__main__":
    main()
