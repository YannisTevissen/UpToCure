# UpToCure — translation

Reports are translated by the `translator.py` script. By default it uses the
OpenAI-compatible LLM client (`llm.py`), but a DeepL fallback is kept for
backwards compatibility.

## Quick start

```bash
cd reports_generator
cp .env.example .env       # add your provider key (OPENAI_API_KEY, …)
pdm install
pdm run translate --target-lang fr             # all English reports → French
pdm run -- translate --target-lang es --file "UpToCure/reports/en/Cystic Fibrosis.md"
pdm run -- translate --target-lang fr --provider deepl   # DeepL fallback
```

The script:

1. Scans `UpToCure/reports/<source-lang>/` for `*.md` files.
2. Translates every non-empty line, batching up to 25 lines per request to
   amortise overhead, while preserving markdown syntax (headings, lists, URLs,
   code spans, link targets).
3. Writes the translated file under `UpToCure/reports/<target-lang>/`.
4. Skips already-existing target files unless `--force` is passed.

## CLI

```
--source-lang   Source language code (default: en)
--target-lang   Target language code (required)
--source-dir    Override the source directory
--target-dir    Override the target directory
--file PATH     Translate a single file instead of an entire directory
--provider      llm (default) | deepl
--force         Overwrite existing translations
--debug         Verbose logging
```

## Choosing a translation model

Configure these env vars (see `.env.example`):

```
LLM_PROVIDER=openai            # or gemini, ollama, vllm, lmstudio, anthropic, custom
LLM_TRANSLATION_MODEL=gpt-5-nano
```

| Model | Cost (in / out per 1M tokens) | Notes |
|-------|-------------------------------|-------|
| `gpt-5-nano` (OpenAI) | $0.05 / $0.40 | Default. Excellent EN↔FR/ES/DE. |
| `gemini-2.5-flash-lite` | $0.10 / $0.40 | Cheapest, broad language coverage. |
| `qwen2.5:7b-instruct` (local via Ollama) | free | Good for EU languages on a laptop. |
| `nllb-200-1.3B` (HF transformers) | free | Pure MT model; needs a wrapper, not currently included. |

## Provider fallback (DeepL)

If you already have a DeepL subscription, set `DEEPL_API_KEY` in `.env` and
pass `--provider deepl`. The script will preserve markdown formatting via
`tag_handling="html"` and the standard `preserve_formatting=True` flag.

## Languages supported

Any language the chosen model can produce. Common codes are mapped to
human-readable names internally, but you can also pass arbitrary codes — the
prompt simply embeds the code if it isn't known.
