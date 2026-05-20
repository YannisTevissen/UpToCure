import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def tmp_reports_dir(tmp_path, monkeypatch):
    """Create an isolated reports directory and point the app at it."""
    reports = tmp_path / "reports"
    (reports / "en").mkdir(parents=True)
    (reports / "fr").mkdir(parents=True)

    (reports / "en" / "Sample Disease.md").write_text(
        "---\n"
        "date: 2025-02-15\n"
        "summary: A short summary of the disease.\n"
        "model: gpt-5\n"
        "---\n"
        "# Sample Disease\n\n"
        "Recent research highlights several promising therapies.\n\n"
        "See [PubMed](https://pubmed.ncbi.nlm.nih.gov/) for more.\n",
        encoding="utf-8",
    )
    (reports / "fr" / "Sample Disease.md").write_text(
        "---\n"
        "date: 2025-02-15\n"
        "summary: Une courte synthèse de la maladie.\n"
        "---\n"
        "# Maladie d'exemple\n\nDe la recherche prometteuse.\n",
        encoding="utf-8",
    )

    from src import app as app_module
    from src import parser as parser_module

    parser_module.clear_cache()
    monkeypatch.setattr(app_module, "REPORTS_DIR", reports)
    requests = tmp_path / "disease_requests"
    requests.mkdir()
    monkeypatch.setattr(app_module, "REQUESTS_DIR", requests)
    monkeypatch.setattr(app_module, "_recent_requests", {})
    monkeypatch.setattr(app_module, "_RATE_LIMIT_PER_HOUR", 5)
    return reports


@pytest.fixture()
def client(tmp_reports_dir):
    from src.app import app
    app.config.update(TESTING=True)
    return app.test_client()
