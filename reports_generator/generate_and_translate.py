#!/usr/bin/env python3
"""End-to-end pipeline: generate English reports then translate them.

Reads `diseases.yaml` for the list of diseases and target languages. Each
disease is generated only if its English markdown file is missing (use
`--force` to regenerate). Each translation is only produced if the matching
language file is missing (again, `--force` overrides).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from llm import LLMClient, LLMConfig
from reporter import generate_report
from translator import translate_file

load_dotenv()

logger = logging.getLogger("pipeline")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORTS_ROOT = REPO_ROOT / "UpToCure" / "reports"
DEFAULT_CONFIG = Path(__file__).resolve().parent / "diseases.yaml"


def _load_config(path: Path) -> tuple[list[str], list[str]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    diseases = [d for d in (data.get("diseases") or []) if d]
    languages = [l for l in (data.get("target_languages") or []) if l and l != "en"]
    return diseases, languages


def run_pipeline(
    config_path: Path = DEFAULT_CONFIG,
    *,
    force_generate: bool = False,
    force_translate: bool = False,
    skip_generation: bool = False,
    skip_translation: bool = False,
    only_disease: str | None = None,
) -> None:
    diseases, languages = _load_config(config_path)
    if only_disease:
        diseases = [d for d in diseases if d.lower() == only_disease.lower()]
        if not diseases:
            logger.error("Disease %r not present in %s", only_disease, config_path)
            sys.exit(1)

    en_dir = REPORTS_ROOT / "en"
    en_dir.mkdir(parents=True, exist_ok=True)

    llm_config = LLMConfig.from_env()
    llm_client = LLMClient(llm_config)

    logger.info(
        "Pipeline starting (provider=%s, gen=%s, translate=%s, diseases=%d, langs=%s)",
        llm_config.provider, llm_config.generation_model,
        llm_config.translation_model, len(diseases), languages,
    )

    for disease in diseases:
        if not skip_generation:
            try:
                generate_report(
                    disease, output_dir=en_dir, config=llm_config, overwrite=force_generate,
                )
            except Exception:
                logger.exception("Failed to generate report for %s", disease)
                continue

        if skip_translation:
            continue

        source_file = en_dir / f"{disease}.md"
        if not source_file.exists():
            logger.warning("Source missing, cannot translate: %s", source_file)
            continue

        for lang in languages:
            try:
                translate_file(
                    source_file,
                    REPORTS_ROOT / lang,
                    source_lang="en",
                    target_lang=lang,
                    provider="llm",
                    client=llm_client,
                    force=force_translate,
                )
            except Exception:
                logger.exception("Failed to translate %s -> %s", disease, lang)

    logger.info("Pipeline complete")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--force-generate", action="store_true")
    ap.add_argument("--force-translate", action="store_true")
    ap.add_argument("--skip-generation", action="store_true")
    ap.add_argument("--skip-translation", action="store_true")
    ap.add_argument("--only", help="Only run for this disease name (must be in the YAML)")
    args = ap.parse_args(argv)
    run_pipeline(
        Path(args.config),
        force_generate=args.force_generate,
        force_translate=args.force_translate,
        skip_generation=args.skip_generation,
        skip_translation=args.skip_translation,
        only_disease=args.only,
    )


if __name__ == "__main__":
    main()
