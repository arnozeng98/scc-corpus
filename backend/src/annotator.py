import os
import re
from typing import Dict, List, Any, Optional, Union
from bs4 import BeautifulSoup, Tag
from config import ANNOTATOR_LOG_FILE, CRIMINAL_CASES_OUTPUT, SCRAPED_LINKS_FILE
from utils import setup_logging, save_json_file, ensure_dir_exists, load_json_file
import datetime

# Set up logging
logger = setup_logging(ANNOTATOR_LOG_FILE)

# Regex pattern to match statutes related to Criminal cases
criminal_regex = re.compile(r"Criminal", re.IGNORECASE)

def extract_facts(soup: BeautifulSoup) -> str:
    """
    Extract the 'Facts' section from a case HTML document.
    
    Locates the 'Facts' section in the document by finding an underlined
    header containing the word 'facts', then extracts all content until
    the next underlined header. This captures the complete facts section
    of a legal case.
    
    Args:
        soup: BeautifulSoup object of the parsed HTML document
        
    Returns:
        String containing the extracted facts or an empty string if not found
        
    Example:
        >>> with open("case_12345.html", "r") as f:
        >>>     soup = BeautifulSoup(f, "html.parser")
        >>> facts = extract_facts(soup)
        >>> print(f"Extracted {len(facts)} characters of facts")
    """
    facts_content = []
    found_facts = False
    elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    for element in elements:
        if found_facts:
            # Check for the next underlying section to stop
            if element.find('u'):
                break
            facts_content.append(element.get_text(strip=True))
        elif element.find('u') and 'facts' in element.get_text(strip=True).lower():
            found_facts = True
    return ' '.join(facts_content)

def extract_statutes(soup: BeautifulSoup) -> List[str]:
    """
    Extract statutes and regulations cited in a case that are related to criminal law.
    
    Finds the 'Statutes and Regulations Cited' section in the document,
    and extracts all paragraphs that contain the word 'Criminal'.
    
    Args:
        soup: BeautifulSoup object of the parsed HTML document
        
    Returns:
        List of strings, each representing a statute related to criminal law
        
    Example:
        >>> with open("case_12345.html", "r") as f:
        >>>     soup = BeautifulSoup(f, "html.parser")
        >>> statutes = extract_statutes(soup)
        >>> for statute in statutes:
        >>>     print(f"Found statute: {statute}")
    """
    content = []
    statutes_start = soup.find('b', text='Statutes and Regulations Cited')
    if statutes_start:
        current = statutes_start.find_next('p')
        while current and current.find('b') is None:
            if 'Authors Cited' in current.text:
                break
            text = current.text.strip()
            if text and criminal_regex.search(text):
                content.append(text)
            current = current.find_next('p')
    return content

def find_original_url(case_number: str, scraped_links: Dict[str, str]) -> str:
    """
    Find the original URL for a case based on its case number.
    
    This function performs a reverse lookup in the scraped_links dictionary
    to find the URL corresponding to a given case number.
    
    Args:
        case_number: The case number to look up
        scraped_links: Dictionary mapping URLs to case numbers
        
    Returns:
        Original URL of the case or an empty string if not found
        
    Example:
        >>> links = load_json_file(SCRAPED_LINKS_FILE, default={})
        >>> url = find_original_url("12345", links)
        >>> print(f"Original URL: {url}")
    """
    # Perform reverse lookup in the scraped_links dictionary
    for url, number in scraped_links.items():
        if number == case_number:
            return url
    
    # Handle prefixed case numbers (from fallback mechanisms in scraper)
    for url, number in scraped_links.items():
        # Check for citation or title prefixes and timestamps
        if (case_number.startswith("citation-") or 
            case_number.startswith("title-") or 
            "-" in case_number) and number in case_number:
            return url
    
    return ""

def annotate_cases(directory: str, output_filename: str) -> List[Dict[str, Any]]:
    """
    Process HTML case files to extract structured information and save as JSON.
    
    For each HTML file in the directory:
    1. Parses the HTML and extracts metadata (title, case number, etc.)
    2. Extracts facts and statutes related to criminal law
    3. Finds the original URL for each case
    4. Filters to include only criminal cases with complete metadata
    5. Saves the results to a JSON file
    
    Args:
        directory: Path to directory containing HTML case files
        output_filename: Path where to save the JSON output file
        
    Returns:
        List of dictionaries, each representing a processed criminal case
        
    Example:
        >>> cases = annotate_cases("./data/raw", "./data/criminal_cases.json")
        >>> print(f"Processed {len(cases)} criminal cases")
    """
    all_cases = []
    case_files = [f for f in os.listdir(directory) if f.endswith(".html")]
    logger.info(f"Found {len(case_files)} case files to annotate")
    
    # Load the mapping of URLs to case numbers from scraped_links.json
    scraped_links = load_json_file(SCRAPED_LINKS_FILE, default={})
    logger.info(f"Loaded {len(scraped_links)} scraped link records for URL lookup")
    
    for filename in case_files:
        filepath = os.path.join(directory, filename)
        try:
            # Extract case number from filename (remove .html extension)
            file_case_number = filename[:-5] if filename.endswith(".html") else filename
            
            with open(filepath, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')

                # Extract the basic metadata
                title = soup.find('h3', class_='title').text.strip() if soup.find('h3', class_='title') else None
                collection = soup.find('td', text='Collection').find_next_sibling('td').text.strip() if soup.find('td', text='Collection') else None
                date = soup.find('td', text='Date').find_next_sibling('td').text.strip() if soup.find('td', text='Date') else None
                neutral_citation = soup.find('td', text='Neutral citation').find_next_sibling('td').text.strip() if soup.find('td', text='Neutral citation') else None
                case_number = soup.find('td', text='Case number').find_next_sibling('td').text.strip() if soup.find('td', text='Case number') else None
                judges = soup.find('td', text='Judges').find_next_sibling('td').text.strip() if soup.find('td', text='Judges') else None
                on_appeal_from = soup.find('td', text='On appeal from').find_next_sibling('td').text.strip() if soup.find('td', text='On appeal from') else None
                subjects = soup.find('td', text='Subjects').find_next_sibling('td').text.strip() if soup.find('td', text='Subjects') else None

                # Find original URL using the case number from the filename
                original_url = find_original_url(file_case_number, scraped_links)
                
                # Extract and filter Statutes and Regulations Cited
                statutes_text = extract_statutes(soup)
                # Extract facts
                facts = extract_facts(soup)

                # Only append cases with 'Criminal' in subjects and non-empty essential metadata
                if subjects and 'Criminal' in subjects and all([title, case_number, collection, date]) and statutes_text:
                    all_cases.append({
                        'Title': title,
                        'Collection': collection,
                        'Date': date,
                        'Neutral Citation': neutral_citation,
                        'Case Number': case_number,
                        'Judges': judges,
                        'On Appeal From': on_appeal_from,
                        'Subjects': subjects,
                        'Statutes and Regulations Cited': statutes_text,
                        'Facts': facts,  # Facts section
                        'Original URL': original_url  # Adding the original URL
                    })
                    logger.info(f"Processed case: {title} (Case number: {case_number})")
                    if original_url:
                        logger.info(f"Found original URL for case {case_number}: {original_url}")
                    else:
                        logger.warning(f"Could not find original URL for case {case_number}")
                else:
                    if not subjects or 'Criminal' not in subjects:
                        logger.info(f"Skipping non-criminal case: {title}")
                    elif not all([title, case_number, collection, date]):
                        logger.info(f"Skipping case with incomplete metadata: {title}")
                    elif not statutes_text:
                        logger.info(f"Skipping case without statutes: {title}")
        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")

    # Save data as JSON
    success = save_json_file(output_filename, all_cases, indent=4)
    if success:
        logger.info(f"Filtered data has been saved to '{output_filename}' ({len(all_cases)} cases)")
    else:
        logger.error(f"Failed to save filtered data to '{output_filename}'")
    
    # Generate corpus statistics
    if all_cases:
        try:
            # Import token-counting library if needed
            # For demonstration we'll use character counts and word estimates
            # In production, you might want to use tiktoken or another tokenizer
            
            # Character counts for all documents
            char_counts = [len(case['Facts']) for case in all_cases if 'Facts' in case]
            
            # Estimate token counts (rough approximation: 4 chars ≈ 1 token)
            token_counts = [count // 4 for count in char_counts]
            
            # Count statutes
            statute_counts = [len(case['Statutes and Regulations Cited']) for case in all_cases]
            
            # Calculate statistics
            total_cases = len(all_cases)
            total_chars = sum(char_counts)
            total_tokens = sum(token_counts)
            total_statutes = sum(statute_counts)
            
            # Find cases with min/max lengths
            min_idx = token_counts.index(min(token_counts))
            max_idx = token_counts.index(max(token_counts))
            min_case = all_cases[min_idx]['Title']
            max_case = all_cases[max_idx]['Title']
            
            # Years coverage
            years = [case['Date'].split()[-1] for case in all_cases if 'Date' in case]
            year_range = f"{min(years)} - {max(years)}" if years else "N/A"
            
            # Output statistics
            logger.info("\n" + "="*50)
            logger.info("CORPUS STATISTICS")
            logger.info("="*50)
            logger.info(f"Total number of cases: {total_cases}")
            logger.info(f"Year range: {year_range}")
            logger.info(f"Total character count: {total_chars:,}")
            logger.info(f"Estimated token count: {total_tokens:,}")
            logger.info(f"Average case length: {total_tokens//total_cases:,} tokens ({total_chars//total_cases:,} characters)")
            logger.info(f"Shortest case: {min(token_counts):,} tokens ({min_case})")
            logger.info(f"Longest case: {max(token_counts):,} tokens ({max_case})")
            logger.info(f"Total statutes cited: {total_statutes}")
            logger.info(f"Average statutes per case: {total_statutes/total_cases:.2f}")
            logger.info("="*50)
            
            # Create a separate statistics file
            stats = {
                "name": "SCC Criminal Cases Corpus Statistics",
                "description": "Statistical analysis of the Supreme Court of Canada criminal cases corpus",
                "generation_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "corpus_overview": {
                    "total_cases": total_cases,
                    "year_range": year_range,
                    "total_characters": total_chars,
                    "estimated_tokens": total_tokens
                },
                "case_length": {
                    "average_tokens": total_tokens//total_cases,
                    "average_characters": total_chars//total_cases,
                    "min_tokens": min(token_counts),
                    "min_case": min_case,
                    "max_tokens": max(token_counts),
                    "max_case": max_case
                },
                "legal_content": {
                    "total_statutes": total_statutes,
                    "average_statutes_per_case": total_statutes/total_cases
                }
            }
            
            # Save statistics to a separate file
            stats_filename = output_filename.replace('.json', '_statistics.json')
            save_json_file(stats_filename, stats, indent=4)
            logger.info(f"Corpus statistics saved to {stats_filename}")
            
        except Exception as e:
            logger.error(f"Error generating corpus statistics: {e}")
    
    return all_cases
