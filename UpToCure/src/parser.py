"""
Parser module for UpToCure

This module processes markdown files and extracts structured content.
"""

import os
import re
import glob
import logging
import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from markdown.inlinepatterns import LinkInlineProcessor
from markdown.inlinepatterns import LINK_RE
from datetime import datetime
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Ensure INFO level is set for this logger

# Global configuration for the parser
PARSER_CONFIG = {
    'open_links_in_new_tab': True,  # Whether to add target="_blank" to links
}

class NewTabLinksTreeprocessor(Treeprocessor):
    """
    Treeprocessor that modifies all links to open in a new tab.
    """
    def run(self, root):
        if not PARSER_CONFIG['open_links_in_new_tab']:
            return root
            
        try:
            # Find all <a> elements and add target="_blank" attribute
            for element in root.iter("a"):
                element.set("target", "_blank")
                # For better security, also add rel="noopener noreferrer"
                element.set("rel", "noopener noreferrer")
                logger.debug(f"Modified link: {element.get('href')}")
        except Exception as e:
            logger.error(f"Error in NewTabLinksTreeprocessor: {str(e)}")
        return root

class CustomLinkProcessor(LinkInlineProcessor):
    """Custom link processor that ensures links open in a new tab."""
    
    def handleMatch(self, m, data):
        el, start, end = super().handleMatch(m, data)
        if el is not None and PARSER_CONFIG['open_links_in_new_tab']:
            el.set("target", "_blank")
            el.set("rel", "noopener noreferrer")
            logger.debug(f"Processed link with CustomLinkProcessor: {el.get('href')}")
        return el, start, end

class NewTabLinksExtension(Extension):
    """
    Extension that ensures all links open in a new tab.
    Uses both a Treeprocessor and a custom inline processor for maximum compatibility.
    """
    def extendMarkdown(self, md):
        # Replace the default link processor with our custom one
        md.inlinePatterns.register(CustomLinkProcessor(LINK_RE, md), 'link', 160)
        
        # Also register the treeprocessor as a backup to catch any links missed by the inline processor
        md.treeprocessors.register(NewTabLinksTreeprocessor(md), 'newtablinks', 9)  # Higher priority (lower number)

def configure_parser(open_links_in_new_tab=None):
    """
    Configure the global parser settings.
    
    Args:
        open_links_in_new_tab (bool, optional): Whether links should open in a new tab.
    """
    global PARSER_CONFIG
    
    if open_links_in_new_tab is not None:
        PARSER_CONFIG['open_links_in_new_tab'] = open_links_in_new_tab
    
    logger.info(f"Parser configured with settings: {PARSER_CONFIG}")
    return PARSER_CONFIG

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
            logger.info(f"Processing markdown file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                logger.info(f"Read {len(content)} characters from file")
                
            # Extract metadata
            metadata = extract_metadata(content, file_path)
            logger.info(f"Successfully extracted metadata: title='{metadata['title']}', date='{metadata['date']}'")
            
            reports.append(metadata)
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
    
    return reports

def extract_metadata(markdown_content, path, config=None):
    """
    Extracts title, content, and date from markdown.
    
    Args:
        markdown_content (str): The markdown content to process.
        path (str): Path to the markdown file (used for date extraction).
        config (dict, optional): Override the global parser configuration.
    
    Returns:
        dict: Metadata including title, content, date, and filename.
    """
    # Use local config if provided, otherwise use global config
    if config is None:
        config = PARSER_CONFIG
    
    # Find title (first h1)
    title_match = re.search(r'^# (.+?)$', markdown_content, re.MULTILINE)
    title = title_match.group(1) if title_match else "Untitled Document"
    
    # Parse content to HTML with our custom extension for new tab links
    extensions = [
        'markdown.extensions.tables',
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite',
        'markdown.extensions.smarty',
    ]
    
    # Add our link extension only if configured
    if config['open_links_in_new_tab']:
        extensions.append(NewTabLinksExtension())
    
    content = markdown.markdown(markdown_content, extensions=extensions)
    
    # Double-check all links with BeautifulSoup to ensure they have target="_blank" if configured
    if config['open_links_in_new_tab']:
        try:
            soup = BeautifulSoup(content, 'html.parser')
            for link in soup.find_all('a'):
                if not link.get('target'):
                    link['target'] = '_blank'
                if not link.get('rel') or link.get('rel') != 'noopener noreferrer':
                    link['rel'] = 'noopener noreferrer'
            
            # Use the modified content
            content = str(soup)
            logger.debug(f"BeautifulSoup processed content: {content}")
        except ImportError:
            logger.warning("BeautifulSoup not available for secondary link checking")
        except Exception as e:
            logger.error(f"Error during BeautifulSoup processing: {str(e)}")
    
    # Convert creation time to formatted date string
    creation_time = os.path.getctime(path)
    date_str = datetime.fromtimestamp(creation_time).strftime("%B %d, %Y")
    
    return {
        'title': title,
        'content': content,
        'date': date_str,
        'filename': os.path.basename(path)
    }

def parse_markdown(markdown_content, links_in_new_tab=True):
    """
    Simplified unified interface for parsing markdown.
    
    This is the recommended function to use for consistent parsing throughout the application.
    
    Args:
        markdown_content (str): The markdown content to parse.
        links_in_new_tab (bool): Whether links should open in a new tab.
    
    Returns:
        str: The parsed HTML content.
    """
    logger.info(f"parse_markdown called with links_in_new_tab={links_in_new_tab}")
    logger.info(f"Content first 100 chars: {markdown_content[:100].replace(chr(10), ' ')}")
    
    # Use a temporary file path for extract_metadata
    temp_path = "temp.md"
    
    # Create a local config for this parsing operation
    local_config = {
        'open_links_in_new_tab': links_in_new_tab
    }
    logger.info(f"Created local parser config: {local_config}")
    
    # Extract content using the specified configuration
    result = extract_metadata(markdown_content, temp_path, local_config)
    
    # Log HTML output summary
    html_content = result['content']
    h1_count = html_content.count("<h1")
    h2_count = html_content.count("<h2")
    h3_count = html_content.count("<h3")
    logger.info(f"HTML output contains: {h1_count} h1 tags, {h2_count} h2 tags, {h3_count} h3 tags")
    logger.info(f"HTML output first 100 chars: {html_content[:100].replace(chr(10), ' ')}")
    
    return result['content']

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
* Links automatically open in a new tab
* Consistent heading level handling

## Getting Started

To add your own reports, simply create markdown files in the `reports` directory.

Check out our [GitHub repository](https://github.com/example/uptocure) for more information.

### Heading Levels

This is an h3 heading in the source, but will be rendered as an h4 due to our heading level adjustment.

*Last updated: April 15, 2025*
""",
        'fr': """# Exemple de rapport : Introduction à UpToCure

Bienvenue sur UpToCure ! Ceci est un exemple de rapport pour démontrer les capacités d'analyse Markdown.

**Fonctionnalités clés :**
* Conversion du Markdown en HTML
* Extraction de métadonnées comme le titre et la date
* Affichage du contenu dans un carrousel responsive
* Les liens s'ouvrent automatiquement dans un nouvel onglet
* Gestion cohérente des niveaux de titres

## Pour commencer

Pour ajouter vos propres rapports, créez simplement des fichiers Markdown dans le répertoire `reports`.

Consultez notre [dépôt GitHub](https://github.com/example/uptocure) pour plus d'informations.

### Niveaux de titres

Ceci est un titre h3 dans la source, mais sera rendu comme h4 en raison de notre ajustement de niveau de titre.

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