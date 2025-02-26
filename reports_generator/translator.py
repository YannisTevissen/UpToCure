#!/usr/bin/env python3
"""
NLLB Translation Script for UpToCure Reports

This script translates markdown reports from one language to another using the NLLB
(No Language Left Behind) translation model from Facebook/Meta.
"""

import os
import sys
import glob
import re
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import torch
from tqdm import tqdm
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("translator")

# NLLB language codes for common languages
# (NLLB uses specialized codes different from standard language codes)
NLLB_LANG_CODES = {
    'en': 'eng_Latn',  # English
    'fr': 'fra_Latn',  # French
    'es': 'spa_Latn',  # Spanish
    'de': 'deu_Latn',  # German
    'it': 'ita_Latn',  # Italian
    'pt': 'por_Latn',  # Portuguese
    'nl': 'nld_Latn',  # Dutch
    'ru': 'rus_Cyrl',  # Russian
    'zh': 'zho_Hans',  # Chinese (Simplified)
    'ja': 'jpn_Jpan',  # Japanese
    'ar': 'ara_Arab',  # Arabic
}

# Default model to use (smaller model for faster translation)
DEFAULT_MODEL = "facebook/nllb-200-distilled-1.3B"
# Smaller model as fallback
FALLBACK_MODEL = "facebook/nllb-200-distilled-600M"

class TranslationError(Exception):
    """Custom exception for translation errors"""
    pass

def get_nllb_language_code(language_code: str) -> str:
    """
    Convert standard language code to NLLB language code.
    
    Args:
        language_code: Standard ISO language code (e.g., 'fr', 'en')
        
    Returns:
        NLLB language code (e.g., 'fra_Latn', 'eng_Latn')
    """
    # If the code is already in NLLB format (xxx_Xxxx), return as is
    if re.match(r'^[a-z]{3}_[A-Z][a-z]{3}$', language_code):
        logger.info(f"Language code '{language_code}' appears to already be in NLLB format")
        return language_code
        
    # Convert from standard code
    nllb_code = NLLB_LANG_CODES.get(language_code)
    if nllb_code:
        logger.info(f"Converted '{language_code}' to NLLB code '{nllb_code}'")
        return nllb_code
    
    # If not found, warn and return original code
    logger.warning(f"Could not convert '{language_code}' to an NLLB language code. "
                  f"This may cause translation issues. Available codes: {list(NLLB_LANG_CODES.keys())}")
    return language_code

def setup_model(model_name: str) -> Tuple[AutoModelForSeq2SeqLM, AutoTokenizer]:
    """
    Load the NLLB model and tokenizer.
    
    Args:
        model_name: HuggingFace model name/path
        
    Returns:
        Tuple of (model, tokenizer)
    """
    logger.info(f"Loading NLLB model: {model_name}")
    
    try:
        # Load tokenizer with explicit trust_remote_code for safety
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            use_fast=True,
            trust_remote_code=True
        )
        
        # Load model with conservative memory settings
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        
        # Use CPU for now to avoid MPS issues
        device = "cpu"
        logger.info(f"Using device: {device}")
        
        model = model.to(device)
        logger.info(f"Model loaded on {device}")
        
        # Try to identify and print available language codes in tokenizer
        if hasattr(tokenizer, 'get_vocab'):
            # Look for tokens that might be language codes in the vocabulary
            vocab = tokenizer.get_vocab()
            lang_tokens = [token for token in vocab.keys() if re.match(r'[a-z]{3}_[A-Z][a-z]{3}', token)]
            
            if lang_tokens:
                logger.info(f"Model supports {len(lang_tokens)} language codes, including: {', '.join(lang_tokens[:10])}")
        
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Error loading model {model_name}: {str(e)}")
        
        if model_name != FALLBACK_MODEL:
            logger.info(f"Attempting to load fallback model: {FALLBACK_MODEL}")
            return setup_model(FALLBACK_MODEL)
        
        logger.error("Could not load any translation model")
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
        os.path.join(base_dir, '..', 'UpToCure', 'reports', source_lang),  # Original path
        os.path.join(base_dir, 'reports', source_lang),                    # Direct subdirectory
        os.path.join(base_dir, '..', 'reports', source_lang),              # One level up
        os.path.join('reports', source_lang),                              # Relative to current directory
        os.path.abspath(os.path.join('reports', source_lang))              # Absolute path
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
    logger.info(f"Found {len(md_files)} reports in {source_lang} language directory")
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
        os.path.join(base_dir, '..', 'UpToCure', 'reports', target_lang),  # Original path
        os.path.join(base_dir, 'reports', target_lang),                    # Direct subdirectory
        os.path.join(base_dir, '..', 'reports', target_lang),              # One level up
        os.path.join('reports', target_lang),                              # Relative to current directory
        os.path.abspath(os.path.join('reports', target_lang))              # Absolute path
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
        os.makedirs(target_dir, exist_ok=True)
        logger.info(f"Created alternative target directory at: {target_dir}")
    
    return target_dir

def extract_and_translate_markdown(
    content: str,
    model: AutoModelForSeq2SeqLM,
    tokenizer: AutoTokenizer,
    source_lang: str,
    target_lang: str
) -> str:
    """
    Extract markdown sections, translate them, and reconstruct the document.
    This approach translates each section as it's found, without using placeholders.
    
    Args:
        content: Markdown content
        model: NLLB model
        tokenizer: NLLB tokenizer
        source_lang: Source language code
        target_lang: Target language code
        
    Returns:
        Translated markdown content
    """
    translated_content = ""
    remaining_content = content
    
    # Process headers (h1, h2, h3, etc.)
    header_pattern = r'^(#{1,6})\s+(.+)$'
    
    # Process the document line by line to maintain structure
    lines = remaining_content.split('\n')
    translated_lines = []
    
    for line in lines:
        # Check if this line is a header
        header_match = re.match(header_pattern, line)
        if header_match:
            level, header_text = header_match.groups()
            # Translate the header text
            translated_header = translate_text(header_text, model, tokenizer, source_lang, target_lang)
            # Ensure header doesn't have line breaks
            translated_header = translated_header.replace('\n', ' ').strip()
            # Reconstruct the header with the same level
            translated_line = f"{level} {translated_header}"
            translated_lines.append(translated_line)
            logger.debug(f"Translated header: '{header_text}' -> '{translated_header}'")
        
        # Check if this line is part of a code block
        elif line.strip().startswith('```') or line.strip() == '```':
            # Don't translate code blocks, add as is
            translated_lines.append(line)
            
        # Check if this line contains inline code
        elif '`' in line:
            # Extract and preserve inline code
            parts = []
            current_pos = 0
            
            # Find all inline code segments
            inline_code_pattern = r'`([^`]+)`'
            for match in re.finditer(inline_code_pattern, line):
                # Add text before the code
                if match.start() > current_pos:
                    text_before = line[current_pos:match.start()]
                    if text_before.strip():
                        translated_text = translate_text(text_before, model, tokenizer, source_lang, target_lang)
                        parts.append(translated_text)
                    else:
                        parts.append(text_before)  # Preserve whitespace
                
                # Add the code as is
                code = match.group(0)  # The entire match including backticks
                parts.append(code)
                current_pos = match.end()
            
            # Add any remaining text after the last code segment
            if current_pos < len(line):
                text_after = line[current_pos:]
                if text_after.strip():
                    translated_text = translate_text(text_after, model, tokenizer, source_lang, target_lang)
                    parts.append(translated_text)
                else:
                    parts.append(text_after)  # Preserve whitespace
            
            translated_lines.append(''.join(parts))
            
        # Check if this line contains URLs
        elif '[' in line and '](' in line:
            # Extract and preserve URLs
            parts = []
            current_pos = 0
            
            # Find all URL segments
            url_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            for match in re.finditer(url_pattern, line):
                # Add text before the URL
                if match.start() > current_pos:
                    text_before = line[current_pos:match.start()]
                    if text_before.strip():
                        translated_text = translate_text(text_before, model, tokenizer, source_lang, target_lang)
                        parts.append(translated_text)
                    else:
                        parts.append(text_before)  # Preserve whitespace
                
                # Extract link text and URL
                link_text = match.group(1)
                url = match.group(2)
                
                # Translate only the link text
                translated_link_text = translate_text(link_text, model, tokenizer, source_lang, target_lang)
                
                # Reconstruct the link
                parts.append(f"[{translated_link_text}]({url})")
                current_pos = match.end()
            
            # Add any remaining text after the last URL
            if current_pos < len(line):
                text_after = line[current_pos:]
                if text_after.strip():
                    translated_text = translate_text(text_after, model, tokenizer, source_lang, target_lang)
                    parts.append(translated_text)
                else:
                    parts.append(text_after)  # Preserve whitespace
            
            translated_lines.append(''.join(parts))
            
        # Check if this line is a reference
        elif re.match(r'^\[\d+\]\s+', line):
            # References are typically kept as is or minimally translated
            ref_pattern = r'^\[(\d+)\]\s+(.+)$'
            ref_match = re.match(ref_pattern, line)
            if ref_match:
                ref_num, ref_text = ref_match.groups()
                # Translate the reference text
                translated_ref = translate_text(ref_text, model, tokenizer, source_lang, target_lang)
                translated_lines.append(f"[{ref_num}] {translated_ref}")
            else:
                # If pattern doesn't match exactly, keep as is
                translated_lines.append(line)
                
        # Regular text line
        elif line.strip():
            # Translate regular text
            translated_text = translate_text(line, model, tokenizer, source_lang, target_lang)
            translated_lines.append(translated_text)
            
        # Empty line or whitespace
        else:
            # Preserve empty lines for document structure
            translated_lines.append(line)
    
    # Ensure proper line breaks after headers
    translated_content = '\n'.join(translated_lines)
    translated_content = re.sub(r'(^#+ .+)$', r'\1\n', translated_content, flags=re.MULTILINE)
    
    return translated_content

def translate_text(text, model, tokenizer, source_lang, target_lang):
    """
    Translate text from source language to target language using the NLLB model.
    
    Args:
        text (str): Text to translate
        model: NLLB model
        tokenizer: NLLB tokenizer
        source_lang (str): Source language code
        target_lang (str): Target language code
        
    Returns:
        str: Translated text
    """
    if not text or text.strip() == "":
        return text
    
    # Convert standard language codes to NLLB language codes
    nllb_source_lang = NLLB_LANG_CODES.get(source_lang, source_lang)
    nllb_target_lang = NLLB_LANG_CODES.get(target_lang, target_lang)
    
    logger.debug(f"Translating text from {nllb_source_lang} to {nllb_target_lang}")
    logger.debug(f"Text length: {len(text)} characters")
    
    # Get the device the model is on
    device = next(model.parameters()).device
    logger.debug(f"Model is on device: {device}")
    
    # Split text into paragraphs to preserve line breaks
    paragraphs = text.split('\n\n')
    translated_paragraphs = []
    
    # Process each paragraph separately
    for i, paragraph in enumerate(paragraphs):
        # Skip empty paragraphs but preserve them in the output
        if not paragraph.strip():
            translated_paragraphs.append('')
            continue
            
        # Handle single line breaks within paragraphs
        # Replace them with a special token that we'll convert back after translation
        lines = paragraph.split('\n')
        paragraph_with_markers = ' LINEBREAK '.join(lines)
        
        # Split long paragraphs into chunks to avoid token limit
        chunks = []
        current_chunk = ""
        
        for line in paragraph_with_markers.split('. '):
            # If adding this line would make the chunk too long, start a new chunk
            if len(current_chunk) + len(line) > 512:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line
            else:
                if current_chunk:
                    current_chunk += '. ' + line
                else:
                    current_chunk = line
                    
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk)
            
        # Translate each chunk
        translated_chunks = []
        for chunk in chunks:
            try:
                # Prepare the input for the model and move to the same device as the model
                inputs = tokenizer(chunk, return_tensors="pt")
                # Move input tensors to the same device as the model
                inputs = {k: v.to(device) for k, v in inputs.items()}
                
                # Determine the correct token ID for the target language
                forced_bos_token_id = None
                
                # Method 1: Check if the tokenizer has a lang_code_to_id mapping
                if hasattr(tokenizer, 'lang_code_to_id') and isinstance(tokenizer.lang_code_to_id, dict):
                    if nllb_target_lang in tokenizer.lang_code_to_id:
                        forced_bos_token_id = tokenizer.lang_code_to_id[nllb_target_lang]
                        logger.debug(f"Found target language ID using lang_code_to_id: {forced_bos_token_id}")
                
                # Method 2: Direct conversion from token to ID
                if forced_bos_token_id is None:
                    try:
                        token_id = tokenizer.convert_tokens_to_ids(nllb_target_lang)
                        if token_id != tokenizer.unk_token_id:
                            forced_bos_token_id = token_id
                            logger.debug(f"Found target language ID using convert_tokens_to_ids: {forced_bos_token_id}")
                    except Exception as e:
                        logger.debug(f"Could not convert token to ID: {str(e)}")
                
                # Generate translation
                with torch.no_grad():
                    generation_kwargs = {
                        "max_length": 512,
                        "num_beams": 5,  # Use beam search for better quality
                    }
                    
                    if forced_bos_token_id is not None:
                        generation_kwargs["forced_bos_token_id"] = forced_bos_token_id
                    else:
                        # If we couldn't find the token ID, try prefixing the input with the target language code
                        logger.warning(f"Could not determine token ID for language {nllb_target_lang}. Using prefix method.")
                        inputs = tokenizer(f"{nllb_target_lang} {chunk}", return_tensors="pt")
                        # Move input tensors to the same device as the model
                        inputs = {k: v.to(device) for k, v in inputs.items()}
                    
                    translated_tokens = model.generate(**inputs, **generation_kwargs)
                
                # Decode the generated tokens
                translation = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
                
                # Remove the language prefix if it was prepended
                if translation.startswith(nllb_target_lang + " "):
                    translation = translation[len(nllb_target_lang) + 1:]
                    
                translated_chunks.append(translation)
                
            except Exception as e:
                logger.error(f"Error translating chunk: {str(e)}")
                # Return the original text if translation fails
                translated_chunks.append(chunk)
        
        # Join the translated chunks
        translated_paragraph = ' '.join(translated_chunks)
        
        # Convert the special line break token back to actual line breaks
        translated_paragraph = translated_paragraph.replace(' LINEBREAK ', '\n')
        translated_paragraph = translated_paragraph.replace('LINEBREAK', '\n')
        
        translated_paragraphs.append(translated_paragraph)
    
    # Join the translated paragraphs with double line breaks to preserve formatting
    translated_text = '\n\n'.join(translated_paragraphs)
    
    logger.debug(f"Translation complete. Result length: {len(translated_text)} characters")
    return translated_text

def translate_filename(filename: str, model: AutoModelForSeq2SeqLM, tokenizer: AutoTokenizer, 
                      source_lang: str, target_lang: str) -> str:
    """
    Translate a filename from source language to target language.
    Preserves the file extension.
    
    Args:
        filename: Filename to translate
        model: NLLB model
        tokenizer: NLLB tokenizer
        source_lang: Source language code
        target_lang: Target language code
        
    Returns:
        Translated filename
    """
    # Extract the base name and extension
    base_name, extension = os.path.splitext(os.path.basename(filename))
    
    # Replace hyphens and underscores with spaces for better translation
    base_name_spaced = base_name.replace('-', ' ').replace('_', ' ')
    
    # Translate the base name
    translated_base = translate_text(base_name_spaced, model, tokenizer, source_lang, target_lang)
    
    # Clean up the translated name for use as a filename
    # Replace spaces with hyphens and remove any characters that aren't safe for filenames
    translated_base = translated_base.strip()
    translated_base = re.sub(r'\s+', '-', translated_base)  # Replace spaces with hyphens
    translated_base = re.sub(r'[^\w\-\.]', '', translated_base)  # Remove unsafe characters
    
    # Ensure we have a valid filename
    if not translated_base:
        logger.warning(f"Translation resulted in empty filename for {filename}, using original")
        return filename
    
    # Combine the translated base name with the original extension
    return translated_base + extension

def translate_report(
    filepath: str, 
    target_dir: str, 
    model: AutoModelForSeq2SeqLM, 
    tokenizer: AutoTokenizer, 
    source_lang: str, 
    target_lang: str,
    force: bool = False,
    translate_filenames: bool = True
) -> None:
    """
    Translate a single markdown report file.
    
    Args:
        filepath: Path to report file
        target_dir: Target directory
        model: NLLB model
        tokenizer: NLLB tokenizer
        source_lang: Source language code
        target_lang: Target language code
        force: Force translation even if target file exists
        translate_filenames: Whether to translate filenames
    """
    filename = os.path.basename(filepath)
    
    # Debug file paths
    logger.debug(f"Source filepath: {filepath}")
    logger.debug(f"Target directory: {target_dir}")
    
    # Optionally translate the filename
    if translate_filenames:
        try:
            translated_filename = translate_filename(filename, model, tokenizer, source_lang, target_lang)
            logger.info(f"Translated filename: {filename} -> {translated_filename}")
        except Exception as e:
            logger.warning(f"Could not translate filename, using original: {str(e)}")
            translated_filename = filename
    else:
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
        
        # Extract and translate markdown sections
        translated_content = extract_and_translate_markdown(
            content, model, tokenizer, source_lang, target_lang
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
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL,
                        help=f"NLLB model to use (default: {DEFAULT_MODEL})")
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
    if args.source_lang not in NLLB_LANG_CODES and not re.match(r'^[a-z]{3}_[A-Z][a-z]{3}$', args.source_lang):
        logger.warning(f"Source language '{args.source_lang}' is not in the known language codes list")
    
    if args.target_lang not in NLLB_LANG_CODES and not re.match(r'^[a-z]{3}_[A-Z][a-z]{3}$', args.target_lang):
        logger.warning(f"Target language '{args.target_lang}' is not in the known language codes list")
    
    # Print translation parameters
    logger.info(f"Translation task: {args.source_lang} -> {args.target_lang}")
    logger.info(f"Using model: {args.model}")
    logger.info(f"Translating filenames: {not args.no_translate_filenames}")
    
    # Get the base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logger.debug(f"Base directory: {base_dir}")
    logger.debug(f"Current working directory: {os.getcwd()}")
    
    try:
        # Load the translation model
        model, tokenizer = setup_model(args.model)
        
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
                model, 
                tokenizer, 
                args.source_lang, 
                args.target_lang,
                args.force,
                not args.no_translate_filenames
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
                        model, 
                        tokenizer, 
                        args.source_lang, 
                        args.target_lang,
                        args.force,
                        not args.no_translate_filenames
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
