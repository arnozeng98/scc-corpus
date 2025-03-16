import os
from utils import generate_date_range_urls, ensure_dir_exists

# Base directories
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")

# SCC scraping configuration
BASE_URL = "https://decisions.scc-csc.ca"
OUTPUT_DIR = os.path.join(DATA_DIR, "raw")  # Raw HTML storage
TARGET_CASES = 500    # Legacy parameter, kept for backward compatibility
MAX_NO_CHANGE_SCROLLS = 3  # Stop scrolling after this many consecutive scrolls with no new cases
SCROLL_ATTEMPTS = 30  # Number of scroll attempts

# Chrome Driver configuration (modify according to actual path)
CHROME_DRIVER_PATH = os.path.join(BASE_DIR, "chromedriver")

# Other settings
TIMEOUT = 10     # Selenium wait timeout (seconds)
HEADLESS = True  # Whether to use headless mode

# Generate search URLs based on date ranges
SEARCH_URLS = generate_date_range_urls(BASE_URL, subject_id="16")

# Log file paths
LOGS_DIR = os.path.join(BASE_DIR, "logs")
SCRAPER_LOG_FILE = os.path.join(LOGS_DIR, "scraper.log")
MAIN_LOG_FILE = os.path.join(LOGS_DIR, "main.log")
ANNOTATOR_LOG_FILE = os.path.join(LOGS_DIR, "annotator.log")

# Data storage paths
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
SCRAPED_LINKS_FILE = os.path.join(PROCESSED_DIR, "scraped_links.json")
CRIMINAL_CASES_OUTPUT = os.path.join(PROCESSED_DIR, "annotation.json")

# Ensure directories exist
ensure_dir_exists(LOGS_DIR)
ensure_dir_exists(OUTPUT_DIR)
ensure_dir_exists(PROCESSED_DIR)
ensure_dir_exists(os.path.dirname(CRIMINAL_CASES_OUTPUT))
