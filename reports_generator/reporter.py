#!/usr/bin/env python3
"""Generate a markdown research report for a single disease.

Uses smolagents' CodeAgent + WebSearchTool + visit_webpage tool, driven by the
configurable LLM client from `llm.py`. Front-matter is added so the website
can display canonical metadata (date, model, cost) without inferring it from
file timestamps.
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

from llm import LLMConfig

load_dotenv()

logger = logging.getLogger("reporter")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = REPO_ROOT / "UpToCure" / "reports" / "en"

PROMPT_TEMPLATE = """Today is {today}. Write a comprehensive, exhaustive review of \
all recent research efforts (2020 onward) aimed at curing {disease}.

Requirements:
- Search the web for peer-reviewed articles, clinical trials, preclinical \
studies, and innovative experimental therapies.
- Identify breakthroughs, emerging trends, methodologies, funding sources, \
and the leading institutions driving these efforts.
- Critically evaluate strengths and limitations of each approach.
- Write in accessible language for a broad audience while preserving \
technical accuracy.
- Cite every claim with a markdown link `[short title](url)` to the original \
source. Verify URLs resolve.
- Use plain paragraphs and headings up to four `#`. No tables, no images, \
minimal bullet points.
- Start the document with exactly:
# {disease}
"""


def _build_agent(model_id: str, api_base: str, api_key: str):
    """Lazy import smolagents so the file is importable without it installed."""
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


def _front_matter(disease: str, model_id: str) -> str:
    payload = {
        "title": disease,
        "date": dt.date.today().isoformat(),
        "model": model_id,
        "generator": "uptocure-reports-generator",
        "summary": f"Recent research efforts aimed at curing {disease}.",
    }
    return "---\n" + yaml.safe_dump(payload, sort_keys=False).strip() + "\n---\n\n"


def generate_report(
    disease: str,
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    config: LLMConfig | None = None,
    overwrite: bool = False,
) -> Path:
    """Generate a markdown report and return the path written."""
    config = config or LLMConfig.from_env()
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{disease}.md"
    if target.exists() and not overwrite:
        logger.info("Report already exists, skipping: %s (use --force to regenerate)", target)
        return target

    logger.info("Generating report for %r using model=%s", disease, config.generation_model)
    agent = _build_agent(
        model_id=config.generation_model,
        api_base=config.base_url,
        api_key=config.api_key,
    )

    prompt = PROMPT_TEMPLATE.format(today=dt.date.today().isoformat(), disease=disease)
    body = str(agent.run(prompt)).strip()

    if not body.startswith("# "):
        body = f"# {disease}\n\n{body}"

    content = _front_matter(disease, config.generation_model) + body + "\n"
    target.write_text(content, encoding="utf-8")
    logger.info("Wrote %s (%d bytes)", target, len(content))
    return target


# ---- CLI ---------------------------------------------------------------------

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Generate UpToCure research reports.")
    ap.add_argument("--disease", action="append", help="Disease name (repeatable)")
    ap.add_argument("--diseases-file", help="Path to a YAML file containing a `diseases:` list")
    ap.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
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
            generate_report(disease, output_dir=output_dir, overwrite=args.force)
        except Exception:
            logger.exception("Failed to generate report for %s", disease)


if __name__ == "__main__":
    main(sys.argv[1:])
