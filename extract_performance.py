"""
Helper functions to extract performance table data.
"""

import re
from bs4 import BeautifulSoup

def extract_performance_table(soup):
    """Extract performance table showing fund vs benchmark returns."""
    performance_data = {}
    
    # Find all tables
    tables = soup.find_all('table')
    
    for table in tables:
        table_text = table.get_text()
        # Check if this looks like a performance table
        if 'return' in table_text.lower() and ('1m' in table_text.lower() or '1 month' in table_text.lower()):
            # Try to parse table rows
            rows = table.find_all('tr')
            headers = []
            
            for i, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                
                if i == 0:
                    # Header row
                    headers = cell_texts
                else:
                    # Data row
                    if len(cell_texts) > 0:
                        row_label = cell_texts[0].lower()
                        
                        # Look for fund name row
                        if 'fund' in row_label or 'direct' in row_label:
                            for j, header in enumerate(headers):
                                if j < len(cell_texts) - 1:
                                    period = header.lower()
                                    value = cell_texts[j + 1]
                                    
                                    # Extract percentage
                                    percent_match = re.search(r'([0-9.+-]+)\s*%', value)
                                    if percent_match:
                                        if '1m' in period or '1 month' in period:
                                            performance_data['fund_1m'] = percent_match.group(1) + '%'
                                        
                        # Look for benchmark row
                        if 'benchmark' in row_label or 'nifty' in row_label:
                            for j, header in enumerate(headers):
                                if j < len(cell_texts) - 1:
                                    period = header.lower()
                                    value = cell_texts[j + 1]
                                    
                                    # Extract percentage
                                    percent_match = re.search(r'([0-9.+-]+)\s*%', value)
                                    if percent_match:
                                        if '1m' in period or '1 month' in period:
                                            performance_data['benchmark_1m'] = percent_match.group(1) + '%'
    
    return performance_data

def extract_category_rank(soup, page_source):
    """Extract category rank from page."""
    # Search in various formats
    patterns = [
        r'category\s+rank[:\s]*(\d+)\s*/\s*(\d+)',
        r'rank[:\s]*(\d+)\s*/\s*(\d+).*category',
        r'ranked\s+(\d+)\s*(?:out\s+of|/)\s*(\d+)',
    ]
    
    # Search in text content
    text = soup.get_text()
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    
    # Search in page source for structured data
    for pattern in patterns:
        match = re.search(pattern, page_source, re.IGNORECASE)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    
    return None


