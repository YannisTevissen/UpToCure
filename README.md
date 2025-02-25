# UpToCure

UpToCure is a specialized application focused on delivering up-to-date reports on ongoing research efforts to cure rare diseases. It uses AI to process and present the latest medical research in an accessible web interface with a responsive carousel.

![UpToCure Demo](frontend/images/demo.png)

## About UpToCure

UpToCure leverages artificial intelligence to generate comprehensive reports about rare disease research. While the system aims for accuracy, users should be aware that the AI-generated content may occasionally contain inaccuracies. Always refer to the original research sources provided in each report for the most precise information.

## Features

- 📝 AI-assisted generation of rare disease research reports
- 📊 Automated extraction of key information from medical research
- 🎠 Responsive carousel interface for browsing multiple reports
- 🔄 REST API for programmatic access to research reports
- 🔄 Auto-refresh capability to display the latest reports
- 🔧 Development tools for testing and extending functionality
- 🎨 Clean, accessible user interface for medical information
- 🤖 Advanced AI research agent for gathering the latest scientific information

## System Requirements

- Python 3.11 or higher (for the main application)
- Python 3.12 for the reports generator
- PDM (Python Dependency Manager)
- Modern web browser

## Quick Start

The easiest way to run UpToCure is using PDM:

```bash
pdm run run
```

This will:
1. Check and install required dependencies
2. Ensure the reports directory exists
3. Check for sample reports (create one if none exist)
4. Start the FastAPI server
5. Open your browser to view the application

## Reports Generator

UpToCure includes a separate `reports_generator` module that uses advanced AI techniques to automatically generate comprehensive research reports on rare diseases. The generator:

1. Uses the SmolAgents deep research agent to search and gather information from the web
2. Processes medical literature to extract relevant research data
3. Generates formatted markdown reports with proper citations
4. Outputs reports directly to the `reports` directory for immediate viewing in the application

To generate a new report:

```bash
cd reports_generator
pdm run report
```

This requires API keys for the AI services used (Claude or OpenAI) and search APIs, which should be set in the `.env` file.

## Adding Your Own Reports

You can add reports in two ways:

### 1. Using the AI Reports Generator

Use the reports_generator module to automatically create comprehensive reports on specified rare diseases.

### 2. Manual Creation

Create a markdown (.md) file in the `reports` directory and format it with:
- A title (using # at the beginning)
- Content about rare disease research (any markdown is supported)
- Optional date (using *Last updated: DATE* format)
- References to original research sources

Example:
```markdown
# Research Progress in Gaucher's Disease Treatment

This report summarizes recent advances in enzyme replacement therapy for Gaucher's disease.

**Key findings:**
* Improved delivery mechanisms for glucocerebrosidase
* New clinical trials showing enhanced outcomes in Type 1 patients

*Last updated: January 21, 2025*

[1] Smith et al. Journal of Rare Diseases (2024)
[2] Clinical Trials Database: NCT09876543
```

## Project Structure

```
UpToCure/
├── src/
│   └── app.py              # FastAPI application for serving reports
├── scripts/
│   └── run.py              # Application launcher
├── frontend/
│   ├── images/             # UI assets
│   ├── index.html          # Main interface
│   ├── methodology.html    # Explanation of our AI approach
│   ├── reports-fallback.json # Development fallback data
│   ├── script.js           # Frontend logic
│   └── styles.css          # Visual styling
├── reports/                # Markdown reports on rare diseases
├── pyproject.toml          # PDM project configuration
└── README.md               # This file

reports_generator/          # AI-powered reports generation module
├── reporter.py             # Main script for generating reports
├── smolagents_repo/        # Deep research agent framework
│   └── examples/
│       └── open_deep_research/ # Web research capabilities
├── downloads_folder/       # Temporary storage for research content
└── pyproject.toml          # Dependencies for the generator
```

## API Endpoints

- `GET /api/reports` - Retrieve all processed rare disease research reports
- `GET /` - View the frontend application

## Development

For manual setup:

1. Install PDM: `pip install pdm`
2. Setup the project: `pdm install`
3. Run the server: `pdm run run-backend`

## Testing the API

There are two ways to test the API:

1. Using your browser:
   - Start the application using `pdm run run`
   - Visit `http://localhost:8000/api/reports` in your browser

2. Using curl:
   ```bash
   curl -s http://localhost:8000/api/reports | jq
   ```

## Troubleshooting

- **No reports showing up?** Check that your markdown files are in the `reports` directory and formatted correctly.
- **Server won't start?** Ensure you have Python 3.11+ and PDM installed.
- **API errors?** Check the server logs for detailed error messages.
- **Reports generator errors?** Check API keys in the `.env` file and ensure Python 3.12 is installed.

## Disclaimer

The reports generated by UpToCure are created with an AI agent that can sometimes hallucinate or present inaccurate information. For precise medical information, please refer to the original research sources provided in each report. UpToCure is intended for informational purposes only and is not a substitute for professional medical advice.

## License

This project is open-source.

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/)
- [PDM](https://pdm.fming.dev/)
- [SmolAgents](https://github.com/smol-ai/agent) - AI research agent framework 