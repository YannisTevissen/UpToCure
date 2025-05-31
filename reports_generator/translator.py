#!/usr/bin/env python3
"""
DeepL Translation Script for UpToCure Reports

This script translates markdown reports from one language to another using the DeepL API.
"""

import os
import sys
import glob
import re
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import deepl
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("translator")

# DeepL language codes for common languages
DEEPL_LANG_CODES = {
    'en': 'EN',  # English
    'fr': 'FR',  # French
    'es': 'ES',  # Spanish
    'de': 'DE',  # German
    'it': 'IT',  # Italian
    'pt': 'PT',  # Portuguese
    'nl': 'NL',  # Dutch
    'ru': 'RU',  # Russian
    'zh': 'ZH',  # Chinese (Simplified)
    'ja': 'JA',  # Japanese
    'bg': 'BG',  # Bulgarian
    'cs': 'CS',  # Czech
    'da': 'DA',  # Danish
    'et': 'ET',  # Estonian
    'fi': 'FI',  # Finnish
    'el': 'EL',  # Greek
    'hu': 'HU',  # Hungarian
    'id': 'ID',  # Indonesian
    'lv': 'LV',  # Latvian
    'lt': 'LT',  # Lithuanian
    'pl': 'PL',  # Polish
    'ro': 'RO',  # Romanian
    'sk': 'SK',  # Slovak
    'sl': 'SL',  # Slovenian
    'sv': 'SV',  # Swedish
    'tr': 'TR',  # Turkish
    'uk': 'UK',  # Ukrainian
    'ko': 'KO',  # Korean
    'nb': 'NB',  # Norwegian (Bokmål)
}

class TranslationError(Exception):
    """Custom exception for translation errors"""
    pass

def get_deepl_language_code(language_code: str) -> str:
    """
    Convert standard language code to DeepL language code.
    
    Args:
        language_code: Standard ISO language code (e.g., 'fr', 'en')
        
    Returns:
        DeepL language code (e.g., 'FR', 'EN')
    """
    # If the code is already in DeepL format (uppercase), return as is
    if language_code.upper() in DEEPL_LANG_CODES.values():
        logger.info(f"Language code '{language_code}' appears to already be in DeepL format")
        return language_code.upper()
        
    # Convert from standard code
    deepl_code = DEEPL_LANG_CODES.get(language_code.lower())
    if deepl_code:
        logger.info(f"Converted '{language_code}' to DeepL code '{deepl_code}'")
        return deepl_code
    
    # If not found, warn and return original code in uppercase
    logger.warning(f"Could not convert '{language_code}' to a DeepL language code. "
                  f"This may cause translation issues. Available codes: {list(DEEPL_LANG_CODES.keys())}")
    return language_code.upper()

def setup_translator(api_key: str = None) -> deepl.Translator:
    """
    Set up the DeepL translator.
    
    Args:
        api_key: DeepL API key (if None, will try to get from DEEPL_API_KEY environment variable)
        
    Returns:
        DeepL translator object
    """
    logger.info("Setting up DeepL translator")
    
    try:
        # Try to get API key from environment if not provided
        if api_key is None:
            api_key = os.environ.get("DEEPL_API_KEY")
            if api_key is None:
                raise ValueError("No DeepL API key provided. Please provide an API key or set the DEEPL_API_KEY environment variable.")
        
        # Initialize the translator
        translator = deepl.Translator(api_key)
        
        # Test the connection and get usage information
        usage = translator.get_usage()
        if usage.character.limit:
            logger.info(f"DeepL API usage: {usage.character.count}/{usage.character.limit} characters")
        else:
            logger.info("DeepL API connected successfully")
             
        return translator
        
    except Exception as e:
        logger.error(f"Error setting up DeepL translator: {str(e)}")
        raise

def find_reports(base_dir: str, source_lang: str) -> List[str]:
    """
    Find all markdown reports in the source language directory.
    
    Args:
        base_dir: Base directory of the script
        source_lang: Source language code
        
    Returns:
        List of markdown file paths
    """
    # Try different possible paths for reports
    possible_paths = [
        os.path.join(base_dir, '..', 'UpToCure', 'reports', 'generated'),  # Original path
        os.path.join(base_dir, 'reports', 'generated'),                    # Direct subdirectory
        os.path.join(base_dir, '..', 'reports', 'generated'),              # One level up
        os.path.join('reports', 'generated'),                              # Relative to current directory
        os.path.abspath(os.path.join('reports', 'generated'))              # Absolute path
    ]
    
    reports_dir = None
    for path in possible_paths:
        if os.path.exists(path):
            reports_dir = path
            logger.info(f"Found reports directory at: {reports_dir}")
            break
    
    if not reports_dir:
        logger.warning(f"Source directory not found. Tried: {possible_paths}")
        return []
    
    md_files = glob.glob(os.path.join(reports_dir, '*.md'))
    logger.info(f"Found {len(md_files)} reports in generated directory")
    return md_files

def ensure_target_dir(base_dir: str, target_lang: str) -> str:
    """
    Ensure the target language directory exists.
    
    Args:
        base_dir: Base directory of the script
        target_lang: Target language code
        
    Returns:
        Path to the target directory
    """
    # Try different possible paths for target directory
    possible_paths = [
        os.path.join(base_dir, '..', 'UpToCure', 'reports', 'translated', target_lang),  # Original path
        os.path.join(base_dir, 'reports', 'translated', target_lang),                    # Direct subdirectory
        os.path.join(base_dir, '..', 'reports', 'translated', target_lang),              # One level up
        os.path.join('reports', 'translated', target_lang),                              # Relative to current directory
        os.path.abspath(os.path.join('reports', 'translated', target_lang))              # Absolute path
    ]
    
    # First, check if any of these directories already exist
    for path in possible_paths:
        if os.path.exists(os.path.dirname(path)):
            target_dir = path
            logger.info(f"Using target directory path: {target_dir}")
            os.makedirs(target_dir, exist_ok=True)
            return target_dir
    
    # If none exist, try to create the first one
    target_dir = possible_paths[0]
    try:
        os.makedirs(target_dir, exist_ok=True)
        logger.info(f"Created target directory at: {target_dir}")
    except Exception as e:
        logger.error(f"Could not create target directory at {target_dir}: {str(e)}")
        # Try the second option
        target_dir = possible_paths[1]
        try:
            os.makedirs(target_dir, exist_ok=True)
            logger.info(f"Created target directory at: {target_dir}")
        except Exception as e:
            logger.error(f"Could not create target directory at {target_dir}: {str(e)}")
            raise TranslationError(f"Failed to create target directory: {str(e)}")
    
    return target_dir

def translate_markdown_file(
    content: str,
    translator: deepl.Translator,
    source_lang: str,
    target_lang: str
) -> str:
    """
    Translate a markdown file as one big block, preserving markdown formatting.
    
    Args:
        content: Markdown content
        translator: DeepL translator
        source_lang: Source language code
        target_lang: Target language code
        
    Returns:
        Translated markdown content
    """
    logger.info("Translating markdown file as one block")
    
    # Convert standard language codes to DeepL language codes
    deepl_source_lang = get_deepl_language_code(source_lang)
    deepl_target_lang = get_deepl_language_code(target_lang)
    
    # Extract code blocks and placeholders to protect them from translation
    
    try:
        # Translate the content with placeholders
        logger.debug(f"Translating content with {len(content)} characters")
        content_splitted = content.split("\n")
        content_splitted_translated = []
        for i, c in enumerate(content_splitted):
            logger.debug(f"Translating line {i+1}: {c}")
            if c.strip() == "":
                content_splitted_translated.append(c)
            else:
                # Use DeepL to translate the content
                result = translator.translate_text(
                    c,
                    source_lang=deepl_source_lang if deepl_source_lang != "AUTO" else None,
                    target_lang=deepl_target_lang,
                    preserve_formatting=True,
                    tag_handling="html"  # This helps preserve some markdown formatting
                )
                content_splitted_translated.append(result.text)

        translated_content = "\n".join(content_splitted_translated)
        logger.debug(f"Translation complete. Result length: {len(translated_content)} characters")
        
        
        return translated_content
        
    except Exception as e:
        logger.error(f"Error translating markdown content: {str(e)}")
        raise TranslationError(f"Error translating markdown content: {str(e)}")



def translate_report(
    filepath: str, 
    target_dir: str, 
    translator: deepl.Translator, 
    source_lang: str, 
    target_lang: str,
    force: bool = False,
) -> None:
    """
    Translate a single markdown report file.
    
    Args:
        filepath: Path to report file
        target_dir: Target directory
        translator: DeepL translator
        source_lang: Source language code
        target_lang: Target language code
        force: Force translation even if target file exists
        translate_filenames: Whether to translate filenames
    """
    filename = os.path.basename(filepath)
    
    # Debug file paths
    logger.debug(f"Source filepath: {filepath}")
    logger.debug(f"Target directory: {target_dir}")
    
   
    try:
        translated_filename = translator.translate_text(filename, source_lang, target_lang)
        logger.info(f"Translated filename: {filename} -> {translated_filename}")
    except Exception as e:
        logger.warning(f"Could not translate filename, using original: {str(e)}")
        translated_filename = filename
    
    
    target_path = os.path.join(target_dir, translated_filename)
    logger.debug(f"Target path: {target_path}")
    
    # Skip if target file already exists and force is False
    if os.path.exists(target_path) and not force:
        logger.info(f"Target file already exists, skipping: {target_path}")
        return
    
    logger.info(f"Translating {filename} from {source_lang} to {target_lang}")
    
    try:
        # Read the source file
        logger.debug(f"Reading source file: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.debug(f"Source content length: {len(content)} characters")
        
        translated_content = translate_markdown_file(
            content, translator, source_lang, target_lang
        )
        logger.debug(f"Translated content length: {len(translated_content)} characters")
        
        # Write the translated file
        logger.debug(f"Writing to target path: {target_path}")
        try:
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            logger.debug(f"File written successfully")
        except Exception as write_error:
            logger.error(f"Error writing file: {str(write_error)}")
            # Try to check if directory exists and is writable
            if not os.path.exists(os.path.dirname(target_path)):
                logger.error(f"Target directory does not exist: {os.path.dirname(target_path)}")
            elif not os.access(os.path.dirname(target_path), os.W_OK):
                logger.error(f"Target directory is not writable: {os.path.dirname(target_path)}")
            raise
        
        logger.info(f"Successfully translated to {target_path}")
    
    except Exception as e:
        logger.error(f"Error translating {filename}: {str(e)}")
        raise TranslationError(f"Error translating {filename}: {str(e)}")
 


def create_sample_report(target_dir: str, language: str) -> str:
    """
    Create a sample report in the specified language directory.
    
    Args:
        target_dir: Target directory
        language: Language code
        
    Returns:
        Path to the created sample report
    """
    sample_filename = "sample-report.md"
    sample_path = os.path.join(target_dir, sample_filename)
    
    # Skip if file already exists
    if os.path.exists(sample_path):
        logger.info(f"Sample report already exists at {sample_path}")
        return sample_path
    
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

    try:
        # Use the specified language sample if available, otherwise use English
        content = sample_reports.get(language, sample_reports.get('en'))
        
        # Write the sample report to file
        with open(sample_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Successfully created sample report at {sample_path}")
        return sample_path
    except Exception as e:
        logger.error(f"Error creating sample report: {str(e)}")
        return None

def main():
    """
    Main entry point for the translation script.
    Parses command line arguments and executes the translation process.
    """
    parser = argparse.ArgumentParser(description="Translate UpToCure reports between languages")
    parser.add_argument("--source-lang", "--source", dest="source_lang", type=str, default="en",
                        help="Source language code (default: en)")
    parser.add_argument("--target-lang", "--target", dest="target_lang", type=str, required=True,
                        help="Target language code")
    parser.add_argument("--api-key", type=str, help="DeepL API key (if not set in DEEPL_API_KEY environment variable)")
    parser.add_argument("--file", type=str, help="Translate a specific file only")
    parser.add_argument("--force", action="store_true", help="Force translation even if target file exists")
    parser.add_argument("--no-translate-filenames", action="store_true", 
                        help="Don't translate filenames")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Validate language codes
    if args.source_lang not in DEEPL_LANG_CODES and args.source_lang.upper() not in DEEPL_LANG_CODES.values():
        logger.warning(f"Source language '{args.source_lang}' is not in the known language codes list")
    
    if args.target_lang not in DEEPL_LANG_CODES and args.target_lang.upper() not in DEEPL_LANG_CODES.values():
        logger.warning(f"Target language '{args.target_lang}' is not in the known language codes list")
    
    # Print translation parameters
    logger.info(f"Translation task: {args.source_lang} -> {args.target_lang}")
    logger.info(f"Using DeepL API")
    
    # Get the base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logger.debug(f"Base directory: {base_dir}")
    logger.debug(f"Current working directory: {os.getcwd()}")
    
    try:
        # Set up the DeepL translator
        translator = setup_translator(args.api_key)
        
        # Create target directory if needed
        target_dir = ensure_target_dir(base_dir, args.target_lang)
        logger.info(f"Target directory: {target_dir}")
        
        # If specific file is specified, translate only that file
        if args.file:
            filepath = args.file
            
            # Check if the file exists, if not try to find it
            if not os.path.exists(filepath):
                logger.warning(f"File not found at specified path: {filepath}")
                
                # Try to find the file in different locations
                possible_paths = [
                    filepath,
                    os.path.join(base_dir, filepath),
                    os.path.join(base_dir, '..', filepath),
                    os.path.join(base_dir, 'reports', args.source_lang, os.path.basename(filepath)),
                    os.path.join(base_dir, '..', 'reports', args.source_lang, os.path.basename(filepath)),
                    os.path.join(base_dir, '..', 'UpToCure', 'reports', args.source_lang, os.path.basename(filepath))
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        filepath = path
                        logger.info(f"Found file at: {filepath}")
                        break
                
                if not os.path.exists(filepath):
                    logger.error(f"File not found: {filepath}")
                    logger.error(f"Tried these paths: {possible_paths}")
                    sys.exit(1)
            
            translate_report(
                filepath, 
                target_dir, 
                translator, 
                args.source_lang, 
                args.target_lang,
                args.force,
            )
            logger.info(f"Translation completed for {filepath}")
        else:
            # Find all reports in source language
            reports = find_reports(base_dir, args.source_lang)
            
            if not reports:
                logger.error(f"No reports found for language: {args.source_lang}")
                sys.exit(1)
            
            # Translate each report
            logger.info(f"Starting translation of {len(reports)} reports")
            for i, report in enumerate(tqdm(reports, desc="Translating reports")):
                try:
                    translate_report(
                        report, 
                        target_dir, 
                        translator, 
                        args.source_lang, 
                        args.target_lang,
                        args.force,
                    )
                except Exception as e:
                    logger.error(f"Error translating report {i+1}/{len(reports)}: {str(e)}")
            
            logger.info(f"Translation completed for {len(reports)} reports")
            
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
