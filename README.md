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
│   ├── reports/{en,fr}/       ← Markdown reports (dev seed; production content lives outside git)
│   ├── disease_requests/      ← User-submitted requests (JSON files)
│   ├── tests/                 ← pytest suite
│   ├── scripts/smoke_test.sh  ← Local end-to-end smoke test
│   └── pyproject.toml
├── reports_generator/         ← Content pipeline (Python 3.11+)
│   ├── llm.py                 ← OpenAI-compatible client (works with local LLMs)
│   ├── backends.py            ← Pluggable research backends (smolagents / Responses / deep research)
│   ├── reporter.py            ← Generates one markdown report per disease
│   ├── translator.py          ← Translates reports between languages
│   ├── refresh.py             ← Scheduled self-update job (budget-capped)
│   ├── costs.py               ← Pricing table + monthly cost ledger
│   ├── benchmark_backends.py  ← Compare backends on the same diseases
│   ├── generate_and_translate.py
│   ├── diseases.yaml          ← Base catalog of diseases to publish
│   └── pyproject.toml
└── deploy/                    ← systemd units + server setup for the self-updating pipeline
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
| `GET`  | `/feed.xml` and `/fr/feed.xml` | RSS feed of the 20 most recently updated reports |
| `GET`  | `/robots.txt` | Allows everything except the JSON API and query-string search |
| `GET`  | `/healthz` | Liveness probe |
| `GET`  | `/api/status` | Pipeline status: last refresh run, report counts, month-to-date spend |
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
pdm run refresh -- --dry-run   # what the scheduled job would do
```

## Self-updating pipeline

The site updates itself: a systemd timer on the server runs
`reports_generator/refresh.py` daily. Each run:

1. **Ingests user requests** (`POST /api/request-report` JSON files): each
   candidate is validated with one cheap LLM call, deduplicated against the
   catalog, and accepted names are queued permanently.
2. **Selects work** — catalog diseases with no English report first, then the
   stalest reports older than `REFRESH_MAX_AGE_DAYS` (default 30), capped at
   `REFRESH_MAX_REPORTS_PER_RUN` (default 4) generations per run. Four per day
   keeps a ~100-disease catalog fresh on a monthly cycle.
3. **Generates and translates** within a hard budget: every LLM call is priced
   into a monthly ledger, and the run stops as soon as `MONTHLY_BUDGET_USD`
   (default $30) is reached. Token usage and cost are stamped into each
   report's front-matter.
4. **Publishes instantly** — reports are written to the content directory the
   Flask app serves from (`UPTOCURE_REPORTS_DIR`), no deploy needed.

Progress is visible at `/api/status`. Server setup lives in
[`deploy/README.md`](deploy/README.md).

### Research backends

`RESEARCH_BACKEND` (or `--backend`) selects how a report is researched:

| Backend | How it works | Cost/report (gpt-5.6-terra) |
|---------|--------------|------------------------------|
| `smolagents` | CodeAgent loop, free DuckDuckGo search + page fetches | ~$0.21 |
| `openai-responses` | One Responses API call with OpenAI's hosted `web_search` tool | ~$0.30–0.40 |
| `deep-research` | `o4-mini-deep-research` with autonomous search (`DEEP_RESEARCH_MAX_TOOL_CALLS`) | ~$0.40–0.90 |

`smolagents` works with any OpenAI-compatible provider (including local
models); the other two require OpenAI. `pdm run benchmark --disease "…"`
generates the same reports with several backends side by side into
`benchmark_output/` for comparison.

A three-disease benchmark (August 2026, `gpt-5.6-terra`) found both backends
produce fully template-compliant reports, but `openai-responses` cited
13–20 unique sources per report versus 7–8 for `smolagents`, at similar speed
and cost (~$0.25 vs ~$0.16) — so production uses `openai-responses`. Note:
`deep-research` models may require OpenAI organisation verification; the
backend is implemented but untested on unverified accounts.

### Choosing an LLM (cost-aware defaults)

All LLM calls go through `reports_generator/llm.py`, which speaks the OpenAI Chat Completions protocol. Set the following in `.env`:

| Variable | Purpose | Default |
|----------|---------|---------|
| `LLM_PROVIDER` | `openai` (default), `gemini`, `anthropic`, `ollama`, `vllm`, `lmstudio`, `custom` | `openai` |
| `LLM_BASE_URL` | Override the OpenAI-compatible base URL | provider default |
| `LLM_API_KEY` | Cross-provider API key | provider env var |
| `LLM_MODEL` | Model used for report generation | `gpt-5` |
| `LLM_TRANSLATION_MODEL` | Model used for translation | `gpt-5-nano` |
| `RESEARCH_BACKEND` | `smolagents`, `openai-responses`, `deep-research` | `smolagents` |
| `UPTOCURE_REPORTS_DIR` | Content root read by the app and written by the pipeline | `UpToCure/reports` |
| `MONTHLY_BUDGET_USD` | Hard monthly spend cap for the refresh job | `30` |

#### Local LLM example (Ollama)

```bash
ollama pull qwen2.5:32b-instruct      # or llama3.1:70b-instruct on a beefy box
LLM_PROVIDER=ollama \
LLM_MODEL=qwen2.5:32b-instruct \
LLM_TRANSLATION_MODEL=qwen2.5:7b-instruct \
pdm run generate-reports
```

#### Per-report cost (August 2026 prices)

A finished report is ~6 000 markdown tokens. The research phase typically consumes 30k–80k input tokens and produces 5k–8k output tokens.

| Pipeline component | Model | Tokens (typical) | Cost per report |
|--------------------|-------|------------------|-----------------|
| Research + generation (recommended) | `gpt-5.6-terra` ($2 in / $12 out per 1M) | 60k in / 7k out | **≈ $0.21** |
| Translation EN → FR (per language) | `gpt-5-nano` ($0.05 in / $0.40 out per 1M) | 7k in / 8k out | **≈ $0.004** |
| Alternative — frontier quality | `gpt-5.5` ($5 in / $30 out) | 60k in / 7k out | ≈ $0.51 |
| Alternative — ultra cheap (lower quality) | `gpt-5.6-luna` ($0.20 in / $1.20 out) | 60k in / 7k out | ≈ $0.02 |

With the recommended tier, a freshly generated report in English plus French costs roughly **$0.21**. Refreshing the full ~100-disease catalog once a month costs **≈ $21/month** (the `openai-responses` backend adds ~$0.10–0.20/report in hosted search fees), which is why `MONTHLY_BUDGET_USD` defaults to $30. The pricing table used by the ledger lives in `reports_generator/costs.py`.

#### Wiring a local LLM end-to-end

- **Generation**: use `RESEARCH_BACKEND=smolagents` with `LLM_PROVIDER=ollama` and pick a 30B+ model — anything smaller will struggle with the agent loop. The web search and page fetch tools (`DuckDuckGoSearchTool`, `VisitWebpageTool`) work without an external API key.
- **Translation**: any 7B+ multilingual instruct model is fine. The `translate_lines` helper batches lines and protects the markdown structure.

## Deployment

`.github/workflows/deploy.yml`:

1. On every PR and push: lint with ruff, run pytest, run the live smoke test.
2. On push to `main`: SSH into the EC2 host, `git fetch && git reset --hard origin/main`, `pdm install --prod` (app + generator), install/enable the `uptocure-refresh` systemd units, reload the `uptocure` systemd unit, then poll `/healthz` for up to 30 seconds and fail the job if it doesn't come back healthy.

In production the markdown content lives **outside** the git checkout
(`UPTOCURE_REPORTS_DIR=/var/lib/uptocure/reports`) so deploys never clobber
server-generated reports. One-time server setup is documented in
[`deploy/README.md`](deploy/README.md).

## License

MIT — see [`LICENSE`](LICENSE).
