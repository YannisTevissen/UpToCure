"""UpToCure Flask application.

The server renders SEO-friendly pages (one URL per disease, per language) and
exposes a small JSON API consumed by the interactive carousel.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import random
import re
import sys
import threading
from collections import deque
from pathlib import Path
from urllib.parse import quote

from flask import (
    Flask,
    Response,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
)

from src import parser as report_parser
from src import seo
from src.i18n import (
    LANG_LOCALES,
    LANG_NAMES,
    SUPPORTED_LANGS,
    normalise_lang,
    t,
)

# ----- paths ------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
# Content lives outside the git checkout in production so that server-side
# report generation survives `git reset --hard` deploys. The in-repo folders
# remain the defaults for local development.
REPORTS_DIR = Path(os.environ.get("UPTOCURE_REPORTS_DIR", str(BASE_DIR / "reports")))
REQUESTS_DIR = Path(os.environ.get("UPTOCURE_REQUESTS_DIR", str(BASE_DIR / "disease_requests")))
# Pipeline state (cost ledger, last-run info) written by reports_generator/refresh.py.
STATE_DIR = Path(os.environ.get("UPTOCURE_STATE_DIR", str(REPORTS_DIR / ".state")))
IMAGES_DIR = FRONTEND_DIR / "images"
TEMPLATES_DIR = BASE_DIR / "templates"

REQUESTS_DIR.mkdir(parents=True, exist_ok=True)

# ----- logging ----------------------------------------------------------------

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("uptocure")

# ----- app --------------------------------------------------------------------

app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIR),
    static_url_path="",
    template_folder=str(TEMPLATES_DIR),
)

DISEASE_NAME_RE = re.compile(r"^[\w\s\-\'’.,()/&]{2,120}$", re.UNICODE)
ALLOWED_LANGS = set(SUPPORTED_LANGS)


# ----- template context -------------------------------------------------------

@app.context_processor
def _inject_globals():
    return {
        "site_name": "UpToCure",
        "site_url": seo.SITE_URL,
    }


def _base_context(lang: str, *, slug: str | None = None, search_query: str | None = None) -> dict:
    """Build common template context (i18n, alternates, JSON-LD)."""
    lang = normalise_lang(lang)
    alternates = seo.language_alternates(slug=slug)
    alt_url_en = next((a["url"] for a in alternates if a["lang"] == "en"), seo.home_url("en"))
    alt_url_fr = next((a["url"] for a in alternates if a["lang"] == "fr"), seo.home_url("fr"))
    return {
        "lang": lang,
        "locale": LANG_LOCALES.get(lang, "en_US"),
        "t": lambda key, **kw: t(key, lang, **kw),
        "alternates": alternates,
        "home_url": seo.home_url(lang),
        "alt_url_en": alt_url_en,
        "alt_url_fr": alt_url_fr,
        "jsonld_website": seo.jsonld_website(lang),
        "jsonld_organization": seo.jsonld_organization(),
        "search_query": search_query,
    }


# ----- headers ----------------------------------------------------------------

def _security_headers(response: Response) -> Response:
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "geolocation=(), microphone=(), camera=()",
    )
    return response


def _cache(response: Response, *, seconds: int) -> Response:
    response.headers["Cache-Control"] = f"public, max-age={seconds}, stale-while-revalidate=60"
    return response


@app.after_request
def _apply_default_headers(response: Response) -> Response:
    return _security_headers(response)


# ----- HTML pages -------------------------------------------------------------

RECENT_BADGE_DAYS = 14


def _recent_slugs(reports) -> set[str]:
    """Slugs of reports updated within the last RECENT_BADGE_DAYS days."""
    cutoff = (dt.date.today() - dt.timedelta(days=RECENT_BADGE_DAYS)).isoformat()
    return {r.slug for r in reports if (seo._iso_date(r.date) or "") >= cutoff}


def _featured_reports(reports, recent_slugs: set[str], limit: int = 5):
    """Prefer recently updated reports; fill from the alpha list if needed."""
    recent = [r for r in reports if r.slug in recent_slugs]
    recent.sort(key=lambda r: seo._iso_date(r.date) or "", reverse=True)
    featured = recent[:limit]
    if len(featured) < limit:
        seen = {r.slug for r in featured}
        for report in reports:
            if report.slug in seen:
                continue
            featured.append(report)
            if len(featured) >= limit:
                break
    return featured


def _index_letters(reports) -> list[str]:
    letters: list[str] = []
    seen: set[str] = set()
    for report in reports:
        title = (report.title or "").strip()
        letter = title[0].upper() if title else "#"
        if letter not in seen:
            seen.add(letter)
            letters.append(letter)
    return letters


def _render_home(lang: str):
    reports = report_parser.list_reports(str(REPORTS_DIR), lang)
    recent = _recent_slugs(reports)
    ctx = _base_context(lang)
    ctx.update(
        reports=reports,
        recent_slugs=recent,
        featured_reports=_featured_reports(reports, recent),
        index_letters=_index_letters(reports),
        jsonld_list=seo.jsonld_item_list(reports, lang),
    )
    response = Response(render_template("home.html", **ctx))
    return _cache(response, seconds=300)


@app.route("/")
def home_en():
    return _render_home("en")


@app.route("/fr/")
def home_fr():
    return _render_home("fr")


@app.route("/methodology")
@app.route("/methodology.html")  # legacy
def methodology_en():
    ctx = _base_context("en")
    return _cache(Response(render_template("methodology.html", **ctx)), seconds=86400)


@app.route("/fr/methodology")
def methodology_fr():
    ctx = _base_context("fr")
    return _cache(Response(render_template("methodology.html", **ctx)), seconds=86400)


@app.route("/reports/<lang>/<slug>")
def report_page(lang: str, slug: str):
    lang = normalise_lang(lang)
    if lang not in ALLOWED_LANGS:
        abort(404)

    report = report_parser.get_report(str(REPORTS_DIR), lang, slug)
    if not report:
        abort(404)

    # Related: pick a deterministic-but-varied set of other reports.
    all_reports = [r for r in report_parser.list_reports(str(REPORTS_DIR), lang) if r.slug != slug]
    rng = random.Random(slug)
    related = rng.sample(all_reports, k=min(6, len(all_reports))) if all_reports else []

    other_lang = "fr" if lang == "en" else "en"
    other_lang_report = report_parser.get_report(str(REPORTS_DIR), other_lang, slug)
    other_url = seo.report_url(other_lang, slug) if other_lang_report else None
    other_title = other_lang_report.title if other_lang_report else None

    ctx = _base_context(lang, slug=slug)
    canonical = seo.report_url(lang, slug)
    published_iso = seo._iso_date(report.date)
    breadcrumb_items = [
        ("UpToCure", seo.home_url(lang)),
        (t("all_reports_heading", lang), seo.home_url(lang) + "#all-reports"),
        (report.title, canonical),
    ]
    ctx.update(
        report=report,
        canonical_url=canonical,
        published_iso=published_iso,
        modified_iso=published_iso,
        jsonld_report=seo.jsonld_report(report, lang),
        jsonld_breadcrumb=seo.jsonld_breadcrumb(breadcrumb_items),
        related=related[:6],
        other_language_url=other_url,
        other_language_code=other_lang,
        other_language_name=LANG_NAMES.get(other_lang, other_lang) + (f" — {other_title}" if other_title else ""),
    )
    return _cache(Response(render_template("report.html", **ctx)), seconds=900)


@app.route("/search")
def search_page():
    query = (request.args.get("q") or "").strip()
    lang = normalise_lang(request.args.get("lang"))
    all_reports = report_parser.list_reports(str(REPORTS_DIR), lang)

    results: list[report_parser.Report] = []
    if query:
        lowered = query.lower()
        results = [
            r for r in all_reports
            if lowered in r.title.lower() or lowered in (r.summary or "").lower()
        ]

    ctx = _base_context(lang, search_query=query)
    ctx.update(query=query, results=results, all_reports=all_reports)
    response = Response(render_template("search.html", **ctx))
    return _cache(response, seconds=300)


# ----- SEO infrastructure ----------------------------------------------------

@app.route("/robots.txt")
def robots_txt():
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /api/\n"
        "Disallow: /search?q=\n"
        f"Sitemap: {seo.SITE_URL}/sitemap.xml\n"
    )
    return Response(body, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap_xml():
    urls: list[dict] = []

    for lang in SUPPORTED_LANGS:
        urls.append({
            "loc": seo.home_url(lang),
            "changefreq": "daily",
            "priority": "1.0",
            "alternates": seo.language_alternates(),
        })
        urls.append({
            "loc": (seo.SITE_URL + ("/methodology" if lang == "en" else f"/{lang}/methodology")),
            "changefreq": "monthly",
            "priority": "0.4",
            "alternates": [],
        })
        for report in report_parser.list_reports(str(REPORTS_DIR), lang):
            urls.append({
                "loc": seo.report_url(lang, report.slug),
                "lastmod": seo._iso_date(report.date) or dt.date.today().isoformat(),
                "changefreq": "weekly",
                "priority": "0.8",
                "alternates": seo.language_alternates(slug=report.slug),
            })

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]
    for entry in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{entry['loc']}</loc>")
        if entry.get("lastmod"):
            lines.append(f"    <lastmod>{entry['lastmod']}</lastmod>")
        lines.append(f"    <changefreq>{entry['changefreq']}</changefreq>")
        lines.append(f"    <priority>{entry['priority']}</priority>")
        for alt in entry["alternates"]:
            lines.append(
                f'    <xhtml:link rel="alternate" hreflang="{alt["lang"]}" href="{alt["url"]}"/>'
            )
        lines.append("  </url>")
    lines.append("</urlset>")
    return Response("\n".join(lines), mimetype="application/xml")


# ----- RSS feed ----------------------------------------------------------------

def _rfc822(iso_date: str) -> str:
    try:
        parsed = dt.datetime.strptime(iso_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        parsed = dt.datetime.utcnow()
    return parsed.strftime("%a, %d %b %Y 00:00:00 +0000")


def _render_feed(lang: str):
    from xml.sax.saxutils import escape

    reports = report_parser.list_reports(str(REPORTS_DIR), lang)
    latest = sorted(reports, key=lambda r: seo._iso_date(r.date) or "", reverse=True)[:20]

    items = []
    for report in latest:
        url = seo.report_url(lang, report.slug)
        items.append(
            "    <item>\n"
            f"      <title>{escape(report.title)}</title>\n"
            f"      <link>{escape(url)}</link>\n"
            f"      <guid isPermaLink=\"true\">{escape(url)}</guid>\n"
            f"      <pubDate>{_rfc822(seo._iso_date(report.date))}</pubDate>\n"
            f"      <description>{escape(report.summary or '')}</description>\n"
            "    </item>"
        )

    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        f"    <title>UpToCure — {escape(t('all_reports_heading', lang))}</title>\n"
        f"    <link>{escape(seo.home_url(lang))}</link>\n"
        f"    <description>{escape(t('site_description', lang))}</description>\n"
        f"    <language>{lang}</language>\n"
        f'    <atom:link href="{escape(seo.site_url("/feed.xml" if lang == "en" else f"/{lang}/feed.xml"))}" rel="self" type="application/rss+xml"/>\n'
        + "\n".join(items) + "\n"
        "  </channel>\n"
        "</rss>\n"
    )
    return _cache(Response(body, mimetype="application/rss+xml"), seconds=900)


@app.route("/feed.xml")
def feed_en():
    return _render_feed("en")


@app.route("/fr/feed.xml")
def feed_fr():
    return _render_feed("fr")


# ----- legacy hash redirect --------------------------------------------------

@app.route("/_redirect/<slug>")
def _legacy_hash_redirect(slug):
    return redirect(f"/reports/en/{quote(slug)}", code=301)


# ----- static media -----------------------------------------------------------

@app.route("/images/<path:filename>")
def serve_image(filename):
    response = send_from_directory(IMAGES_DIR, filename)
    return _cache(response, seconds=60 * 60 * 24 * 7)


# ----- JSON API ---------------------------------------------------------------

@app.route("/healthz")
def healthz():
    return jsonify(status="ok", time=dt.datetime.utcnow().isoformat() + "Z")


@app.route("/api")
def api_root():
    return jsonify(name="UpToCure", version="2.1.0")


@app.route("/api/status")
def api_status():
    """Pipeline transparency: last refresh run and month-to-date spend."""
    payload: dict = {
        "reports": {
            lang: len(report_parser.list_reports(str(REPORTS_DIR), lang))
            for lang in SUPPORTED_LANGS
        },
    }

    last_run_path = STATE_DIR / "last_run.json"
    if last_run_path.exists():
        try:
            run = json.loads(last_run_path.read_text(encoding="utf-8"))
            payload["last_run"] = {
                "started": run.get("started"),
                "finished": run.get("finished"),
                "generated": len(run.get("generated") or []),
                "translated": len(run.get("translated") or []),
                "errors": len(run.get("errors") or []),
                "stopped_by_budget": run.get("stopped_by_budget", False),
            }
        except (json.JSONDecodeError, OSError):
            logger.exception("Unreadable last_run.json")

    ledger_path = STATE_DIR / "cost-ledger.json"
    if ledger_path.exists():
        try:
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            month = dt.date.today().strftime("%Y-%m")
            payload["month_spend_usd"] = (ledger.get(month) or {}).get("total_usd", 0.0)
        except (json.JSONDecodeError, OSError):
            logger.exception("Unreadable cost ledger")

    return _cache(jsonify(payload), seconds=300)


@app.route("/api/reports")
def reports_list():
    lang = request.args.get("lang", "en")
    if lang not in ALLOWED_LANGS:
        return jsonify(error=True, message=f"Unsupported language '{lang}'"), 400

    reports = report_parser.list_reports(str(REPORTS_DIR), lang)
    response = jsonify(
        error=False,
        language=lang,
        count=len(reports),
        reports=[r.to_summary() for r in reports],
    )
    return _cache(response, seconds=60)


@app.route("/api/reports/<lang>/<slug>")
def report_detail(lang: str, slug: str):
    if lang not in ALLOWED_LANGS:
        abort(404)

    report = report_parser.get_report(str(REPORTS_DIR), lang, slug)
    if not report:
        abort(404)

    response = jsonify(error=False, report=report.to_detail())
    return _cache(response, seconds=300)


# ----- request endpoint with token-bucket rate limit --------------------------

_RATE_LIMIT_PER_HOUR = int(os.environ.get("REQUEST_REPORT_HOURLY_LIMIT", "20"))
_rate_lock = threading.Lock()
_recent_requests: dict[str, deque[float]] = {}


def _rate_limit_ok(client_ip: str) -> bool:
    now = dt.datetime.utcnow().timestamp()
    window = 3600
    with _rate_lock:
        bucket = _recent_requests.setdefault(client_ip, deque())
        while bucket and bucket[0] < now - window:
            bucket.popleft()
        if len(bucket) >= _RATE_LIMIT_PER_HOUR:
            return False
        bucket.append(now)
    return True


@app.route("/api/request-report", methods=["POST"])
def request_report():
    payload = request.get_json(silent=True) or {}
    disease = (payload.get("disease") or "").strip()
    if not disease:
        return jsonify(success=False, message="Missing 'disease' field"), 400
    if not DISEASE_NAME_RE.match(disease):
        return jsonify(success=False, message="Invalid disease name"), 400

    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
    if not _rate_limit_ok(client_ip):
        return jsonify(success=False, message="Too many requests, please try again later"), 429

    record = {
        "disease": disease,
        "language": payload.get("language", "en"),
        "client_timestamp": payload.get("timestamp"),
        "server_timestamp": dt.datetime.utcnow().isoformat() + "Z",
        "client_ip": client_ip,
        "user_agent": request.headers.get("User-Agent", ""),
    }

    timestamp = dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    target = REQUESTS_DIR / f"request_{timestamp}.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Saved disease request for %r from %s", disease, client_ip)
    return jsonify(success=True, message="Request received")


# ----- error handlers ---------------------------------------------------------

@app.errorhandler(404)
def not_found(_e):
    # Serve JSON for API paths, HTML otherwise
    if request.path.startswith("/api/") or request.accept_mimetypes.best == "application/json":
        return jsonify(error=True, message="Not found"), 404
    lang = normalise_lang(request.args.get("lang") or request.path.split("/", 2)[1] if "/" in request.path else "en")
    if lang not in SUPPORTED_LANGS:
        lang = "en"
    suggestions = report_parser.list_reports(str(REPORTS_DIR), lang)[:10]
    ctx = _base_context(lang)
    ctx.update(suggestions=suggestions)
    return render_template("404.html", **ctx), 404


@app.errorhandler(500)
def server_error(_e):
    logger.exception("Unhandled server error")
    if request.path.startswith("/api/"):
        return jsonify(error=True, message="Internal server error"), 500
    return "Internal server error", 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
