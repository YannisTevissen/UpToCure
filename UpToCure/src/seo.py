"""SEO helpers: canonical URLs, hreflang, and JSON-LD structured data builders."""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from urllib.parse import quote

from src.i18n import DEFAULT_LANG, LANG_LOCALES, SUPPORTED_LANGS, t

SITE_URL = os.environ.get("SITE_URL", "https://uptocure.com").rstrip("/")
SITE_ORG_NAME = "UpToCure"


# ---- URL helpers -------------------------------------------------------------

def site_url(path: str = "") -> str:
    return f"{SITE_URL}{path}" if path.startswith("/") else f"{SITE_URL}/{path}"


def home_url(lang: str) -> str:
    return site_url("/") if lang == DEFAULT_LANG else site_url(f"/{lang}/")


def report_url(lang: str, slug: str) -> str:
    return site_url(f"/reports/{lang}/{quote(slug)}")


def language_alternates(slug: str | None = None) -> list[dict]:
    """Build hreflang link descriptors for a given page."""
    items = []
    for lang in SUPPORTED_LANGS:
        url = report_url(lang, slug) if slug else home_url(lang)
        items.append({"lang": lang, "url": url})
    items.append({"lang": "x-default", "url": items[0]["url"]})
    return items


# ---- JSON-LD builders --------------------------------------------------------

def _dumps(payload: dict | list) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def jsonld_website(lang: str) -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_ORG_NAME,
        "alternateName": t("site_tagline", lang),
        "url": SITE_URL,
        "description": t("site_description", lang),
        "inLanguage": list(SUPPORTED_LANGS),
        "publisher": {
            "@type": "Organization",
            "name": SITE_ORG_NAME,
            "url": SITE_URL,
            "logo": {"@type": "ImageObject", "url": site_url("/images/logo.png")},
        },
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": site_url("/search?q={search_term_string}"),
            },
            "query-input": "required name=search_term_string",
        },
    }
    return _dumps(payload)


def jsonld_organization() -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": SITE_ORG_NAME,
        "url": SITE_URL,
        "logo": site_url("/images/logo.png"),
        "sameAs": ["https://github.com/yannistevissen/UpToCure"],
    }
    return _dumps(payload)


def jsonld_breadcrumb(items: Iterable[tuple[str, str]]) -> str:
    """`items` is an iterable of (label, url) pairs in order."""
    payload = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": label, "item": url}
            for i, (label, url) in enumerate(items)
        ],
    }
    return _dumps(payload)


def jsonld_report(report, lang: str) -> str:
    """Build MedicalScholarlyArticle + MedicalCondition JSON-LD for a report."""
    url = report_url(lang, report.slug)
    payload = {
        "@context": "https://schema.org",
        "@type": ["MedicalScholarlyArticle", "MedicalWebPage"],
        "headline": report.title,
        "name": report.title,
        "description": report.summary or t("site_description", lang),
        "url": url,
        "inLanguage": LANG_LOCALES.get(lang, lang),
        "datePublished": report.metadata.get("date_iso") or _iso_date(report.date),
        "dateModified": report.metadata.get("updated") or report.metadata.get("date_iso") or _iso_date(report.date),
        "isAccessibleForFree": True,
        "audience": {"@type": "MedicalAudience", "audienceType": ["Patient", "Researcher"]},
        "publisher": {
            "@type": "Organization",
            "name": SITE_ORG_NAME,
            "url": SITE_URL,
            "logo": {"@type": "ImageObject", "url": site_url("/images/logo.png")},
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "about": {
            "@type": "MedicalCondition",
            "name": report.title,
        },
    }
    if report.metadata.get("model"):
        payload["creator"] = {"@type": "SoftwareApplication", "name": str(report.metadata["model"])}
    return _dumps(payload)


def jsonld_item_list(reports, lang: str) -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": t("all_reports_heading", lang),
        "numberOfItems": len(reports),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "url": report_url(lang, r.slug),
                "name": r.title,
            }
            for i, r in enumerate(reports)
        ],
    }
    return _dumps(payload)


def _iso_date(human_date: str) -> str:
    """Best-effort conversion of "February 15, 2025" -> "2025-02-15"."""
    import datetime as dt
    for fmt in ("%B %d, %Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(human_date, fmt).date().isoformat()
        except (ValueError, TypeError):
            continue
    return ""
