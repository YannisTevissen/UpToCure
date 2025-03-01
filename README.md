# UpToCure

UpToCure is a platform designed to provide accessible information about rare diseases and medical research. It displays interactive medical research reports in multiple languages, making complex scientific information more accessible to the general public.

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

</div>


## 📁 Project Structure

```
UpToCure/
├── frontend/            # Web interface files (HTML, CSS, JS)
├── reports/             # Markdown reports organized by language
│   ├── en/              # English reports
│   └── fr/              # French reports
├── src/                 # Backend source code
│   ├── app.py           # Flask application
│   └── parser.py        # Markdown parsing logic
├── requirements.txt     # Python dependencies
├── pyproject.toml       # PDM project configuration
└── run.py               # Main entry point to run the application
reports_generator/       # Tools for generating and translating reports
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or later
- PDM (Python Dependency Manager) or pip

### Installation

#### Using PDM (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/UpToCure.git
   cd UpToCure
   ```

2. Install dependencies with PDM:
   ```bash
   pdm install
   ```

3. Run the application:
   ```bash
   pdm run run
   ```

4. For production deployment with Gunicorn:
   ```bash
   pdm run serve
   ```

5. Access the application in your browser at `http://localhost:8000`


## 📝 Adding Reports

Reports are stored as Markdown files in the `reports` directory, organized by language:

1. Create a Markdown file in the appropriate language folder (e.g., `reports/en/` for English)
2. Follow the template structure available in sample reports
3. The application will automatically detect and display new reports

## 🛠️ Reports Generator

The `reports_generator` directory contains tools for:
- Generating new reports from research papers using `reporter.py`
- Translating existing reports between languages using `translator.py`
- See `TRANSLATION.md` for detailed instructions on translation workflows

## 💻 Development

### Frontend

- Built with vanilla JavaScript, HTML, and CSS for maximum accessibility
- `frontend/styles.css`: Main stylesheet
- `frontend/script.js`: JavaScript functionality
- `frontend/localization.js`: Translation strings and localization utilities

### Backend

- Flask-based backend serving Markdown reports
- `src/app.py`: Flask application defining routes and API endpoints
- `src/parser.py`: Logic for parsing and processing Markdown reports

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📬 Contact

If you have any questions or suggestions, feel free to open an issue or contact me. All my contact information is available on my [website](https://yannistevissen.fr).
