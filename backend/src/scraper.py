import os
import time
from typing import Dict, List, Any, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from config import (
    BASE_URL, OUTPUT_DIR, SCROLL_ATTEMPTS, MAX_NO_CHANGE_SCROLLS,
    TIMEOUT, HEADLESS, SEARCH_URLS, SCRAPER_LOG_FILE, SCRAPED_LINKS_FILE
)
from utils import setup_logging, load_json_file, save_json_file, sanitize_filename

# Set up logging
logger = setup_logging(SCRAPER_LOG_FILE)

def load_scraped_links(links_file: str = None) -> Dict[str, str]:
    """
    Load previously scraped links from storage file.
    
    Retrieves the dictionary of previously scraped links where keys are
    the case URLs and values are the corresponding case numbers.
    
    Args:
        links_file: Optional custom path to the scraped links file
                   (defaults to SCRAPED_LINKS_FILE from config)
    
    Returns:
        Dictionary mapping case URLs to case numbers
    
    Example:
        >>> links = load_scraped_links()
        >>> print(f"Found {len(links)} previously scraped links")
    """
    file_path = links_file if links_file else SCRAPED_LINKS_FILE
    return load_json_file(file_path, default={})

def save_scraped_link(link: str, case_number: str, links_file: str = None) -> None:
    """
    Save a newly scraped link with its case number to persistent storage.
    
    Updates the scraped links dictionary with a new entry and saves it
    to the configured storage file.
    
    Args:
        link: URL of the case
        case_number: Case number extracted from the case page
        links_file: Optional custom path to the scraped links file
                   (defaults to SCRAPED_LINKS_FILE from config)
    
    Example:
        >>> save_scraped_link("https://example.com/case/123", "ABC-123")
    """
    file_path = links_file if links_file else SCRAPED_LINKS_FILE
    links = load_scraped_links(file_path)
    links[link] = case_number
    save_json_file(file_path, links)

def setup_driver() -> webdriver.Chrome:
    """
    Initialize and configure Selenium WebDriver with necessary options.
    
    Sets up Chrome WebDriver with appropriate settings for scraping,
    including headless mode if enabled in configuration.
    
    Returns:
        Configured Chrome WebDriver instance
    
    Example:
        >>> driver = setup_driver()
        >>> driver.get("https://example.com")
        >>> driver.quit()
    """
    service = Service(ChromeDriverManager().install())
    options = Options()
    if HEADLESS:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")  # Fix DevTools log issues
    options.add_argument("--log-level=3")  # Reduce the log level and reduce console output
    return webdriver.Chrome(service=service, options=options)

def scrape_cases(search_url: str, stop_after_first: bool = False) -> List[Dict[str, str]]:
    """
    Scrape case links from a search results page.
    
    Handles scrolling through the search results page to load all available
    case links via lazy loading. Stops when no new cases appear after multiple
    scrolls or when maximum scroll attempts is reached.
    
    Args:
        search_url: URL of the search results page
        stop_after_first: If True, stops after finding the first unprocessed case
                         (useful for testing to avoid loading all links)
        
    Returns:
        List of dictionaries containing case information (title, link)
        
    Example:
        >>> cases = scrape_cases("https://decisions.scc-csc.ca/scc-csc/en/d/s/index.do?...")
        >>> print(f"Found {len(cases)} new cases to scrape")
        >>> # For testing, get just one link quickly
        >>> test_case = scrape_cases(url, stop_after_first=True)
    """
    driver = setup_driver()
    driver.get(search_url)
    time.sleep(3)  # Allow the page to load

    # Load previously scraped links to check against
    scraped_links = load_scraped_links()
    logger.info(f"Loaded {len(scraped_links)} previously scraped links for reference")

    # Track consecutive scrolls with no new content
    last_count = 0
    no_change_count = 0
    total_scrolls = 0
    
    case_data = []
    
    # Continue scrolling until we detect no change in MAX_NO_CHANGE_SCROLLS consecutive scrolls
    # or we reach the maximum scroll attempts as a safety limit
    while no_change_count < MAX_NO_CHANGE_SCROLLS and total_scrolls < SCROLL_ATTEMPTS:
        # If we're in testing mode and already found a case, stop scrolling
        if stop_after_first and len(case_data) > 0:
            logger.info(f"Stop after first enabled: Found {len(case_data)} unprocessed case, stopping scroll")
            break
            
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        total_scrolls += 1
        
        try:
            search_iframe = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "decisia-iframe"))
            )
            driver.switch_to.frame(search_iframe)
            cases = driver.find_elements(By.CSS_SELECTOR, "div.metadata")
            current_count = len(cases)
            
            # If we're in testing mode, check for unprocessed cases right away
            if stop_after_first:
                # Check each case and add first unprocessed one to the list
                for case in cases:
                    try:
                        a_elem = case.find_element(By.CSS_SELECTOR, "span.title a")
                        title = a_elem.text.strip()
                        href = a_elem.get_attribute("href")
                        full_link = BASE_URL + href if href.startswith("/") else href
                        
                        # Check if the link has already been scraped
                        if full_link not in scraped_links:
                            case_data.append({"title": title, "link": full_link})
                            logger.info(f"Found unprocessed case for testing: {title}")
                            break  # Stop after finding the first case
                    except Exception as e:
                        logger.error(f"Error extracting case link: {e}")
                        continue
            
            driver.switch_to.default_content()
            
            logger.info(f"Scroll #{total_scrolls}: Found {current_count} cases (previous: {last_count})")
            
            if current_count == last_count:
                no_change_count += 1
                logger.info(f"No new cases found after scroll. Consecutive no-change scrolls: {no_change_count}/{MAX_NO_CHANGE_SCROLLS}")
            else:
                no_change_count = 0  # Reset the counter when we find new cases
                last_count = current_count
                
            # If we're in testing mode and found a case, stop scrolling
            if stop_after_first and len(case_data) > 0:
                break
                
        except Exception as e:
            logger.error(f"Error during scrolling: {e}")
            break
    
    # If we're in testing mode and already have a case, skip the final extraction
    if stop_after_first and len(case_data) > 0:
        driver.quit()
        logger.info(f"Test mode: Using first unprocessed case found during scrolling")
        return case_data
    
    reason = "Maximum scroll attempts reached" if total_scrolls >= SCROLL_ATTEMPTS else "No new cases found after consecutive scrolls"
    if stop_after_first and len(case_data) > 0:
        reason = "Found first unprocessed case for testing"
    logger.info(f"Stopped scrolling: {reason}. Total scrolls: {total_scrolls}, Total cases found: {last_count}")

    # If we get here, we need to do a full extraction (non-testing case or no case found yet)
    case_data = []
    try:
        search_iframe = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.ID, "decisia-iframe"))
        )
        driver.switch_to.frame(search_iframe)
        cases = driver.find_elements(By.CSS_SELECTOR, "div.metadata")
        
        for case in cases:  # Get all cases, no limit
            try:
                a_elem = case.find_element(By.CSS_SELECTOR, "span.title a")
                title = a_elem.text.strip()
                href = a_elem.get_attribute("href")
                full_link = BASE_URL + href if href.startswith("/") else href
                
                # Check if the link has already been scraped
                if full_link in scraped_links:
                    logger.info(f"Skipping already scraped case: {title} (Case number: {scraped_links[full_link]})")
                    continue
                    
                case_data.append({"title": title, "link": full_link})
                
                # If we're in testing mode, stop after finding the first unprocessed case
                if stop_after_first and len(case_data) > 0:
                    logger.info(f"Test mode: Found first unprocessed case, breaking extraction")
                    break
            except Exception as e:
                logger.error(f"Error extracting case link: {e}")
                continue
    except Exception as e:
        logger.error(f"Error switching to iframe: {e}")

    driver.quit()
    logger.info(f"Found {len(case_data)} new cases to scrape")
    return case_data

def save_cases(case_data: List[Dict[str, str]], output_dir: str = OUTPUT_DIR, links_file: str = None) -> int:
    """
    Download and save case HTML content to files, named by case number.
    
    For each case in the input list, downloads the HTML content and saves it
    to a file named with the case number. Skips cases that have already been
    processed.
    
    Args:
        case_data: List of dictionaries containing case information (title, link)
        output_dir: Directory where to save the HTML files
        links_file: Optional custom path to the scraped links file
                   (defaults to SCRAPED_LINKS_FILE from config)
        
    Returns:
        Number of cases successfully processed and saved
        
    Example:
        >>> cases = scrape_cases("...")
        >>> processed = save_cases(cases)
        >>> print(f"Successfully saved {processed} new cases")
    """
    os.makedirs(output_dir, exist_ok=True)
    driver = setup_driver()
    
    processed_count = 0
    for case in case_data:
        try:
            link = case["link"]
            title = case["title"]
            
            # Skip already processed links (double-check)
            scraped_links = load_scraped_links(links_file)
            if link in scraped_links:
                logger.info(f"Skipping already scraped case: {title} (Case number: {scraped_links[link]})")
                continue
                
            driver.get(link)
            time.sleep(3)
            case_iframe = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "decisia-iframe"))
            )
            driver.switch_to.frame(case_iframe)
            
            # Try to extract the case number
            case_number = None
            try:
                case_number_element = driver.find_element(By.XPATH, "//td[text()='Case number']/following-sibling::td")
                case_number = case_number_element.text.strip()
            except Exception as e:
                # If case number is not found, use a fallback
                logger.warning(f"Could not find case number for '{title}': {e}")
                
                # Try to extract a neutral citation as fallback
                try:
                    citation_element = driver.find_element(By.XPATH, "//td[text()='Neutral citation']/following-sibling::td")
                    case_number = f"citation-{citation_element.text.strip()}"
                    logger.info(f"Using neutral citation as fallback identifier for '{title}'")
                except Exception:
                    # Last resort: Use sanitized title and timestamp
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    case_number = f"title-{timestamp}"
                    logger.info(f"Using title and timestamp as fallback identifier for '{title}'")
            
            # Ensure the case number (or fallback) is a valid filename
            case_number = sanitize_filename(case_number)
            file_name = os.path.join(output_dir, f"{case_number}.html")
            
            # If a file with this name already exists, add a timestamp to make it unique
            if os.path.exists(file_name):
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                case_number = f"{case_number}-{timestamp}"
                file_name = os.path.join(output_dir, f"{case_number}.html")
            
            case_content = driver.page_source
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(case_content)
            
            # Save the link to the scraped links file
            save_scraped_link(link, case_number, links_file)
            
            logger.info(f"Saved case {case_number} to {file_name}.")
            processed_count += 1
                
        except Exception as e:
            logger.error(f"Error processing case '{case['title']}': {e}")
            logger.exception("Full error details:")
    
    driver.quit()
    return processed_count

def perform_search(url: str, output_dir: str, base_url: str, max_cases: int = None, links_file: str = None) -> int:
    """
    Orchestrate the complete search and download process for a search URL.
    
    This is the main entry point that coordinates the entire scraping workflow:
    1. Scrape case links from the search URL
    2. Download and save each case's HTML content
    
    Args:
        url: Search URL to scrape
        output_dir: Directory where to save the HTML files
        base_url: Base URL for building full links
        max_cases: Maximum number of cases to process (None for no limit, useful for testing)
        links_file: Optional custom path to the scraped links file
                  (defaults to SCRAPED_LINKS_FILE from config)
        
    Returns:
        Total number of cases processed
        
    Example:
        >>> processed = perform_search("https://decisions.scc-csc.ca/...", "./data/raw", "https://decisions.scc-csc.ca")
        >>> print(f"Processed {processed} cases")
        >>> # For testing with a separate links file
        >>> test_processed = perform_search(url, test_dir, base_url, links_file="./test_links.json")
    """
    # Determine if we're in testing mode
    is_testing = max_cases is not None and max_cases > 0
    
    # Scrape case links - if testing, stop after finding first unprocessed link
    cases = scrape_cases(url, stop_after_first=is_testing)
    
    # Limit number of cases if max_cases is specified
    if max_cases is not None and max_cases > 0:
        cases = cases[:max_cases]
        logger.info(f"Limited to processing {max_cases} cases for testing")
    
    # Save case content (directly named with case numbers)
    processed_count = save_cases(cases, output_dir=output_dir, links_file=links_file)
    
    # Return the number of cases processed
    return processed_count

if __name__ == "__main__":
    total_processed = 0
    for url in SEARCH_URLS:
        cases = scrape_cases(url)
        processed = save_cases(cases, OUTPUT_DIR)
        total_processed += processed
        logger.info(f"Total cases processed so far: {total_processed}")
    
    logger.info(f"Scraping completed. Total cases processed: {total_processed}")
