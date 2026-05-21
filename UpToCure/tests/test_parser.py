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


def test_summary_extraction_skips_heading_without_blank_line(tmp_path):
    """Files that have `## Heading\\nParagraph` (no blank line between) should
    still surface the paragraph, not the next section."""
    reports_dir = tmp_path / "reports"
    (reports_dir / "en").mkdir(parents=True)
    (reports_dir / "en" / "fabry-style.md").write_text(
        "# Title\n\n## Introduction\n"
        "The real intro paragraph belongs here.\n\n"
        "## Other Section\nDifferent content.\n",
        encoding="utf-8",
    )
    p.clear_cache()
    [report] = p.list_reports(str(reports_dir), "en")
    assert report.summary == "The real intro paragraph belongs here."


def test_summary_inlines_markdown_links_in_plain_text(tmp_path):
    reports_dir = tmp_path / "reports"
    (reports_dir / "en").mkdir(parents=True)
    (reports_dir / "en" / "linky.md").write_text(
        "# Linky\n\nSee [PubMed](https://pubmed.ncbi.nlm.nih.gov/) for more.\n",
        encoding="utf-8",
    )
    p.clear_cache()
    [report] = p.list_reports(str(reports_dir), "en")
    # Plain summary used in meta tags: no markdown / no HTML, just visible text.
    assert report.summary == "See PubMed for more."
    # HTML summary used in visible UI: real anchor with safe attrs.
    assert '<a href="https://pubmed.ncbi.nlm.nih.gov/"' in report.summary_html
    assert 'target="_blank"' in report.summary_html
    assert 'rel="noopener noreferrer"' in report.summary_html


def test_summary_truncates_at_word_boundary_with_ellipsis(tmp_path):
    """Long summaries are cut at a sentence/word boundary and end with `…`,
    never mid-word."""
    long_para = (
        "Alkaptonuria is a rare inherited metabolic disorder caused by a "
        "deficiency of the enzyme homogentisate 1,2-dioxygenase, leading to "
        "the accumulation of homogentisic acid and resulting in ochronosis — "
        "a progressive darkening and brittle degeneration of connective "
        "tissues that affects joints, cartilage, and the spine over many "
        "decades of life."
    )
    reports_dir = tmp_path / "reports"
    (reports_dir / "en").mkdir(parents=True)
    (reports_dir / "en" / "long.md").write_text(
        f"# Long Disease\n\n{long_para}\n", encoding="utf-8",
    )
    p.clear_cache()
    [report] = p.list_reports(str(reports_dir), "en")
    # Must end with a horizontal ellipsis (one-char) following whitespace.
    assert report.summary.endswith(" …"), report.summary
    # No mid-word cut: every word in the summary (minus the trailing ellipsis)
    # is a prefix of a word in the source.
    prefix = report.summary.rstrip(" …")
    assert long_para.startswith(prefix[: prefix.rfind(" ")]) or prefix in long_para
    assert len(report.summary) <= p.SUMMARY_MAX_CHARS + 4  # + " …"


def test_summary_html_drops_unsafe_link_scheme(tmp_path):
    reports_dir = tmp_path / "reports"
    (reports_dir / "en").mkdir(parents=True)
    (reports_dir / "en" / "xss.md").write_text(
        "# XSS\n\nClick [here](javascript:alert(1)) for danger.\n",
        encoding="utf-8",
    )
    p.clear_cache()
    [report] = p.list_reports(str(reports_dir), "en")
    assert "javascript:" not in report.summary_html
    assert "<a " not in report.summary_html
    # The visible link text is still present.
    assert "Click here" in report.summary_html
