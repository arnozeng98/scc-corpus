# Supreme Court of Canada Criminal Cases Corpus Collection

## Overview

This document describes the current implementation for collecting a corpus of criminal cases from the Supreme Court of Canada (SCC). The system scrapes case data from the SCC website, filters for criminal cases, extracts relevant information, and stores it in structured JSON format for further analysis and NLP applications.

## Technical Architecture

The data collection system consists of three main components:

1. **Web Scraper (`scraper.py`)**: Handles web interaction with the SCC database
2. **Annotator (`annotator.py`)**: Processes HTML files and extracts structured data
3. **Main Controller (`main.py`)**: Orchestrates the scraping and annotation workflow

### Web Scraper

The scraper is built using Selenium WebDriver and implements the following functionality:

- **Search Automation**: Automatically submits search queries to the SCC database with configurable date ranges
- **Result Parsing**: Navigates through search result pages and extracts links to individual cases
- **Case Download**: Downloads the full HTML content of each case
- **State Management**: Maintains a record of already scraped links to avoid duplicates

Key functions:

- `setup_driver()`: Configures and initializes a Chrome WebDriver instance
- `load_scraped_links()`: Loads previously downloaded cases to avoid duplicates
- `save_scraped_link()`: Records scraped links with their case numbers
- `scrape_cases()`: Extracts all case links from a search results page
- `save_cases()`: Downloads and saves HTML content for each case
- `perform_search()`: Orchestrates the entire search and download process

### Annotator

The annotator processes downloaded HTML files to extract structured information about each case:

- **Metadata Extraction**: Title, case number, date, judges, etc.
- **Facts Extraction**: Identifies and extracts the 'Facts' section from each case
- **Statute Identification**: Extracts criminal law-related statutes referenced in the case
- **Filtering**: Ensures only criminal cases with complete information are included
- **Statistics Generation**: Calculates and records corpus statistics

Key functions:

- `extract_facts()`: Extracts the 'Facts' section from case HTML
- `extract_statutes()`: Identifies relevant criminal statutes cited in the case
- `find_original_url()`: Retrieves the original source URL for each case
- `annotate_cases()`: Main function that processes all cases and outputs JSON

### Data Flow

1. The main controller initiates searches across specified date ranges
2. The web scraper collects case links and downloads HTML content
3. The annotator processes HTML files to extract structured data
4. A single JSON file containing all criminal cases is created
5. A statistics file is generated to provide corpus metrics

## Installation

### Prerequisites

- Python 3.8 or higher
- Chrome browser (for the WebDriver)

### Dependencies

Install dependencies:

```bash
pip install selenium beautifulsoup4 webdriver-manager tqdm
```

## Running the System

The system can be run through the main.py file. The default configuration will search for criminal cases within the predefined date ranges.

### Basic Execution

```bash
cd backend
python src/main.py
```

### Configuration

Before running, you may want to modify the following settings in `config.py`:

- `DATE_RANGES`: List of tuples defining the search periods
- `RAW_HTML_DIR`: Directory where HTML files will be stored
- `CRIMINAL_CASES_OUTPUT`: Path for the output JSON file
- `LOG_FILE`: Path where logs will be written

Example configuration:

```python
# Chrome Driver configuration
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
```

### Running with Limited Results (Testing)

For testing purposes, you can limit the number of cases downloaded by modifying the `perform_search` function call in `main.py`:

```python
# Limit to 10 cases per date range for testing
perform_search(driver, start_date, end_date, max_cases=10)
```

## Checkpoint Recovery System

The system implements a checkpoint recovery mechanism that enables interrupted scraping sessions to be resumed without duplicating work. This is particularly valuable for handling network issues, server timeouts, or when dealing with large datasets.

### Key Features of the Checkpoint Recovery System

1. **State Persistence**: 
   - All scraped links are continuously saved to `scraped_links.json` after each successful download
   - This file serves as a checkpoint registry, mapping case URLs to case numbers

2. **Automatic Recovery**:
   - When the scraper is restarted, it first loads the previously scraped links
   - All previously downloaded cases are skipped during subsequent runs
   - The system resumes from where it left off, focusing only on new cases

3. **Incremental Processing**:
   - Each date range is processed independently, allowing for targeted resumption
   - If one date range search fails, others can still be completed successfully

4. **Implementation Details**:
   - The `load_scraped_links()` function retrieves the checkpoint data at startup
   - `save_scraped_link()` updates the checkpoint file after each case download
   - `scrape_cases()` checks each link against the checkpoint before processing

### Example Recovery Scenario

1. The system begins scraping with multiple date ranges to process
2. After successfully downloading 200 cases, the process is interrupted
3. When restarted, the system:
   - Loads the 200 already processed cases from `scraped_links.json`
   - Skips re-downloading these cases
   - Continues with remaining unprocessed cases
   - Maintains the same output file structure

This design ensures efficient resource usage, prevents duplication, and provides resilience against interruptions during lengthy scraping processes.

## Manual Inspection

To manually verify the results:

1. Check the produced JSON file for proper structure:

   ```bash
   cat data/processed/annotation.json | jq
   ```

2. Review the statistics file:

   ```bash
   cat data/processed/annotation_statistics.json | jq
   ```

3. Examine log files for any warnings or errors:

   ```bash
   cat logs/scraper.log
   cat logs/annotator.log
   ```

## Data Structure

### Output Format

The criminal cases are stored in a JSON file with the following structure:

```json
[
  {
    "Title": "R. v. Smith",
    "Collection": "Supreme Court Judgments",
    "Date": "March 1, 2021",
    "Neutral Citation": "2021 SCC 10",
    "Case Number": "39227",
    "Judges": "Wagner C.J. and Abella, Moldaver, Karakatsanis, Côté, Brown, Rowe, Martin and Kasirer JJ.",
    "On Appeal From": "Court of Appeal for Ontario",
    "Subjects": "Criminal law",
    "Statutes and Regulations Cited": ["Criminal Code, R.S.C. 1985, c. C-46, s. 486"],
    "Facts": "The defendant was charged with...",
    "Original URL": "https://scc-csc.lexum.com/scc-csc/scc-csc/en/item/1989/index.do"
  },
  ...
]
```

### Statistics

A separate statistics file includes:

```json
{
  "name": "SCC Criminal Cases Corpus Statistics",
  "description": "Statistical analysis of the Supreme Court of Canada criminal cases corpus",
  "generation_date": "2023-05-15",
  "corpus_overview": {
    "total_cases": 123,
    "year_range": "1985 - 2023",
    "total_characters": 1234567,
    "estimated_tokens": 308642
  },
  "case_length": {
    "average_tokens": 2509,
    "average_characters": 10037,
    "min_tokens": 782,
    "min_case": "R. v. Smith",
    "max_tokens": 6543,
    "max_case": "R. v. Jones"
  },
  "legal_content": {
    "total_statutes": 456,
    "average_statutes_per_case": 3.71
  }
}
```

## Known Limitations

- Case detection depends on consistent HTML structure, which can occasionally vary
- The current system handles common variations but may miss some non-standard cases
- Lexical detection of criminal cases could miss some relevant cases if not explicitly labeled
- The token estimation in statistics is approximate (4 chars ≈ 1 token)

## Current Development Status

- [x] Basic web scraping functionality
- [x] HTML parsing and metadata extraction
- [x] Criminal case filtering
- [x] Facts and statutes extraction
- [x] Original URL recording and addition to annotation data
- [x] Corpus statistics generation
- [x] Checkpoint recovery system for interrupted sessions
- [ ] More accurate token counting (currently using an estimate)
- [ ] Automated test suite
