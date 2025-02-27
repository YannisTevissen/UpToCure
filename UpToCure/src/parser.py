"""
Parser module for UpToCure

This module processes markdown files and extracts structured content.
"""

import os
import re
import glob
import logging
import markdown
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_reports(reports_dir="reports", lang="en"):
    """Process the markdown files in the specified language reports directory."""
    logger.info(f"Processing reports for language: {lang}")
    
    # Update the reports directory to include the language
    lang_reports_dir = os.path.join(reports_dir, lang)
    
    # Ensure the language-specific directory exists
    if not os.path.exists(lang_reports_dir):
        logger.info(f"Creating directory for language: {lang}")
        os.makedirs(lang_reports_dir, exist_ok=True)
        
        # Create a sample report if the directory is empty
        create_sample_report(lang_reports_dir, lang)
    
    markdown_files = glob.glob(os.path.join(lang_reports_dir, "*.md"))
    
    if not markdown_files:
        logger.info(f"No markdown files found in {lang_reports_dir}")
        # Create a sample report if no files were found
        create_sample_report(lang_reports_dir, lang)
        markdown_files = glob.glob(os.path.join(lang_reports_dir, "*.md"))
        
        if not markdown_files:
            return []
    
    reports = []
    
    for file_path in markdown_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Extract metadata
            metadata = extract_metadata(content, os.path.basename(file_path))
            
            reports.append(metadata)
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
    
    return reports

def extract_metadata(markdown_content, filename):
    """Extracts title, content, and date from markdown"""
    # Find title (first h1)
    title_match = re.search(r'^# (.+?)$', markdown_content, re.MULTILINE)
    title = title_match.group(1) if title_match else "Untitled Document"
    
    # Find date using multiple patterns
    date_match = re.search(r'Last updated: (.+?)$', markdown_content, re.MULTILINE)
    date = date_match.group(1) if date_match else datetime.now().strftime("%B %d, %Y")
    
    # Parse content to HTML
    content = markdown.markdown(markdown_content)
    
    return {
        'title': title,
        'content': content,
        'date': date,
        'filename': filename
    }

def create_sample_report(target_dir, language):
    """Create a sample report in the specified language directory."""
    sample_filename = "sample-report.md"
    sample_path = os.path.join(target_dir, sample_filename)
    
    # Check if sample already exists
    if os.path.exists(sample_path):
        logger.info(f"Sample report already exists at {sample_path}")
        return
    
    logger.info(f"Creating sample report in {language} at {sample_path}")
    
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
        logger.info(f"Successfully created sample report at {sample_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating sample report: {e}")
        return False 