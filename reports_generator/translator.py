#!/usr/bin/env python3
"""Markdown report translator for UpToCure.

By default the translator uses the configurable LLM client from `llm.py`.
A `--provider deepl` flag is kept for backwards compatibility if a DeepL key
is set in DEEPL_API_KEY.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv
from tqdm import tqdm

from llm import LLMClient

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("translator")

LANG_NAMES = {
    "en": "English", "fr": "French", "es": "Spanish", "de": "German",
    "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "ru": "Russian",
    "zh": "Chinese (Simplified)", "ja": "Japanese", "ar": "Arabic",
    "pl": "Polish", "tr": "Turkish", "ko": "Korean", "uk": "Ukrainian",
}


def lang_name(code: str) -> str:
    return LANG_NAMES.get(code.lower(), code)


# ---- LLM-based translation ---------------------------------------------------

def translate_markdown_llm(content: str, src: str, tgt: str, client: LLMClient) -> str:
    lines = content.split("\n")
    translated = client.translate_lines(lines, lang_name(src), lang_name(tgt))
    return "\n".join(translated)


# ---- Optional DeepL fallback -------------------------------------------------

def translate_markdown_deepl(content: str, src: str, tgt: str) -> str:
    try:
        import deepl  # type: ignore
    except ImportError as exc:
        raise RuntimeError("DeepL provider requested but 'deepl' package not installed") from exc

    api_key = os.environ.get("DEEPL_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPL_API_KEY not set")

    translator = deepl.Translator(api_key)
    lines = content.split("\n")
    non_empty: list[tuple[int, str]] = [(i, line) for i, line in enumerate(lines) if line.strip()]
    if non_empty:
        results = translator.translate_text(
            [line for _, line in non_empty],
            source_lang=src.upper() if src.upper() != "AUTO" else None,
            target_lang=tgt.upper(),
            preserve_formatting=True,
            tag_handling="html",
        )
        if not isinstance(results, list):
            results = [results]
        for (idx, _), result in zip(non_empty, results):
            lines[idx] = result.text
    return "\n".join(lines)


# ---- file orchestration ------------------------------------------------------

def _find_source_files(source_dir: Path) -> list[Path]:
    if not source_dir.is_dir():
        return []
    return sorted(source_dir.glob("*.md"))


def translate_file(
    src_path: Path,
    target_dir: Path,
    *,
    source_lang: str,
    target_lang: str,
    provider: str = "llm",
    client: LLMClient | None = None,
    force: bool = False,
    translate_filename: bool = True,
) -> Path | None:
    target_dir.mkdir(parents=True, exist_ok=True)

    if translate_filename:
        stem = src_path.stem
        if provider == "llm":
            translated_stem = (client or LLMClient()).translate(
                stem, lang_name(source_lang), lang_name(target_lang)
            ).strip().strip(".")
        else:
            translated_stem = stem  # DeepL path keeps original to avoid extra calls
        target_path = target_dir / f"{translated_stem}.md"
    else:
        target_path = target_dir / src_path.name

    if target_path.exists() and not force:
        logger.info("Skip (exists): %s", target_path.name)
        return target_path

    logger.info("Translating %s -> %s", src_path.name, target_path.name)
    content = src_path.read_text(encoding="utf-8")

    if provider == "deepl":
        translated = translate_markdown_deepl(content, source_lang, target_lang)
    else:
        translated = translate_markdown_llm(content, source_lang, target_lang, client or LLMClient())

    target_path.write_text(translated, encoding="utf-8")
    return target_path


def translate_all(
    source_dir: Path,
    target_dir: Path,
    *,
    source_lang: str,
    target_lang: str,
    provider: str,
    force: bool,
) -> None:
    files = _find_source_files(source_dir)
    if not files:
        logger.warning("No markdown files in %s", source_dir)
        return
    client = LLMClient() if provider == "llm" else None
    for path in tqdm(files, desc=f"{source_lang}->{target_lang}"):
        try:
            translate_file(
                path, target_dir,
                source_lang=source_lang, target_lang=target_lang,
                provider=provider, client=client, force=force,
            )
        except Exception:
            logger.exception("Failed translating %s", path.name)


# ---- CLI ---------------------------------------------------------------------

def main(argv: Iterable[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Translate UpToCure markdown reports.")
    ap.add_argument("--source-lang", default="en")
    ap.add_argument("--target-lang", required=True)
    ap.add_argument("--source-dir", default=None, help="Directory containing source markdown files")
    ap.add_argument("--target-dir", default=None, help="Output directory (defaults under UpToCure/reports/<lang>)")
    ap.add_argument("--file", default=None, help="Translate a single file instead of a directory")
    ap.add_argument("--provider", choices=["llm", "deepl"], default="llm")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args(list(argv) if argv is not None else None)

    if args.debug:
        logger.setLevel(logging.DEBUG)

    repo_root = Path(__file__).resolve().parent.parent
    source_dir = Path(args.source_dir) if args.source_dir else repo_root / "UpToCure" / "reports" / args.source_lang
    target_dir = Path(args.target_dir) if args.target_dir else repo_root / "UpToCure" / "reports" / args.target_lang

    if args.file:
        src_path = Path(args.file)
        if not src_path.exists():
            src_path = source_dir / args.file
        if not src_path.exists():
            logger.error("File not found: %s", args.file)
            sys.exit(1)
        client = LLMClient() if args.provider == "llm" else None
        translate_file(
            src_path, target_dir,
            source_lang=args.source_lang, target_lang=args.target_lang,
            provider=args.provider, client=client, force=args.force,
        )
    else:
        translate_all(
            source_dir, target_dir,
            source_lang=args.source_lang, target_lang=args.target_lang,
            provider=args.provider, force=args.force,
        )


if __name__ == "__main__":
    main()
