from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Optional, Any
from datetime import datetime
import re
import os
import glob
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model for our report
class ReportModel(BaseModel):
    title: str
    content: str
    date: str
    filename: str

# Response model
class ReportsResponse(BaseModel):
    error: bool
    message: str
    reports: List[ReportModel]

# Markdown Parser
class MarkdownParser:
    """Simple Markdown Parser that converts markdown to HTML"""
    
    def parse(self, markdown: str) -> str:
        """Converts markdown text to HTML"""
        # Parse headers
        html = re.sub(r'^# (.+?)$', r'<h2>\1</h2>', markdown, flags=re.MULTILINE)
        html = re.sub(r'^## (.+?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+?)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        
        # Parse bold text
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        
        # Parse italic text
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        
        # Parse lists
        html = re.sub(r'^\s*[-*+]\s+(.+?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        
        # Wrap lists in ul tags (simple approach, might need refinement)
        html = re.sub(r'(<li>.+?</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
        
        # Parse horizontal rules
        html = re.sub(r'^---+$', r'<hr>', html, flags=re.MULTILINE)
        
        # Parse paragraphs (lines that don't start with a tag and aren't empty)
        lines = html.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not line.startswith('<') and not re.match(r'^</?[a-z]', line):
                lines[i] = f"<p>{line}</p>"
        
        html = '\n'.join(lines)
        return html
    
    def extract_metadata(self, markdown: str, filename: str) -> Dict[str, Any]:
        """Extracts title, content, and date from markdown"""
        # Find title (first h1)
        title_match = re.search(r'^# (.+?)$', markdown, re.MULTILINE)
        title = title_match.group(1) if title_match else "Untitled Document"
        
        # Find date using multiple patterns
        date = None
        date_patterns = [
            r'\*(?:.*?updated|date):\s*(.+?)\*',  # *Last updated: March 10, 2025*
            r'(?:Updated|Date):\s*([A-Za-z0-9, ]+)',  # Updated: March 10, 2025
            r'([A-Za-z]+ \d{1,2},? \d{4})',  # March 10, 2025
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'  # 10-03-2025 or 10/03/2025
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, markdown, re.IGNORECASE)
            if date_match:
                date = date_match.group(1).strip()
                break
        
        # Use current date if no date found
        if not date:
            date = datetime.now().strftime("%B %d, %Y")
        
        # Parse content
        content = self.parse(markdown)
        
        return {
            'title': title,
            'content': content,
            'date': date,
            'filename': filename
        }

def process_reports() -> Dict[str, Any]:
    """Process all markdown files in the reports directory"""
    # Use absolute path to reports directory from the project root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    reports_dir = os.path.join(base_dir, 'reports')
    
    print(f"Looking for reports in: {reports_dir}")
    
    parser = MarkdownParser()
    reports = []
    
    # Create reports directory if it doesn't exist
    if not os.path.isdir(reports_dir):
        try:
            os.makedirs(reports_dir)
            print(f"Created reports directory at {reports_dir}")
        except Exception as e:
            print(f"Error creating reports directory: {e}")
            return {
                'error': True,
                'message': f"Reports directory not found and could not be created: {str(e)}",
                'reports': []
            }
    
    # Get all files with .md extension
    md_files = glob.glob(os.path.join(reports_dir, '*.md'))
    
    print(f"Found {len(md_files)} markdown files")
    
    if not md_files:
        # Create a sample report if no files found
        sample_path = os.path.join(reports_dir, 'sample-report.md')
        try:
            with open(sample_path, 'w') as f:
                f.write("""# Sample Report: Introduction to UpToCure

Welcome to UpToCure! This is a sample report to demonstrate the markdown parsing capabilities.

**Key Features:**
* Parses markdown to HTML
* Extracts metadata like title and date
* Displays content in a responsive carousel

## Getting Started

To add your own reports, simply create markdown files in the `reports` directory.

*Last updated: April 15, 2025*
""")
            print(f"Created sample report at {sample_path}")
            md_files = [sample_path]  # Add the sample to our files list
        except Exception as e:
            print(f"Error creating sample report: {e}")
            # Important: We're returning an empty array, not raising a 404
            return {
                'error': False,  # Changed to false since this isn't a critical error
                'message': f"No markdown files found. Created a sample but encountered an error: {str(e)}",
                'reports': []
            }
    
    for file_path in md_files:
        filename = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            reports.append(parser.extract_metadata(content, filename))
            print(f"Successfully processed: {filename}")
        except Exception as e:
            print(f"Error processing file {filename}: {str(e)}")
            continue
    
    return {
        'error': False,
        'message': f"Successfully processed {len(reports)} reports",
        'reports': reports
    }

# API routes - define these before mounting static files
@app.get("/api")
def read_root():
    return {"message": "Welcome to UpToCure API"}

@app.get("/api/reports", response_model=ReportsResponse)
def get_reports():
    """Get all processed markdown reports"""
    result = process_reports()
    
    # Never return a 404 for empty reports, only for actual API errors
    if result['error']:
        # Check if this is a critical error that should result in a 404
        if "could not be created" in result['message'].lower():
            raise HTTPException(status_code=500, detail=result['message'])
        # For non-critical errors, continue with the response
    
    # Return the result, even if reports is empty
    return result

# Mount the frontend static files - do this last to ensure API routes take precedence
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')
if os.path.isdir(frontend_dir):
    print(f"Mounting frontend from: {frontend_dir}")
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    print(f"Warning: Frontend directory not found at {frontend_dir}") 