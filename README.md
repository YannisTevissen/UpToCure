# UpToCure

UpToCure is a platform that presents up-to-date, AI-generated research summaries on rare diseases. Reports are written by an LLM-powered agent, translated automatically, and served as a static-feeling website that is friendly to read and easy to share.

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

</div>

## Project layout

```
UpToCure/
├── UpToCure/                  ← the web application (Python 3.11+)
│   ├── src/
│   │   ├── app.py             ← Flask routes & API
│   │   ├── parser.py          ← Markdown → HTML, front-matter aware
│   │   ├── i18n.py            ← Server-side translations for SSR pages
│   │   └── seo.py             ← Sitemap + JSON-LD + hreflang helpers
│   ├── templates/             ← Jinja2 templates (home, report, search, 404, methodology)
│   ├── frontend/
│   │   ├── styles.css
│   │   ├── images/
│   │   └── js/                ← ES modules (config, i18n, api, carousel, share, request, main)
│   ├── reports/{en,fr}/       ← Published markdown reports
│   ├── disease_requests/      ← User-submitted requests (JSON files)
│   ├── tests/                 ← pytest suite
│   ├── scripts/smoke_test.sh  ← Local end-to-end smoke test
│   └── pyproject.toml
└── reports_generator/         ← Offline content pipeline (Python 3.11+)
    ├── llm.py                 ← OpenAI-compatible client (works with local LLMs)
    ├── reporter.py            ← Generates one markdown report per disease
    ├── translator.py          ← Translates reports between languages
    ├── generate_and_translate.py
    ├── diseases.yaml          ← Single source of truth for the diseases to publish
    └── pyproject.toml
```

## Running the website locally

```bash
cd UpToCure
pdm install -d
pdm run run                 # dev server on http://localhost:8000
pdm run serve               # gunicorn (3 workers) on :8000
pdm run test                # unit tests
pdm run smoke               # full smoke test (unit + live HTTP checks)
```

Override the port with `PORT=…`. Enable Flask debug mode with `FLASK_DEBUG=1`.

### URLs and routes

The site is structured to be discoverable: every report has its own server-rendered URL, plus there's the usual SEO infrastructure (sitemap, robots, structured data).

| Method | Path | Notes |
|--------|------|-------|
| `GET`  | `/` | English homepage (server-rendered list of every report) |
| `GET`  | `/fr/` | French homepage |
| `GET`  | `/reports/<lang>/<slug>` | Canonical per-disease page with structured data |
| `GET`  | `/methodology` and `/fr/methodology` | Methodology page |
| `GET`  | `/search?q=…&lang=…` | Server-rendered search results |
| `GET`  | `/sitemap.xml` | Generated dynamically from the published reports |
| `GET`  | `/robots.txt` | Allows everything except the JSON API and query-string search |
| `GET`  | `/healthz` | Liveness probe |
| `GET`  | `/api/reports?lang=en\|fr` | JSON list of report metadata (no HTML body) |
| `GET`  | `/api/reports/<lang>/<slug>` | JSON for one report (used by the carousel) |
| `POST` | `/api/request-report` | Rate-limited (20/hour/IP) submission |

Responses include `Cache-Control` headers and the usual security headers
(`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, etc.).

### SEO

Each disease has a real, indexable URL like `https://uptocure.com/reports/en/cystic-fibrosis`. The HTML returned for that URL contains:

- A descriptive `<title>` and per-page meta description (the report's summary).
- A `<link rel="canonical">` pointing to itself.
- `<link rel="alternate" hreflang>` for every supported language (and the same-slug French translation), plus `x-default`.
- Open Graph and Twitter card meta with the title, description, and the site image.
- A `<meta property="article:published_time">` derived from the report's front-matter date.
- Four JSON-LD blocks:
  - `WebSite` with a `SearchAction` pointing at `/search`
  - `Organization` (UpToCure + GitHub `sameAs`)
  - `MedicalScholarlyArticle` + `MedicalWebPage` describing the report, with `about` → `MedicalCondition` and `creator` → the LLM that generated it
  - `BreadcrumbList` for the navigation trail
- Breadcrumbs in the visible HTML.
- A "More disease reports" section with internal links to related reports (deterministic per slug so it's stable for crawlers).

The homepage server-renders the **full alphabetical list** of every report as plain `<a>` links so crawlers discover the catalog without executing JavaScript. The interactive carousel is added on top for human visitors and uses the same canonical URLs.

`/sitemap.xml` is generated on demand from the markdown directory: it lists each language's homepage, every report (with `lastmod`), and includes `xhtml:link rel="alternate" hreflang="…"` between language variants. `/robots.txt` references it.

Slugs are transliterated (so `Alström Syndrome` → `/reports/en/alstrom-syndrome`) for readable URLs.

To configure the public domain, set `SITE_URL=https://uptocure.com` in the environment — it's used for every canonical / OG / sitemap URL.

## Adding or editing the list of diseases

The canonical list lives in [`reports_generator/diseases.yaml`](reports_generator/diseases.yaml). Add or comment out entries there, then run the pipeline.

## Generating reports

```bash
cd reports_generator
cp .env.example .env        # fill in your provider keys
pdm install
pdm run generate-reports    # uses diseases.yaml, skips existing files
pdm run -- report --disease "Pompe Disease"
pdm run -- translate --target-lang fr
```

### Choosing an LLM (cost-aware defaults)

All LLM calls go through `reports_generator/llm.py`, which speaks the OpenAI Chat Completions protocol. Set the following in `.env`:

| Variable | Purpose | Default |
|----------|---------|---------|
| `LLM_PROVIDER` | `openai` (default), `gemini`, `anthropic`, `ollama`, `vllm`, `lmstudio`, `custom` | `openai` |
| `LLM_BASE_URL` | Override the OpenAI-compatible base URL | provider default |
| `LLM_API_KEY` | Cross-provider API key | provider env var |
| `LLM_MODEL` | Model used for report generation | `gpt-5` |
| `LLM_TRANSLATION_MODEL` | Model used for translation | `gpt-5-nano` |

#### Local LLM example (Ollama)

```bash
ollama pull qwen2.5:32b-instruct      # or llama3.1:70b-instruct on a beefy box
LLM_PROVIDER=ollama \
LLM_MODEL=qwen2.5:32b-instruct \
LLM_TRANSLATION_MODEL=qwen2.5:7b-instruct \
pdm run generate-reports
```

#### Per-report cost (May 2026 prices)

A finished report is ~6 000 markdown tokens. The agent loop typically consumes 30k–80k input tokens and produces 5k–8k output tokens across all internal steps.

| Pipeline component | Model | Tokens (typical) | Cost per report |
|--------------------|-------|------------------|-----------------|
| Deep-research generation | `gpt-5` ($1.25 in / $10 out per 1M) | 60k in / 7k out | **≈ $0.14** |
| Translation EN → FR (per language) | `gpt-5-nano` ($0.05 in / $0.40 out per 1M) | 7k in / 8k out | **≈ $0.003** |
| Alternative — frontier quality | `claude-sonnet-4.6` ($3 in / $15 out) | 60k in / 7k out | ≈ $0.29 |
| Alternative — ultra cheap (lower quality) | `gemini-2.5-flash-lite` ($0.10 in / $0.40 out) | 60k in / 7k out | ≈ $0.009 |

So with the defaults, a freshly generated report in English plus French costs roughly **$0.15**. Updating the whole catalog (~25 diseases × 2 languages) is therefore well under **$5**.

#### Wiring a local LLM end-to-end

- **Generation**: `smolagents` + `OpenAIServerModel` is already plumbed in `reporter.py`. Just set `LLM_PROVIDER=ollama` and pick a 30B+ model — anything smaller will struggle with the agent loop. The web search and page fetch tools (`DuckDuckGoSearchTool`, `VisitWebpageTool`) work without an external API key.
- **Translation**: any 7B+ multilingual instruct model is fine. The `translate_lines` helper batches lines and protects the markdown structure.

See the analysis in `docs/` or the original chat for caveats around model quality vs. medical-research accuracy.

## Deployment

`.github/workflows/deploy.yml`:

1. On every PR and push: lint with ruff, run pytest, run the live smoke test.
2. On push to `main`: SSH into the EC2 host, `git fetch && git reset --hard origin/main`, `pdm install --prod`, reload the `uptocure` systemd unit, then poll `/healthz` for up to 30 seconds and fail the job if it doesn't come back healthy.

## License

MIT — see [`LICENSE`](LICENSE).
