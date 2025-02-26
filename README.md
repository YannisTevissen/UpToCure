# UpToCure

UpToCure is a platform for displaying and interacting with medical research reports in multiple languages.

## Features

- **Multi-language Support**: The platform supports multiple languages, including English and French.
- **Responsive Design**: The interface is fully responsive and works on all devices.
- **Interactive Reports**: Reports are displayed in an interactive carousel.
- **Language-specific Reports**: Reports are organized by language and can be translated using NLLB (No Language Left Behind) AI model.

## Project Structure

```
UpToCure/
├── frontend/          # Frontend HTML, CSS, and JavaScript
├── reports/           # Markdown reports organized by language
│   ├── en/            # English reports
│   ├── fr/            # French reports
│   └── ...            # Other language folders
├── reports_generator/ # Tools for generating and translating reports
├── src/               # Backend API code
└── README.md          # This file
```

## Getting Started

### Prerequisites

- Python 3.7+
- Web browser

### Running the Application

1. Start the backend API server:
   ```
   cd UpToCure/src
   python app.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

### Adding Reports

Reports are stored as Markdown files in the `reports/<language_code>` directory. For example, English reports are stored in `reports/en/`.

If a language directory is empty, a sample report will be automatically generated.

### Translating Reports

To translate reports from one language to another, use the translation tool:

```
cd reports_generator
python translator.py --source-lang en --target-lang fr
```

See the [Translation Documentation](reports_generator/TRANSLATION.md) for more details.

## Development

### Frontend

The frontend is built with HTML, CSS, and JavaScript. The main files are:

- `frontend/index.html`: The main page
- `frontend/methodology.html`: The methodology page
- `frontend/style.css`: CSS styles
- `frontend/script.js`: JavaScript code
- `frontend/localization.js`: Localization strings

### Backend

The backend is built with Python using Flask. The main files are:

- `src/app.py`: The main API server
- `src/parser.py`: Markdown parsing utilities

## License

This project is licensed under the MIT License - see the LICENSE file for details. 