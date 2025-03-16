# SCC Corpus - Supreme Court of Canada Criminal Cases Corpus

## Project Overview

SCC Corpus is a tool for collecting, processing, and analyzing criminal cases from the Supreme Court of Canada website. The project aims to create a structured corpus of criminal cases that can be used for legal text analysis, NLP research, and legal information retrieval applications.

### Main Features

- **Automated Data Collection**: Web crawler to scrape case data from the SCC website
- **Intelligent Filtering**: Automatic identification and extraction of criminal-related cases
- **Structured Data Extraction**: Parsing key metadata, fact statements, and statutory references from case HTML
- **Checkpoint Recovery**: Support for continuing interrupted scraping sessions without duplicating work
- **Corpus Statistics**: Detailed statistics on corpus size, content distribution, and text characteristics

## Project Structure

```bash
scc-corpus/
├── backend/                # Backend code
│   ├── data/               # Data storage
│   │   ├── raw/            # Raw scraped HTML files
│   │   └── processed/      # Processed JSON data
│   ├── src/                # Main Python code
│   │   ├── __init__.py     # Makes src a Python package
│   │   ├── config.py       # Configuration file (BASE_URL, date ranges, etc.)
│   │   ├── scraper.py      # Web scraping logic, Selenium-related code
│   │   ├── annotator.py    # Case analysis and structured data extraction
│   │   ├── utils.py        # Utility functions (file handling, logging, etc.)
│   │   └── main.py         # Entry script, controls overall process
│   ├── logs/               # Log files
│   └── requirements.txt    # Python dependencies
├── docs/                   # Project documentation
│   ├── data_collection_poc.md       # Data collection proof of concept (English)
│   ├── data_collection_poc_zh.md    # Data collection proof of concept (Chinese)
│   └── README_zh.md                 # Chinese version of README
├── .gitignore              # Git ignore file
└── README.md               # Project documentation (English)
```

## Technical Architecture

The system consists of three main components:

1. **Web Scraper (scraper.py)**:
   - Uses Selenium WebDriver for automated browsing
   - Locates and extracts case links based on date ranges
   - Downloads case HTML content
   - Maintains scraping state to support checkpoint recovery

2. **Annotator (annotator.py)**:
   - Parses HTML content using BeautifulSoup
   - Extracts case metadata (title, date, judges, etc.)
   - Identifies and extracts case facts and statutory references
   - Generates structured JSON output

3. **Main Controller (main.py)**:
   - Coordinates scraping and annotation processes
   - Manages data processing pipeline
   - Handles errors and exceptional situations

## Installation Guide

### Prerequisites

- Python 3.8 or higher
- Chrome browser (required for WebDriver)

### Installation Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/scc-corpus.git
   cd scc-corpus
   ```

2. Install dependencies:

   ```bash
   pip install -r backend/requirements.txt
   ```

## Usage Guide

### Configuration

Before running the system, modify the `config.py` file as needed:

- Adjust date ranges (`DATE_RANGES`)
- Set output paths
- Configure browser options

### Running

```bash
cd backend
python src/main.py
```

### Limiting Test Scope

For testing, you can limit the number of cases per date range:

```python
# Modify the call in main.py
perform_search(driver, start_date, end_date, max_cases=10)
```

### Checking Results

After running, check the output:

```bash
# View the JSON output file
cat data/processed/annotation.json | jq

# View statistics
cat data/processed/annotation_statistics.json | jq

# Check logs
cat logs/scraper.log
cat logs/annotator.log
```

## Known Limitations

- Changes in website HTML structure may affect data extraction
- Older cases may have formats different from modern cases, potentially causing partial data extraction failures
- Token counting uses an estimation method (4 characters ≈ 1 token)

## Current Development Status

- [x] Basic web scraping functionality
- [x] HTML parsing and metadata extraction
- [x] Criminal case filtering
- [x] Facts and statutes extraction
- [x] Original URL recording
- [x] Corpus statistics generation
- [x] Checkpoint recovery system
- [ ] More accurate token counting (currently using estimates)
- [ ] Automated test suite
