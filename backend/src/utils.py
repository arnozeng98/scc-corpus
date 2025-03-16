import os
import json
import logging
import datetime
from typing import Dict, List, Any, Optional, Union
import re
import sys
import codecs

def setup_logging(log_file: str, log_level: int = logging.INFO) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_file: Path to the log file
        log_level: Logging level (default: INFO)
        
    Returns:
        Logger instance configured with file and console handlers
    """
    # Make sure the directory exists
    log_dir = os.path.dirname(log_file)
    ensure_dir_exists(log_dir)
    
    # Create a custom logger
    logger = logging.getLogger(log_file)
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    if logger.handlers:
        logger.handlers = []
    
    # Create handlers
    # File handler - using utf-8 encoding to handle special characters
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    
    # Console handler - using utf-8 encoding to handle special characters
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setStream(codecs.getwriter('utf-8')(sys.stdout.buffer) if hasattr(sys.stdout, 'buffer') else sys.stdout)
    
    # Create formatters and add it to handlers
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    file_formatter = logging.Formatter(log_format)
    console_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def generate_date_range_urls(base_url: str, subject_id: str = "16") -> List[str]:
    """
    Generate search URLs based on date ranges spanning 10 years each.
    
    This function creates a series of URLs for searching legal cases, divided into
    10-year periods from 1985 to the current date. It helps handle pagination
    limitations on the website.
    
    Args:
        base_url: Base URL for the search (e.g., "https://decisions.scc-csc.ca")
        subject_id: Subject ID for filtering cases (default: "16" for Criminal cases)
        
    Returns:
        List of generated URLs covering different time periods
    
    Example:
        >>> urls = generate_date_range_urls("https://decisions.scc-csc.ca")
        >>> print(f"Generated {len(urls)} search URLs")
    """
    # Get current date
    today = datetime.datetime.now()
    current_year = today.year
    current_month = today.month
    current_day = today.day
    
    # Create the base search URL template
    base_search_url = f"{base_url}/scc-csc/en/d/s/index.do?cont=&ref=&d1={{d1}}&d2={{d2}}&p=&su={subject_id}&or="
    
    # Generate time ranges
    urls = []
    
    # URL for cases before 1986
    urls.append(
        base_search_url.format(d1="", d2="1985-12-31")
    )
    
    # Generate URLs for 10-year spans dynamically, starting from 1986
    start_year = 1986
    while start_year <= current_year:
        # Calculate end year (10-year span)
        end_year = start_year + 9
        
        # If this range includes the current year, adjust the end date to today
        if current_year <= end_year:
            end_date = f"{current_year}-{current_month:02d}-{current_day:02d}"
        else:
            end_date = f"{end_year}-12-31"
            
        url = base_search_url.format(
            d1=f"{start_year}-01-01",
            d2=end_date
        )
        urls.append(url)
        
        # If we've included the current year, stop adding ranges
        if current_year <= end_year:
            break
        
        # Move to next 10-year span
        start_year += 10
    
    return urls

def ensure_dir_exists(directory: str) -> None:
    """
    Ensure that a directory exists, creating it if necessary.
    
    This is a convenience function that creates all necessary parent
    directories if they don't exist yet.
    
    Args:
        directory: Directory path to check/create
    
    Example:
        >>> ensure_dir_exists("data/output/results")
        # Creates all directories in the path if they don't exist
    """
    os.makedirs(directory, exist_ok=True)

def load_json_file(file_path: str, default: Any = None) -> Any:
    """
    Load data from a JSON file with error handling.
    
    Safely loads JSON data from a file. If the file doesn't exist or
    if there's an error during loading, returns the default value.
    
    Args:
        file_path: Path to the JSON file to load
        default: Default value to return if file doesn't exist or load fails
        
    Returns:
        Loaded data from JSON file or default value if loading fails
    
    Example:
        >>> data = load_json_file("settings.json", default={"version": "1.0"})
    """
    if default is None:
        default = {}
        
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading JSON file {file_path}: {e}")
            return default
    return default

def save_json_file(file_path: str, data: Any, indent: int = 2) -> bool:
    """
    Save data to a JSON file with error handling.
    
    Safely saves data to a JSON file with proper encoding and formatting.
    Creates all necessary directories in the path if they don't exist.
    
    Args:
        file_path: Path where to save the JSON file
        data: Data to save (must be JSON serializable)
        indent: JSON indentation level for pretty-printing
        
    Returns:
        True if saving was successful, False otherwise
    
    Example:
        >>> success = save_json_file("results.json", {"status": "completed", "count": 42})
    """
    try:
        ensure_dir_exists(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        logging.error(f"Error saving JSON file {file_path}: {e}")
        return False

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be used as a valid filename across operating systems.
    
    Replaces characters that are problematic in filenames with safe alternatives.
    This ensures that filenames will be valid on Windows, macOS and Linux.
    Spaces are removed to create more compact filenames.
    
    Args:
        filename: Original filename or string
        
    Returns:
        Sanitized filename safe to use on all operating systems
    
    Example:
        >>> safe_name = sanitize_filename("case/report: 2022?")
        >>> print(safe_name)  # Outputs: "case-report-2022_"
        >>> safe_name = sanitize_filename("18190, 18292")
        >>> print(safe_name)  # Outputs: "18190-18292"
    """
    # Handle leading/trailing whitespace
    filename = filename.strip()
    
    # 1. Replace path separators and OS-specific characters
    os_chars_map = {
        '/': '-',
        '\\': '-',
        ':': '-',
        '*': '_',
        '?': '_',
        '|': '_',
        '<': '_',
        '>': '_',
        '"': "'",
        ',': '-'  # Handle multiple case numbers
    }
    
    for char, replacement in os_chars_map.items():
        filename = filename.replace(char, replacement)
    
    # 2. Replace other potentially problematic characters
    other_chars = r'[%&{}\$!@#\^=+]'
    filename = re.sub(other_chars, '_', filename)
    
    # 3. Remove all spaces (Option 3)
    filename = filename.replace(' ', '')
    
    # Ensure the filename isn't empty and doesn't have problematic starts/ends
    if not filename or filename.isspace():
        filename = "unnamed_file"
    
    # Remove any duplicate special characters
    filename = re.sub(r'[-_]{2,}', '-', filename)
    
    return filename 