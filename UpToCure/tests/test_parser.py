from src import parser as p


def test_slugify_handles_punctuation():
    assert p.slugify("Friedreich's Ataxia") == "friedreich-s-ataxia"
    assert p.slugify("Inflammatory Myopathy (IMAM)") == "inflammatory-myopathy-imam"


def test_slugify_transliterates_accents():
    assert p.slugify("Alström Syndrome") == "alstrom-syndrome"
    assert p.slugify("Mucopolysaccharidose Type II — Hunter") == "mucopolysaccharidose-type-ii-hunter"


def test_parse_markdown_adds_target_blank_to_links():
    html = p.parse_markdown("See [example](https://example.com)")
    assert 'target="_blank"' in html
    assert 'rel="noopener noreferrer"' in html


def test_list_reports_uses_front_matter(tmp_reports_dir):
    reports = p.list_reports(str(tmp_reports_dir), "en")
    assert len(reports) == 1
    report = reports[0]
    assert report.title == "Sample Disease"
    assert report.slug == "sample-disease"
    assert report.date == "February 15, 2025"
    assert report.summary == "A short summary of the disease."
    assert report.metadata["model"] == "gpt-5"
    assert 'target="_blank"' in report.content


def test_get_report_by_slug(tmp_reports_dir):
    report = p.get_report(str(tmp_reports_dir), "en", "sample-disease")
    assert report is not None
    assert "Recent research" in report.content


def test_list_reports_falls_back_to_mtime(tmp_path):
    reports_dir = tmp_path / "reports"
    (reports_dir / "en").mkdir(parents=True)
    (reports_dir / "en" / "no-frontmatter.md").write_text(
        "# Plain Title\n\nFirst paragraph.\n", encoding="utf-8"
    )
    p.clear_cache()
    reports = p.list_reports(str(reports_dir), "en")
    assert len(reports) == 1
    assert reports[0].title == "Plain Title"
    assert reports[0].summary == "First paragraph."
