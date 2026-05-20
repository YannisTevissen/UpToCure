"""Markdown parsing for UpToCure reports.

Produces structured metadata (title, slug, date, summary) plus parsed HTML
from a directory of markdown files organised by language.

Reports may optionally include YAML front-matter at the top of the file:

    ---
    date: 2025-02-25
    summary: Optional one-line summary shown in the listing.
    model: gpt-5
    cost_usd: 0.42
    ---

If the front-matter is missing, the file's modification time is used as the
date and the first paragraph after the H1 is used as the summary.
"""

from __future__ import annotations

import logging
import os
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from functools import lru_cache

import markdown
import yaml
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

MARKDOWN_EXTENSIONS = [
    "markdown.extensions.tables",
    "markdown.extensions.fenced_code",
    "markdown.extensions.codehilite",
    "markdown.extensions.smarty",
]

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
H1_RE = re.compile(r"^# (.+?)$", re.MULTILINE)
SLUG_STRIP_RE = re.compile(r"[^a-z0-9]+")


@dataclass
class Report:
    """Public representation of one report."""

    slug: str
    title: str
    date: str
    summary: str
    filename: str
    language: str
    content: str = ""
    metadata: dict = field(default_factory=dict)

    def to_summary(self) -> dict:
        """Listing payload (no HTML content)."""
        return {
            "slug": self.slug,
            "title": self.title,
            "date": self.date,
            "summary": self.summary,
            "filename": self.filename,
            "language": self.language,
            "metadata": self.metadata,
        }

    def to_detail(self) -> dict:
        """Full payload including parsed HTML."""
        data = self.to_summary()
        data["content"] = self.content
        return data


def slugify(value: str) -> str:
    """Lowercase, hyphenated slug suitable for URLs and deep links.

    Transliterates accented characters first (Alström → Alstrom) so URLs stay
    readable and SEO-friendly.
    """
    decomposed = unicodedata.normalize("NFKD", value.strip())
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")
    normalised = SLUG_STRIP_RE.sub("-", ascii_only.lower()).strip("-")
    return normalised or "report"


def _parse_front_matter(text: str) -> tuple[dict, str]:
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text
    try:
        meta = yaml.safe_load(match.group(1)) or {}
        if not isinstance(meta, dict):
            meta = {}
    except yaml.YAMLError as exc:
        logger.warning("Invalid YAML front-matter ignored: %s", exc)
        meta = {}
    return meta, text[match.end():]


def _force_external_links(html: str) -> str:
    """Make every anchor open in a new tab with safe rel attributes."""
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.find_all("a"):
        link["target"] = "_blank"
        link["rel"] = "noopener noreferrer"
    return str(soup)


def _extract_summary(markdown_body: str) -> str:
    """First non-heading paragraph, trimmed for use as a teaser."""
    for paragraph in markdown_body.split("\n\n"):
        text = paragraph.strip()
        if not text or text.startswith("#") or text.startswith("---"):
            continue
        cleaned = re.sub(r"\s+", " ", text)
        return cleaned[:280]
    return ""


def _format_date(value) -> str:
    if isinstance(value, datetime):
        return value.strftime("%B %d, %Y")
    if hasattr(value, "strftime"):  # datetime.date
        return value.strftime("%B %d, %Y")
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%B %d, %Y"):
            try:
                return datetime.strptime(value, fmt).strftime("%B %d, %Y")
            except ValueError:
                continue
        return value
    return ""


@lru_cache(maxsize=512)
def _parse_file(path: str, mtime_ns: int, language: str) -> Report:
    """Read + parse a single markdown file. Cached on (path, mtime)."""
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()

    meta, body = _parse_front_matter(raw)

    title_match = H1_RE.search(body)
    title = (meta.get("title") or (title_match.group(1) if title_match else "Untitled")).strip()

    date_value = meta.get("date")
    if not date_value:
        date_value = datetime.fromtimestamp(os.path.getmtime(path))
    date_str = _format_date(date_value)

    summary = (meta.get("summary") or _extract_summary(body)).strip()

    body = body.replace("] (", "](")  # legacy fix for stray spaces in links
    html = markdown.markdown(body, extensions=MARKDOWN_EXTENSIONS)
    html = _force_external_links(html)

    filename = os.path.basename(path)
    slug = slugify(meta.get("slug") or os.path.splitext(filename)[0])

    return Report(
        slug=slug,
        title=title,
        date=date_str,
        summary=summary,
        filename=filename,
        language=language,
        content=html,
        metadata={k: v for k, v in meta.items() if k not in {"title", "date", "summary", "slug"}},
    )


def _iter_markdown_files(directory: str) -> Iterable[str]:
    if not os.path.isdir(directory):
        return []
    return sorted(
        os.path.join(directory, name)
        for name in os.listdir(directory)
        if name.endswith(".md")
    )


def list_reports(reports_root: str, language: str) -> list[Report]:
    """Return all reports for a language, ordered by title."""
    lang_dir = os.path.join(reports_root, language)
    if not os.path.isdir(lang_dir):
        logger.info("Language directory missing: %s", lang_dir)
        return []

    reports: list[Report] = []
    for path in _iter_markdown_files(lang_dir):
        try:
            reports.append(_parse_file(path, os.stat(path).st_mtime_ns, language))
        except Exception:  # noqa: BLE001 - we log and skip individual files
            logger.exception("Failed to parse %s", path)
    reports.sort(key=lambda r: r.title.lower())
    return reports


def get_report(reports_root: str, language: str, slug: str) -> Report | None:
    """Look up one report by slug for a given language."""
    for report in list_reports(reports_root, language):
        if report.slug == slug:
            return report
    return None


def clear_cache() -> None:
    """Reset the parse cache (used in tests / hot-reload)."""
    _parse_file.cache_clear()


# ---- backwards-compatible helpers ----

def process_reports(reports_dir: str = "reports", lang: str = "en") -> list[dict]:
    """Legacy helper kept for any caller relying on dict output."""
    return [asdict(r) for r in list_reports(reports_dir, lang)]


def parse_markdown(markdown_content: str, links_in_new_tab: bool = True) -> str:
    """Parse a raw markdown string to HTML (used by tests and tools)."""
    html = markdown.markdown(markdown_content, extensions=MARKDOWN_EXTENSIONS)
    if links_in_new_tab:
        html = _force_external_links(html)
    return html
