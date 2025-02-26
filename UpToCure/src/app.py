from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Optional, Any
from datetime import datetime
import re
import os
import glob
from pydantic import BaseModel
import json
from pathlib import Path
import markdown
from flask import Flask, jsonify, request, send_from_directory

# Initialize Flask app with frontend folder as static folder
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')

# Enable CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

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

# Custom parser for Markdown content
class MarkdownParser:
    """Parser for Markdown content with metadata extraction."""
    
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

def process_reports(reports_dir="reports", lang="en"):
    """Process the markdown files in the specified language reports directory."""
    # Update the reports directory to include the language
    reports_dir = os.path.join(reports_dir, lang)
    
    # Ensure the language-specific directory exists
    if not os.path.exists(reports_dir):
        print(f"Creating directory for language: {lang}")
        os.makedirs(reports_dir, exist_ok=True)
        
        # Create a sample report if the directory is empty
        create_sample_report(reports_dir, lang)
    
    markdown_files = glob.glob(os.path.join(reports_dir, "*.md"))
    
    if not markdown_files:
        print(f"No markdown files found in {reports_dir}")
        # Create a sample report if no files were found
        create_sample_report(reports_dir, lang)
        markdown_files = glob.glob(os.path.join(reports_dir, "*.md"))
        
        if not markdown_files:
            return []
    
    reports = []
    
    for file_path in markdown_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            report = {
                "id": os.path.basename(file_path).replace('.md', ''),
                "content": content
            }
            
            reports.append(report)
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    return reports

def create_sample_report(target_dir, language):
    """Create a sample report in the specified language directory."""
    sample_filename = "sample-report.md"
    sample_path = os.path.join(target_dir, sample_filename)
    
    # Check if sample already exists
    if os.path.exists(sample_path):
        print(f"Sample report already exists at {sample_path}")
        return
    
    print(f"Creating sample report in {language} at {sample_path}")
    
    # Sample reports in different languages
    sample_reports = {
        'en': """# Sample Report: Introduction to UpToCure

Welcome to UpToCure! This is a sample report to demonstrate the markdown parsing capabilities.

**Key Features:**
* Parses markdown to HTML
* Extracts metadata like title and date
* Displays content in a responsive carousel

## Getting Started

To add your own reports, simply create markdown files in the `reports` directory.

*Last updated: April 15, 2025*
""",
        'fr': """# Exemple de rapport : Introduction à UpToCure

Bienvenue sur UpToCure ! Ceci est un exemple de rapport pour démontrer les capacités d'analyse Markdown.

**Fonctionnalités clés :**
* Conversion du Markdown en HTML
* Extraction de métadonnées comme le titre et la date
* Affichage du contenu dans un carrousel responsive

## Pour commencer

Pour ajouter vos propres rapports, créez simplement des fichiers Markdown dans le répertoire `reports`.

*Dernière mise à jour : 15 avril 2025*
"""
    }
    
    # Use the specified language sample if available, otherwise use English
    content = sample_reports.get(language, sample_reports['en'])
    
    try:
        with open(sample_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully created sample report at {sample_path}")
        return True
    except Exception as e:
        print(f"Error creating sample report: {e}")
        return False

# Root API endpoint
@app.route('/api')
def api_root():
    """Root API endpoint returning API info"""
    return jsonify({"message": "Welcome to UpToCure API"})

# API endpoint for reports
@app.route('/api/reports')
def get_reports():
    """Get all available parsed reports"""
    # Get language parameter, default to English if not provided
    lang = request.args.get('lang', 'en')
    
    try:
        print(f"Processing reports for language: {lang}")
        # Get the base directory (where this file is located)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reports_base_dir = os.path.join(base_dir, 'reports')
        
        print(f"Reports directory: {reports_base_dir}")
        print(f"Language-specific directory: {os.path.join(reports_base_dir, lang)}")
        
        # Process reports for the specified language
        reports = process_reports(reports_base_dir, lang)
        
        print(f"Found {len(reports)} raw reports")
        
        # Format the response
        parser = MarkdownParser()
        formatted_reports = []
        
        for report in reports:
            try:
                # Extract metadata using the parser
                report_data = parser.extract_metadata(
                    report['content'], 
                    report['id'] + '.md'  # Add .md extension back for the parser
                )
                formatted_reports.append(report_data)
            except Exception as e:
                print(f"Error parsing report {report['id']}: {str(e)}")
        
        print(f"Formatted {len(formatted_reports)} reports")
        if formatted_reports:
            print(f"First report title: {formatted_reports[0]['title']}")
        
        response = {
            'error': False,
            'message': f"Successfully processed {len(formatted_reports)} reports for language '{lang}'",
            'reports': formatted_reports
        }
        
        # Print the response size to check if it's too large
        response_json = json.dumps(response)
        print(f"Response size: {len(response_json)} bytes")
        
        return jsonify(response)
    except Exception as e:
        print(f"Error in get_reports: {str(e)}")
        # Return a 500 error for critical issues
        return jsonify({
            'error': True,
            'message': f"Error processing reports: {str(e)}",
            'reports': []
        }), 500

# Default route to serve index.html
@app.route('/')
def index():
    """Serve the index.html file"""
    return app.send_static_file('index.html')

# Routes for specific pages
@app.route('/methodology.html')
def methodology():
    """Serve the methodology HTML page"""
    return app.send_static_file('methodology.html')

# Any other static files are served automatically by Flask

# Main entry point
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the UpToCure API server")
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind the server to')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    print(f"Starting UpToCure API server at http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug) 