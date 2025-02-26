# UpToCure Report Translation

This feature allows you to automatically translate markdown reports from one language to another using the NLLB (No Language Left Behind) translation model.

## Prerequisites

- Python 3.12
- PDM package manager
- Required dependencies (installed via PDM)

## Installation

The translation feature is included in the `reports_generator` module. Make sure you have all dependencies installed:

```bash
cd reports_generator
pdm install
```

## Usage

### Basic Usage

To translate all English reports to French:

```bash
pdm run translate --target-lang fr
```

This will:
1. Find all markdown files in the `UpToCure/reports/en` directory
2. Translate each file using NLLB
3. Save the translated files in the `UpToCure/reports/fr` directory

### Command Line Options

The translation script supports several options:

```bash
pdm run translate --source-lang en --target-lang fr --model facebook/nllb-200-distilled-600M --file report.md
```

Parameters:

- `--source-lang`: Source language code (default: "en")
- `--target-lang`: Target language code (required)
- `--model`: NLLB model to use (default: "facebook/nllb-200-distilled-600M")
- `--file`: Translate a specific file only (optional)

### Supported Languages

The script supports the following language codes:

| Code | Language        | NLLB Code |
|------|-----------------|-----------|
| en   | English         | eng_Latn  |
| fr   | French          | fra_Latn  |
| es   | Spanish         | spa_Latn  |
| de   | German          | deu_Latn  |
| it   | Italian         | ita_Latn  |
| pt   | Portuguese      | por_Latn  |
| nl   | Dutch           | nld_Latn  |
| ru   | Russian         | rus_Cyrl  |
| zh   | Chinese (Simp.) | zho_Hans  |
| ja   | Japanese        | jpn_Jpan  |
| ar   | Arabic          | ara_Arab  |

You can also use NLLB-specific language codes directly (e.g., `cat_Latn` for Catalan).

## How It Works

The translation process:

1. **Parsing**: The script parses markdown files to identify headings, code blocks, URLs, and other elements that need special handling.
2. **Translation**: The content is translated using the NLLB model, maintaining markdown formatting.
3. **Output**: Translated files are saved with the same filename in the target language directory.

## Models

By default, the script uses the `facebook/nllb-200-distilled-600M` model, which is a smaller, distilled version of NLLB with good performance and reasonable resource requirements.

For higher quality translations (but slower performance and higher memory usage), you can use:
- `facebook/nllb-200-1.3B`
- `facebook/nllb-200-3.3B`

## Example

Translate all English reports to Spanish:

```bash
pdm run translate --target-lang es
```

Translate a specific report to German:

```bash
pdm run translate --target-lang de --file UpToCure/reports/en/gauchers-disease.md
```

## Notes

- The script preserves markdown formatting including headers, code blocks, and links.
- If a target file already exists, it will be skipped to prevent overwriting existing translations.
- The script handles large reports by splitting them into manageable chunks for translation.
- GPU acceleration is used if available, significantly improving translation speed. 