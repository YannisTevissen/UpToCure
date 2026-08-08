#!/usr/bin/env python3
"""Generate a markdown research report for a single disease.

Research is delegated to a pluggable backend (see `backends.py`): the original
smolagents agent loop, the OpenAI Responses API with the hosted web_search
tool, or an OpenAI deep-research model. Front-matter records date, model,
backend, token usage and estimated cost so the website and the budget ledger
can rely on it.
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from backends import BACKENDS, ResearchResult, run_research
from costs import CostLedger
from llm import LLMConfig

load_dotenv()

logger = logging.getLogger("reporter")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


REPO_ROOT = Path(__file__).resolve().parent.parent
REPORTS_ROOT = Path(
    os.environ.get("UPTOCURE_REPORTS_DIR", str(REPO_ROOT / "UpToCure" / "reports"))
)
DEFAULT_OUTPUT_DIR = REPORTS_ROOT / "en"

PROMPT_TEMPLATE = """Today is {today}. You are writing a research report for the \
UpToCure website on recent efforts (2020 to today) aimed at curing {disease}.

Every report on this site MUST follow the exact same structure so readers can \
compare diseases at a glance. Deviations from the template below are not \
acceptable.

# Mandatory document structure

The document MUST start with the title line, followed by the nine sections \
below, in this exact order, using these exact headings (no renaming, no \
reordering, no extra top-level sections, no missing sections):

1. `# {disease}`  (the very first line of the document)
2. `## Overview` — Plain-language summary of {disease}: what it is, who it \
affects, typical prognosis, and the current standard of care. 1–2 paragraphs.
3. `## Scope of Recent Research (2020–present)` — Short framing paragraph \
describing how active the field is, the dominant research questions, and how \
close the community is to a curative therapy. 1 paragraph.
4. `## Major Breakthroughs and Emerging Therapies` — The most important recent \
findings, grouped by therapeutic strategy (e.g. gene therapy, gene editing, \
small molecules, cell therapy, RNA therapeutics). 3–6 paragraphs.
5. `## Clinical Trials and Experimental Approaches` — Notable ongoing or \
recently completed trials, phase, sponsor, and reported outcomes when \
available. 1–3 paragraphs.
6. `## Methodologies and Scientific Approaches` — How researchers are \
investigating cures (model systems, delivery vehicles, biomarkers, platforms). \
1–2 paragraphs.
7. `## Leading Institutions and Funding` — Universities, hospitals, biotech \
companies, foundations, and government agencies driving the field, with \
representative funding amounts or programs when known. 1–2 paragraphs.
8. `## Strengths, Limitations, and Challenges` — Critical evaluation: what is \
working, what is not, safety/efficacy/access issues, open scientific \
questions. 1–2 paragraphs.
9. `## Outlook and Future Directions` — Honest forward-looking assessment of \
how close a cure is and what milestones to watch. 1 paragraph.
10. `## References` — Bulleted list of every source cited in the document. \
Each bullet uses the format `- [Short descriptive title](URL) — Author or \
publisher, year.` No duplicates.

# Content requirements

- Search the web for peer-reviewed articles, clinical trials, preclinical \
studies, and innovative experimental therapies published from 2020 onward. \
Prefer primary sources (PubMed, NEJM, Nature, Cell, Lancet, ClinicalTrials.gov, \
NIH, EMA, reputable patient foundations) over blog posts.
- Cite EVERY factual claim inline using a markdown link `[short title](url)` \
pointing to the original source. Verify each URL is a real, resolving page \
before including it; never fabricate links.
- Every URL used inline MUST also appear once in the final `## References` \
section, and vice versa.
- Write in accessible language for a broad, non-specialist audience while \
preserving technical accuracy. Define jargon on first use.
- Use plain paragraphs by default. Headings may go up to four `#`. No tables, \
no images, no horizontal rules. Bullet points are only allowed inside the \
`## References` section and, sparingly, when listing 3+ parallel items \
(e.g. trial names, drug names) within sections 4 or 5.
- Do not include a YAML front matter block — it is added automatically.
- Do not include any text before the `# {disease}` line or after the final \
reference bullet.
"""


def build_prompt(disease: str) -> str:
    return PROMPT_TEMPLATE.format(today=dt.date.today().isoformat(), disease=disease)


def _front_matter(disease: str, result: ResearchResult) -> str:
    payload = {
        "title": disease,
        "date": dt.date.today().isoformat(),
        "model": result.model,
        "backend": result.backend,
        "generator": "uptocure-reports-generator",
        "summary": f"Recent research efforts aimed at curing {disease}.",
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "search_calls": result.search_calls,
        "cost_usd": result.cost_usd,
    }
    return "---\n" + yaml.safe_dump(payload, sort_keys=False).strip() + "\n---\n\n"


def generate_report(
    disease: str,
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    config: LLMConfig | None = None,
    overwrite: bool = False,
    backend: str | None = None,
    ledger: CostLedger | None = None,
) -> Path:
    """Generate a markdown report and return the path written."""
    config = config or LLMConfig.from_env()
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{disease}.md"
    if target.exists() and not overwrite:
        logger.info("Report already exists, skipping: %s (use --force to regenerate)", target)
        return target

    logger.info(
        "Generating report for %r (model=%s, backend=%s)",
        disease, config.generation_model, backend or "env default",
    )
    result = run_research(build_prompt(disease), config, backend=backend)

    body = result.markdown
    if not body.startswith("# "):
        body = f"# {disease}\n\n{body}"

    content = _front_matter(disease, result) + body + "\n"
    target.write_text(content, encoding="utf-8")

    ledger = ledger or CostLedger()
    month_total = ledger.record(
        kind="generate",
        disease=disease,
        model=result.model,
        backend=result.backend,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        search_calls=result.search_calls,
        cost_usd=result.cost_usd,
    )
    logger.info(
        "Wrote %s (%d bytes, ~$%.3f, month-to-date $%.2f)",
        target, len(content), result.cost_usd, month_total,
    )
    return target


# ---- CLI ---------------------------------------------------------------------

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Generate UpToCure research reports.")
    ap.add_argument("--disease", action="append", help="Disease name (repeatable)")
    ap.add_argument("--diseases-file", help="Path to a YAML file containing a `diseases:` list")
    ap.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    ap.add_argument("--backend", choices=BACKENDS, default=None,
                    help="Research backend (default: RESEARCH_BACKEND env or smolagents)")
    ap.add_argument("--force", action="store_true", help="Overwrite existing reports")
    args = ap.parse_args(argv)

    diseases: list[str] = []
    if args.diseases_file:
        with open(args.diseases_file, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        diseases.extend(data.get("diseases") or [])
    if args.disease:
        diseases.extend(args.disease)
    if not diseases:
        ap.error("Provide --disease or --diseases-file")

    output_dir = Path(args.output_dir)
    for disease in diseases:
        try:
            generate_report(disease, output_dir=output_dir, overwrite=args.force,
                            backend=args.backend)
        except Exception:
            logger.exception("Failed to generate report for %s", disease)


if __name__ == "__main__":
    main(sys.argv[1:])
