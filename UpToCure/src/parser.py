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

import html as html_lib
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
# Markdown link: [visible text](url). Visible text may contain any character
# except `]`; the URL stops at the first `)` (no support for nested parens).
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
# Surviving emphasis markers and other inline cruft we strip from the plain
# text fallback (we don't try to render emphasis in summaries).
MD_INLINE_NOISE_RE = re.compile(r"[*_`]+")
SUMMARY_MAX_CHARS = 240

# Lines we skip when looking for the first real paragraph inside a chunk.
_SKIP_LINE_PREFIXES = ("#", "---", ">")


@dataclass
class Report:
    """Public representation of one report."""

    slug: str
    title: str
    date: str
    summary: str  # plain text, safe for meta tags / JSON-LD
    filename: str
    language: str
    content: str = ""
    metadata: dict = field(default_factory=dict)
    # HTML-rendered version of the summary for visible UI: markdown links
    # are converted to safe `<a>` tags; everything else is HTML-escaped.
    summary_html: str = ""

    def to_summary(self) -> dict:
        """Listing payload (no HTML content)."""
        return {
            "slug": self.slug,
            "title": self.title,
            "date": self.date,
            "summary": self.summary,
            "summary_html": self.summary_html,
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


def _first_paragraph(markdown_body: str) -> str:
    """Return the first real (non-heading) paragraph from a markdown body.

    Robust to chunks that mix a heading and a paragraph without a blank line in
    between (e.g. ``## Introduction\\n<paragraph>``): leading heading / HR /
    blockquote lines are skipped inside each chunk before the rest is joined
    back into a single line.
    """
    for chunk in markdown_body.split("\n\n"):
        lines = chunk.strip().split("\n")
        # Strip leading heading / HR / blockquote / blank lines.
        while lines and (not lines[0].strip() or lines[0].lstrip().startswith(_SKIP_LINE_PREFIXES)):
            lines.pop(0)
        text = "\n".join(lines).strip()
        if not text:
            continue
        # Skip pure list / bullet chunks: a paragraph that *opens* with a
        # bullet usually means the section has no prose intro yet.
        if text.lstrip().startswith(("- ", "* ", "• ", "+ ")):
            continue
        return re.sub(r"\s+", " ", text)
    return ""


def _safe_url(url: str) -> str | None:
    """Return an attribute-escaped URL if it uses a safe scheme, else None."""
    url = url.strip()
    if not re.match(r"^(https?:|mailto:|/)", url, re.IGNORECASE):
        return None
    return html_lib.escape(url, quote=True)


def _truncate_segment(text: str, limit: int) -> tuple[str, bool]:
    """Cut `text` at the last sentence or word boundary within `limit` chars.

    Returns (cut_text, was_truncated). The cut text never exceeds `limit`.
    """
    if len(text) <= limit:
        return text, False
    window = text[:limit].rstrip()
    # Prefer a sentence-ish break in the back half of the window.
    soft_floor = int(limit * 0.55)
    for sep in (". ", "; ", " — ", " – ", ", "):
        idx = window.rfind(sep)
        if idx >= soft_floor:
            return window[: idx + 1].rstrip(), True
    # Otherwise cut at the last whitespace, falling back to a hard slice.
    space = window.rfind(" ")
    cut = window[:space] if space > 0 else window
    return cut.rstrip(".,;:—– "), True


def _build_summary(raw_paragraph: str, limit: int = SUMMARY_MAX_CHARS) -> tuple[str, str]:
    """From a single markdown paragraph, produce ``(plain_text, html)``.

    - Markdown links are inlined as their visible text in the plain version and
      rendered as `<a>` tags (with safe ``target=_blank rel=...``) in the HTML
      version.
    - Both versions are smart-truncated at the same boundary so the visible
      length is consistent, with `…` appended when content is dropped.
    - Anything that isn't a markdown link is HTML-escaped in the HTML version
      so we never accidentally inject markup.
    """
    if not raw_paragraph:
        return "", ""

    raw = MD_INLINE_NOISE_RE.sub("", raw_paragraph)

    # Split into alternating text / link segments without overlap.
    segments: list[tuple[str, str, str | None]] = []
    cursor = 0
    for match in MD_LINK_RE.finditer(raw):
        if match.start() > cursor:
            segments.append(("text", raw[cursor : match.start()], None))
        segments.append(("link", match.group(1), match.group(2)))
        cursor = match.end()
    if cursor < len(raw):
        segments.append(("text", raw[cursor:], None))

    plain_parts: list[str] = []
    html_parts: list[str] = []
    visible = 0
    truncated = False

    for kind, text, url in segments:
        remaining = limit - visible
        if remaining <= 0:
            truncated = True
            break

        if len(text) <= remaining:
            plain_parts.append(text)
            html_parts.append(_render_segment(kind, text, url))
            visible += len(text)
            continue

        if kind == "link":
            # Don't render a half-cut link: drop it entirely and stop here.
            truncated = True
            break

        cut, was_cut = _truncate_segment(text, remaining)
        if cut:
            plain_parts.append(cut)
            html_parts.append(_render_segment("text", cut, None))
        truncated = truncated or was_cut
        break

    plain = "".join(plain_parts)
    html = "".join(html_parts)
    if truncated:
        # Trim trailing whitespace + dangling punctuation only when we actually
        # cut content off, then add the ellipsis. If nothing was truncated we
        # preserve the source paragraph as-is (incl. its terminal period).
        plain = plain.rstrip(" .,;:—–") + " …"
        html = html.rstrip(" .,;:—–") + " …"
    return plain, html


def _render_segment(kind: str, text: str, url: str | None) -> str:
    """Render one prepared segment to its HTML form."""
    if kind == "link" and url:
        safe_url = _safe_url(url)
        escaped = html_lib.escape(text)
        if safe_url is None:
            return escaped
        return f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">{escaped}</a>'
    return html_lib.escape(text)


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

    body = body.replace("] (", "](")  # legacy fix for stray spaces in links

    summary_source = (meta.get("summary") or _first_paragraph(body)).strip()
    summary_text, summary_html = _build_summary(summary_source)

    html = markdown.markdown(body, extensions=MARKDOWN_EXTENSIONS)
    html = _force_external_links(html)

    filename = os.path.basename(path)
    slug = slugify(meta.get("slug") or os.path.splitext(filename)[0])

    return Report(
        slug=slug,
        title=title,
        date=date_str,
        summary=summary_text,
        summary_html=summary_html,
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
