import json
import re

import pytest

# ---- HTML home page (server rendered) ---------------------------------------

def test_home_page_renders_with_report_list(client):
    res = client.get("/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    # Server-rendered list of every report (key SEO win)
    assert "Sample Disease" in html
    assert "/reports/en/sample-disease" in html
    # Per-page structured data
    assert '"@type": "WebSite"' in html
    assert '"SearchAction"' in html
    assert '"@type": "ItemList"' in html


def test_home_page_french(client):
    res = client.get("/fr/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert 'lang="fr"' in html
    assert "/reports/fr/sample-disease" in html


def test_home_has_hreflang_alternates(client):
    res = client.get("/")
    html = res.data.decode("utf-8")
    assert 'hreflang="en"' in html
    assert 'hreflang="fr"' in html
    assert 'hreflang="x-default"' in html


# ---- Report page (server rendered) ------------------------------------------

def test_report_page_renders(client):
    res = client.get("/reports/en/sample-disease")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "<h1>Sample Disease</h1>" in html
    assert "Recent research highlights several promising therapies" in html
    # Canonical URL + breadcrumbs
    assert '<link rel="canonical"' in html
    assert "/reports/en/sample-disease" in html
    # Structured data
    assert '"MedicalScholarlyArticle"' in html
    assert '"MedicalCondition"' in html
    assert '"BreadcrumbList"' in html
    # Article meta
    assert '<meta property="og:type" content="article">' in html
    assert 'article:published_time' in html
    # Language alternate to French
    assert 'hreflang="fr"' in html


def test_report_404(client):
    res = client.get("/reports/en/not-a-real-disease")
    assert res.status_code == 404


def test_french_report_page(client):
    res = client.get("/reports/fr/sample-disease")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert 'lang="fr"' in html
    assert "Maladie d'exemple" in html or "Maladie d&#39;exemple" in html


# ---- robots / sitemap -------------------------------------------------------

def test_robots_txt(client):
    res = client.get("/robots.txt")
    assert res.status_code == 200
    body = res.data.decode("utf-8")
    assert "Sitemap:" in body
    assert "Disallow: /api/" in body


def test_sitemap_xml(client):
    res = client.get("/sitemap.xml")
    assert res.status_code == 200
    assert res.mimetype == "application/xml"
    body = res.data.decode("utf-8")
    assert "<urlset" in body
    # Both languages of every report are listed
    assert "/reports/en/sample-disease" in body
    assert "/reports/fr/sample-disease" in body
    # Hreflang attributes
    assert 'hreflang="en"' in body
    assert 'hreflang="fr"' in body
    # Home pages
    assert "/fr/" in body


# ---- Search -----------------------------------------------------------------

def test_search_empty_lists_all_reports(client):
    res = client.get("/search")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "Sample Disease" in html


def test_search_with_query(client):
    res = client.get("/search?q=sample")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "Sample Disease" in html


def test_search_noindex_when_query(client):
    res = client.get("/search?q=sample")
    html = res.data.decode("utf-8")
    assert 'name="robots" content="noindex' in html


def test_search_no_results(client):
    res = client.get("/search?q=xyznomatch")
    html = res.data.decode("utf-8")
    assert "No reports" in html or "Aucun rapport" in html


# ---- 404 page ---------------------------------------------------------------

def test_404_page_is_html(client):
    res = client.get("/this-does-not-exist")
    assert res.status_code == 404
    html = res.data.decode("utf-8")
    assert "404" in html
    # Should suggest other reports
    assert "Sample Disease" in html


# ---- Structured data validity ----------------------------------------------

JSONLD_RE = re.compile(
    r'<script type="application/ld\+json">(.*?)</script>',
    re.DOTALL,
)


@pytest.mark.parametrize("path", ["/", "/fr/", "/reports/en/sample-disease"])
def test_jsonld_is_valid(client, path):
    res = client.get(path)
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    blocks = JSONLD_RE.findall(html)
    assert blocks, f"No JSON-LD found on {path}"
    for block in blocks:
        # Each block must parse as valid JSON
        json.loads(block)


# ---- Legacy compatibility ---------------------------------------------------

def test_legacy_methodology_html_still_works(client):
    res = client.get("/methodology.html")
    assert res.status_code == 200


def test_methodology_page(client):
    res = client.get("/methodology")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "Methodology" in html or "Méthodologie" in html
