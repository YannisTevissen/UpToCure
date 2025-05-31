#!/usr/bin/env python3
"""
UpToCure Report Generator and Translator

This script generates medical research reports for specified diseases and translates them into multiple languages.
"""

import os
import sys
import yaml
import logging
from pathlib import Path
from typing import List, Dict
from reporter import generate_report
from translator import translate_report, setup_translator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("generate_and_translate")

def load_config(config_path: str) -> Dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the config file
        
    Returns:
        Dictionary containing configuration
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading config file: {str(e)}")
        sys.exit(1)

def main():
    """
    Main entry point for the script.
    Generates reports and translates them into specified languages.
    """
    # Get the base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, 'config.yaml')
    
    # Load configuration
    config = load_config(config_path)
    diseases = config['diseases']  # Now directly a list of disease names
    target_languages = config['target_languages']  # Now directly a list of language codes
    
    # Set up DeepL translator
    try:
        translator = setup_translator()
    except Exception as e:
        logger.error(f"Failed to set up DeepL translator: {str(e)}")
        sys.exit(1)
    
    # Generate reports for each disease
    logger.info(f"Starting report generation for {len(diseases)} diseases")
    for disease in diseases:
        try:
            logger.info(f"Generating report for {disease}")
            generate_report(disease)
            
            # Translate the report into each target language
            for lang_code in target_languages:
                logger.info(f"Translating {disease} report to {lang_code}")
                
                # Get the source file path
                source_file = os.path.join(base_dir, '..', 'UpToCure', 'reports', 'generated', f"{disease}.md")
                
                # Translate the report
                translate_report(
                    filepath=source_file,
                    target_dir=os.path.join(base_dir, '..', 'UpToCure', 'reports', 'translated', lang_code),
                    translator=translator,
                    source_lang='en',
                    target_lang=lang_code,
                    force=True  # Force translation to overwrite existing files
                )
                
        except Exception as e:
            logger.error(f"Error processing {disease}: {str(e)}")
            continue
    
    logger.info("Report generation and translation completed")

if __name__ == "__main__":
    main() 