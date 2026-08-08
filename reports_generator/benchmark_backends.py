#!/usr/bin/env python3
"""Benchmark the research backends on the same diseases.

Generates one report per (disease, backend) into benchmark_output/<backend>/
and prints a comparison table: tokens, search calls, estimated cost, section
compliance against the mandatory template, and reference counts. Nothing is
recorded in the cost ledger and nothing is published.

Usage:
    pdm run benchmark --disease "Krabbe Disease" --backend smolagents --backend openai-responses
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import time
from pathlib import Path

from dotenv import load_dotenv

from backends import BACKENDS, run_research
from llm import LLMConfig
from reporter import build_prompt

load_dotenv()

logger = logging.getLogger("benchmark")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

OUTPUT_DIR = Path(__file__).resolve().parent / "benchmark_output"

REQUIRED_HEADINGS = [
    "## Overview",
    "## Scope of Recent Research (2020–present)",
    "## Major Breakthroughs and Emerging Therapies",
    "## Clinical Trials and Experimental Approaches",
    "## Methodologies and Scientific Approaches",
    "## Leading Institutions and Funding",
    "## Strengths, Limitations, and Challenges",
    "## Outlook and Future Directions",
    "## References",
]

MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")


def analyse(markdown: str) -> dict:
    headings_present = sum(1 for h in REQUIRED_HEADINGS if h in markdown)
    links = MD_LINK_RE.findall(markdown)
    refs_section = markdown.split("## References", 1)
    ref_bullets = 0
    if len(refs_section) == 2:
        ref_bullets = len(re.findall(r"^- \[", refs_section[1], re.MULTILINE))
    unique_urls = {url for _, url in links}
    return {
        "chars": len(markdown),
        "headings": f"{headings_present}/{len(REQUIRED_HEADINGS)}",
        "inline_links": len(links),
        "unique_urls": len(unique_urls),
        "reference_bullets": ref_bullets,
    }


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--disease", action="append", required=True)
    ap.add_argument("--backend", action="append", choices=BACKENDS,
                    help="Backends to compare (default: all)")
    args = ap.parse_args(argv)

    backends = args.backend or list(BACKENDS)
    config = LLMConfig.from_env()
    rows: list[dict] = []

    for disease in args.disease:
        prompt = build_prompt(disease)
        for backend in backends:
            out_dir = OUTPUT_DIR / backend
            out_dir.mkdir(parents=True, exist_ok=True)
            target = out_dir / f"{disease}.md"
            logger.info("=== %s via %s ===", disease, backend)
            start = time.time()
            try:
                result = run_research(prompt, config, backend=backend)
            except Exception as exc:  # noqa: BLE001 - record and continue
                logger.exception("%s failed for %s", backend, disease)
                rows.append({"disease": disease, "backend": backend, "error": str(exc)[:120]})
                continue
            elapsed = time.time() - start
            target.write_text(result.markdown + "\n", encoding="utf-8")
            rows.append({
                "disease": disease,
                "backend": backend,
                "model": result.model,
                "seconds": round(elapsed),
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "search_calls": result.search_calls,
                "cost_usd": result.cost_usd,
                **analyse(result.markdown),
            })

    print(json.dumps(rows, indent=2))
    (OUTPUT_DIR / "results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    logger.info("Reports and results.json written to %s", OUTPUT_DIR)


if __name__ == "__main__":
    main()
