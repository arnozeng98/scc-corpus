import os
from typing import Dict, List, Any, Optional
from scraper import perform_search
from annotator import annotate_cases
from config import (
    BASE_URL, OUTPUT_DIR, SEARCH_URLS, 
    MAIN_LOG_FILE, CRIMINAL_CASES_OUTPUT
)
from utils import setup_logging

# Set up logging
logger = setup_logging(MAIN_LOG_FILE)

def main() -> int:
    """
    Main entry point for the SCC case scraper and annotator.
    
    This function orchestrates the entire workflow:
    1. Loops through each search URL
    2. Scrapes and downloads case files for each URL
    3. Annotates the downloaded cases
    4. Saves the results to JSON
    
    The function handles multiple date ranges and implements an incremental
    approach that only processes new cases not previously scraped.
    
    Returns:
        Total number of cases processed
    """
    logger.info("Starting the scraping process with resume capability...")

    # Execute searches for each URL
    total_processed = 0
    for url in SEARCH_URLS:
        logger.info(f"Processing search URL: {url}")
        processed_count = perform_search(url, OUTPUT_DIR, BASE_URL)
        total_processed += processed_count
        logger.info(f"Completed processing URL: {url}")
        logger.info(f"Total cases processed so far: {total_processed}")

    logger.info(f"All URLs processed. Total cases processed: {total_processed}")

    # Annotate cases and save to JSON
    logger.info("Starting annotation process...")
    cases = annotate_cases(OUTPUT_DIR, CRIMINAL_CASES_OUTPUT)
    logger.info(f"Annotation completed. Results saved to '{CRIMINAL_CASES_OUTPUT}'")
    logger.info(f"Total criminal cases extracted: {len(cases)}")
    
    return total_processed

if __name__ == "__main__":
    # Call the main function when the script is executed directly
    cases_processed = main()
    logger.info(f"Script completed. Processed {cases_processed} cases in total.")
