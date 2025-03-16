import os
import os.path
import sys

# Add src directory to path for direct imports
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, src_dir)
# Also add parent directory to path to import src module
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, parent_dir)

import pytest
from src.scraper import perform_search
from src.config import SEARCH_URLS, BASE_URL

# Define test directories and files
TEST_OUTPUT_DIR = os.path.join("backend", "data", "temp")
TEST_LINKS_FILE = os.path.join("backend", "data", "temp", "test_scraped_links.json")

@pytest.fixture(scope="module")
def setup_test_env():
    """Setup test environment without cleaning up after testing"""
    # Ensure test directory exists
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    
    # Create empty test_scraped_links.json if it doesn't exist
    if not os.path.exists(TEST_LINKS_FILE):
        with open(TEST_LINKS_FILE, 'w', encoding='utf-8') as f:
            f.write('{}')
    
    # No cleanup after tests - files will be preserved for inspection
    yield

def test_perform_search(setup_test_env):
    """Test if perform_search function can successfully scrape and save cases"""
    # Use the first search URL to execute search and save
    # - Using max_cases=1 which enables stop_after_first=True
    # - This will make the scraper stop once it finds the first unprocessed case
    # - It also uses a separate links file to avoid affecting production data
    processed_count = perform_search(
        SEARCH_URLS[0], 
        TEST_OUTPUT_DIR, 
        BASE_URL, 
        max_cases=1,
        links_file=TEST_LINKS_FILE
    )
    
    # Verify cases were processed successfully
    assert processed_count >= 0, "Case processing count should not be negative"
    # If a new case was found, it should be exactly 1
    if processed_count > 0:
        assert processed_count == 1, "Should only process 1 case in test mode"
    
    # Verify function can scrape cases (if new cases are available) or handle already scraped cases
    saved_files = [f for f in os.listdir(TEST_OUTPUT_DIR) if f.endswith('.html')]
    
    # If new cases were saved, verify file format
    if processed_count > 0:
        assert len(saved_files) > 0, "No files were saved"
        
        # Check if at least one file contains the necessary HTML structure
        test_file = os.path.join(TEST_OUTPUT_DIR, saved_files[0])
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "<html" in content.lower(), "Saved file is not valid HTML"
            assert "case number" in content.lower(), "HTML content is missing case information"

if __name__ == "__main__":
    # Get absolute path to the test file
    test_file_abs = os.path.abspath(__file__)
    
    # Add backend directory to the Python path if running from inside tests/
    backend_dir = os.path.dirname(os.path.dirname(test_file_abs))
    if not backend_dir in sys.path:
        sys.path.insert(0, backend_dir)
    
    # Run pytest with the absolute path to the test file
    pytest.main(["-v", test_file_abs])