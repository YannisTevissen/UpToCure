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
        
        # Parse h4 headers
        html = re.sub(r'^#### (.+?)$', r'<h5>\1</h5>', html, flags=re.MULTILINE)
        
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
        
        # Parse links
        html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)
        
        # Parse tables (more complex approach)
        # First, we need to detect and process multi-line tables
        def process_table_content(table_content):
            rows = table_content.strip().split('\n')
            html_rows = []
            header_processed = False
            
            # Clean up rows and remove empty ones
            rows = [row.strip() for row in rows if row.strip()]
            
            # Identify if there are any separator rows (rows with mostly dashes)
            separator_indices = []
            for i, row in enumerate(rows):
                # Check if this is a separator row (contains mainly dashes and pipes)
                if re.match(r'^\|[\s\-|]+\|$', row) or re.search(r'\|[\s\-|]+\|', row):
                    separator_indices.append(i)
            
            # Process rows
            current_table_part = "header" if separator_indices else "body"
            
            for i, row in enumerate(rows):
                # Skip separator rows
                if i in separator_indices:
                    # Switch from header to body after first separator
                    if current_table_part == "header":
                        current_table_part = "body"
                    continue
                
                # Process cells
                cells = []
                # Split by pipe but keep empty cells
                raw_cells = row.split('|')
                # Remove first and last which are empty due to outer pipes
                if raw_cells[0].strip() == '':
                    raw_cells = raw_cells[1:]
                if raw_cells and raw_cells[-1].strip() == '':
                    raw_cells = raw_cells[:-1]
                
                for cell in raw_cells:
                    cell_content = cell.strip()
                    if current_table_part == "header" and i < separator_indices[0] if separator_indices else False:
                        cells.append(f"<th>{cell_content}</th>")
                    else:
                        cells.append(f"<td>{cell_content}</td>")
                
                if cells:
                    row_html = f"<tr>{''.join(cells)}</tr>"
                    html_rows.append(row_html)
                    if current_table_part == "header":
                        header_processed = True
            
            # Build the final table
            if separator_indices and header_processed:
                # Table with header and body
                header_end = separator_indices[0]
                thead = f"<thead>{''.join(html_rows[:header_end])}</thead>"
                tbody = f"<tbody>{''.join(html_rows[header_end:])}</tbody>"
                return f"<table class='markdown-table'>{thead}{tbody}</table>"
            else:
                # Table with just a body
                return f"<table class='markdown-table'><tbody>{''.join(html_rows)}</tbody></table>"
        
        # Find tables in content
        # A table pattern is a series of lines that start with pipe and contain multiple pipes
        table_pattern = re.compile(r'(\|[^\n]*\|[\r\n]+)+', re.MULTILINE)
        
        # Process all tables
        def replace_table(match):
            return process_table_content(match.group(0))
            
        html = table_pattern.sub(replace_table, html)
        
        # If any single-line table rows remain, wrap them in table tags
        # But first, remove the already processed tables
        html = re.sub(r'<table class=\'markdown-table\'>.*?</table>', '', html, flags=re.DOTALL)
        
        # Now process any single line tables or remaining table fragments
        if '|' in html:
            rows = html.split('\n')
            for i, row in enumerate(rows):
                if row.strip().startswith('|') and row.strip().endswith('|'):
                    # It's a table row, convert it
                    cells = []
                    for cell in row.split('|')[1:-1]:  # Skip first and last empty cells
                        cells.append(f"<td>{cell.strip()}</td>")
                    
                    if cells:
                        rows[i] = f"<table class='simple-table'><tr>{''.join(cells)}</tr></table>"
            
            html = '\n'.join(rows)
        
        return html
    
    def extract_metadata(self, markdown: str, filename: str) -> Dict[str, Any]:
        """Extracts title, content, and date from markdown"""
        # Find title (first h1)
        title_match = re.search(r'^# (.+?)$', markdown, re.MULTILINE)
        title = title_match.group(1) if title_match else "Untitled Document"
        
        # Find date using multiple patterns
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