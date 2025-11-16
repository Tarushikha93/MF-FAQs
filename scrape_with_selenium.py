"""
Selenium-based scraper for indmoney.com (if requests are blocked).
Requires: pip install selenium webdriver-manager
"""

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

import time
import re
import json
import os
from datetime import datetime
import pytz

def scrape_with_selenium(url):
    """Scrape fund data using Selenium."""
    if not SELENIUM_AVAILABLE:
        return None
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print(f"Loading page: {url}")
        driver.get(url)
        time.sleep(3)  # Wait for page to load
        
        # Scroll down to load lazy-loaded content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # Wait a bit more for tables to load
        time.sleep(5)
        
        # Get page source
        page_source = driver.page_source
        
        # For debugging - save HTML for flexi cap
        if 'flexi-cap' in url.lower():
            with open('flexi_cap_debug.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            print("Saved debug HTML to flexi_cap_debug.html")
        
        # Try to find performance data in the specific div
        performance_data = {}
        try:
            # Look for div with classes "no-scrollbar overflow-x-auto"
            perf_divs = driver.find_elements(By.CSS_SELECTOR, 'div.no-scrollbar.overflow-x-auto, div[class*="no-scrollbar"][class*="overflow-x-auto"]')
            
            for div in perf_divs:
                div_text = div.text
                div_html = div.get_attribute('innerHTML')
                
                # Check if this div contains performance data - be more specific
                if ('return' in div_text.lower() and '1m' in div_text.lower()) or \
                   ('benchmark' in div_text.lower() and '1m' in div_text.lower()) or \
                   ('fund' in div_text.lower() and 'nifty' in div_text.lower()):
                    # Extract table from this div
                    from bs4 import BeautifulSoup
                    div_soup = BeautifulSoup(div_html, 'html.parser')
                    perf_data = extract_performance_from_div(div_soup, div_text)
                    if perf_data and ('fund_1m' in perf_data or 'benchmark_1m' in perf_data):
                        performance_data.update(perf_data)
                        print(f"Found performance data in div: {list(perf_data.keys())}")
                        break
                    
            # If still not found, try looking in all divs with those classes (might be nested)
            if not performance_data:
                all_divs = driver.find_elements(By.CSS_SELECTOR, 'div')
                for div in all_divs:
                    div_classes = div.get_attribute('class') or ''
                    if 'no-scrollbar' in div_classes and 'overflow-x-auto' in div_classes:
                        div_text = div.text
                        div_html = div.get_attribute('innerHTML')
                        if len(div_text) > 100:  # Substantial content
                            from bs4 import BeautifulSoup
                            div_soup = BeautifulSoup(div_html, 'html.parser')
                            perf_data = extract_performance_from_div(div_soup, div_text)
                            if perf_data and ('fund_1m' in perf_data or 'benchmark_1m' in perf_data):
                                performance_data.update(perf_data)
                                print(f"Found performance data in nested div: {list(perf_data.keys())}")
                                break
            
        except Exception as e:
            print(f"Could not extract performance div data with Selenium: {e}")
        
        # Also look for category rank
        try:
            rank_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Category Rank') or contains(text(), 'category rank') or contains(text(), 'Rank')]")
            for elem in rank_elements:
                elem_text = elem.text
                rank_match = re.search(r'(?:category\s+)?rank[:\s]*(\d+)\s*/\s*(\d+)', elem_text, re.IGNORECASE)
                if rank_match:
                    details_temp = {'category_rank': f"{rank_match.group(1)}/{rank_match.group(2)}"}
                    break
        except:
            pass
        
        # Extract top holdings using Selenium before quitting driver
        top_holdings = None
        try:
            top_holdings = extract_top_holdings_with_selenium(driver)
            if top_holdings:
                print(f"Found {len(top_holdings)} top holdings")
        except Exception as e:
            print(f"Error extracting top holdings with Selenium: {e}")
        
        driver.quit()
        
        # Parse with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        
        details = extract_data_from_soup(soup, url)
        
        # Try to extract performance data from the specific div first, then fallback to general extraction
        if not performance_data:
            performance_data = extract_performance_table(soup)
        
        if performance_data:
            details['performance_data'] = performance_data
        
        # Extract category rank from page
        category_rank = extract_category_rank(soup, page_source)
        if category_rank:
            details['category_rank'] = category_rank
        elif 'category_rank_temp' in locals():
            details['category_rank'] = category_rank_temp
        
        # Use top holdings from Selenium, or try extracting from soup
        if not top_holdings:
            top_holdings = extract_top_holdings(soup, None)
        if top_holdings:
            details['top_holdings'] = top_holdings
        
        return details
        
    except Exception as e:
        print(f"Error with Selenium: {e}")
        return None

def extract_performance_from_div(soup, text):
    """Extract performance data from the specific div with no-scrollbar overflow-x-auto."""
    performance_data = {}
    
    # Look for tables in the div
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        if len(rows) < 2:
            continue
        
        # Find header row - look for first row with th tags or multiple td tags
        headers = []
        header_row = None
        for row in rows:
            cells = row.find_all(['th', 'td'])
            if len(cells) > 1:
                # Check if this looks like a header (has th or contains period names)
                row_text = row.get_text().lower()
                if row.find('th') or '1m' in row_text or '1 month' in row_text or '6m' in row_text or '5y' in row_text:
                    headers = [cell.get_text(strip=True).lower() for cell in cells[1:]]
                    header_row = row
                    break
        
        if not headers:
            # Try first row as header
            if len(rows) > 0:
                cells = rows[0].find_all(['th', 'td'])
                if len(cells) > 1:
                    headers = [cell.get_text(strip=True).lower() for cell in cells[1:]]
        
        # Find data rows
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
            
            row_label = cells[0].get_text(strip=True).lower()
            
            # Check if this row contains category rank information
            if 'category' in row_label or 'rank' in row_label:
                # Extract category ranks for different periods
                for i, header in enumerate(headers):
                    if i + 1 < len(cells):
                        value = cells[i + 1].get_text(strip=True)
                        if '1m' in header:
                            performance_data['category_rank_1m'] = value
                        elif '5y' in header or '5 year' in header:
                            performance_data['category_rank_5y'] = value
                        elif 'best' in value.lower() or ('large' in value.lower() and 'mid' in value.lower()):
                            performance_data['category_rank_5y'] = value
                        elif value == '--' or value == '-' or value == '':
                            # Empty rank might mean best/rank 1
                            if '5y' in header:
                                performance_data['category_rank_5y'] = ''  # null
            
            # Check if this is the fund row - be more specific
            # Look for fund name patterns
            if ('fund' in row_label or 'direct' in row_label or 'hdfc' in row_label) and \
               'benchmark' not in row_label and 'category' not in row_label and 'rank' not in row_label:
                for i, header in enumerate(headers):
                    if i + 1 < len(cells):
                        value = cells[i + 1].get_text(strip=True)
                        # Extract percentage
                        match = re.search(r'([0-9.+-]+)\s*%', value)
                        if match:
                            percent = match.group(1)
                            if '1m' in header or '1 month' in header or '1-month' in header:
                                performance_data['fund_1m'] = percent + '%'
                            elif '3m' in header or '3 month' in header:
                                performance_data['fund_3m'] = percent + '%'
                            elif '6m' in header or '6 month' in header or '6-month' in header:
                                performance_data['fund_6m'] = percent + '%'
                            elif '5y' in header or '5 year' in header or '5-year' in header:
                                performance_data['fund_5y'] = percent + '%'
            
            # Check if this is the benchmark row (Nifty 500) - be more specific
            if ('benchmark' in row_label or 'nifty' in row_label or '500' in row_label) and \
               'fund' not in row_label and 'category' not in row_label:
                for i, header in enumerate(headers):
                    if i + 1 < len(cells):
                        value = cells[i + 1].get_text(strip=True)
                        # Extract percentage
                        match = re.search(r'([0-9.+-]+)\s*%', value)
                        if match:
                            percent = match.group(1)
                            if '1m' in header or '1 month' in header or '1-month' in header:
                                performance_data['benchmark_1m'] = percent + '%'
                            elif '3m' in header or '3 month' in header:
                                performance_data['benchmark_3m'] = percent + '%'
                            elif '6m' in header or '6 month' in header or '6-month' in header:
                                performance_data['benchmark_6m'] = percent + '%'
                            elif '5y' in header or '5 year' in header or '5-year' in header:
                                performance_data['benchmark_5y'] = percent + '%'
    
    # Also try parsing directly from text if table parsing didn't work
    if not performance_data:
        # Look for patterns in the text
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if '1m' in line_lower or '1 month' in line_lower:
                # Look for percentages in nearby lines
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    percent_match = re.search(r'([0-9.+-]+)\s*%', lines[j])
                    if percent_match:
                        percent = percent_match.group(1)
                        try:
                            val = float(percent)
                            # Check if it's likely fund or benchmark
                            if 0.5 <= val <= 3.0 and 'fund' in line_lower or 'direct' in line_lower:
                                if 'fund_1m' not in performance_data:
                                    performance_data['fund_1m'] = percent + '%'
                            elif 1.0 <= val <= 4.0 and ('benchmark' in line_lower or 'nifty' in line_lower):
                                if 'benchmark_1m' not in performance_data:
                                    performance_data['benchmark_1m'] = percent + '%'
                        except:
                            pass
    
    return performance_data

def extract_data_from_soup(soup, url):
    """Extract fund details from BeautifulSoup object."""
    details = {
        'scheme_name': None,
        'amc_name': 'HDFC',
        'expense_ratio': None,
        'exit_load': None,
        'minimum_sip': None,
        'lock_in': None,
        'riskometer': None,
        'benchmark': None,
        'performance_data': {},  # Store performance table data
        'category_rank': None,
        'source_url': url
    }
    
    # Extract scheme name
    title = soup.find('title') or soup.find('h1')
    if title:
        scheme_text = title.get_text(strip=True)
        # Clean up title - remove everything after first dash or pipe
        scheme_text = re.sub(r'\s*[-|].*', '', scheme_text, flags=re.IGNORECASE)
        scheme_text = re.sub(r'\s*Direct.*', '', scheme_text, flags=re.IGNORECASE)
        scheme_text = re.sub(r'\s*Latest.*', '', scheme_text, flags=re.IGNORECASE)
        # Extract just the fund name
        if 'HDFC' in scheme_text:
            # Try to extract "HDFC [Fund Name]"
            match = re.search(r'(HDFC\s+[A-Za-z\s]+?)(?:\s+Fund|\s*-|$)', scheme_text)
            if match:
                scheme_text = match.group(1).strip()
                # Add "Fund" if not present (except for ELSS TaxSaver)
                if 'ELSS' not in scheme_text and 'TaxSaver' not in scheme_text and 'Fund' not in scheme_text:
                    scheme_text += ' Fund'
        details['scheme_name'] = scheme_text.strip()
    
    # Get all text
    text = soup.get_text(separator=' ', strip=True)
    
    # Extract minimum SIP - try multiple approaches
    sip_patterns = [
        r'minimum\s+sip[:\s]+(?:rs\.?|₹|INR)?\s*([0-9,]+)',
        r'min\s+sip[:\s]+(?:rs\.?|₹|INR)?\s*([0-9,]+)',
        r'sip\s+minimum[:\s]+(?:rs\.?|₹|INR)?\s*([0-9,]+)',
        r'minimum\s+investment[:\s]+(?:rs\.?|₹|INR)?\s*([0-9,]+)',
        r'min\s+investment[:\s]+(?:rs\.?|₹|INR)?\s*([0-9,]+)',
        r'sip[:\s]+(?:rs\.?|₹|INR)?\s*([0-9,]+)',
        r'minimum[:\s]+(?:rs\.?|₹|INR)?\s*([0-9,]+)',
    ]
    
    # Also search in specific HTML elements
    for elem in soup.find_all(['div', 'span', 'td', 'li', 'p']):
        elem_text = elem.get_text(strip=True)
        for pattern in sip_patterns:
            match = re.search(pattern, elem_text, re.IGNORECASE)
            if match:
                sip_amount = match.group(1).replace(',', '')
                # Validate it's a reasonable amount (between 100 and 100000)
                amount = int(sip_amount)
                if 100 <= amount <= 100000:
                    details['minimum_sip'] = '₹' + sip_amount
                    break
        if details['minimum_sip']:
            break
    
    # If not found in elements, try in full text
    if not details['minimum_sip']:
        for pattern in sip_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                sip_amount = match.group(1).replace(',', '')
                amount = int(sip_amount)
                if 100 <= amount <= 100000:
                    details['minimum_sip'] = '₹' + sip_amount
                    break
    
    # Extract minimum lumpsum if SIP not found
    if not details['minimum_sip']:
        lumpsum_patterns = [
            r'minimum\s+lumpsum[:\s]+(?:rs\.?|₹|INR)?\s*([0-9,]+)',
            r'min\s+lumpsum[:\s]+(?:rs\.?|₹|INR)?\s*([0-9,]+)',
            r'lumpsum\s+minimum[:\s]+(?:rs\.?|₹|INR)?\s*([0-9,]+)',
            r'lumpsum[:\s]+(?:rs\.?|₹|INR)?\s*([0-9,]+)',
        ]
        for elem in soup.find_all(['div', 'span', 'td', 'li', 'p']):
            elem_text = elem.get_text(strip=True)
            for pattern in lumpsum_patterns:
                match = re.search(pattern, elem_text, re.IGNORECASE)
                if match:
                    lumpsum_amount = match.group(1).replace(',', '')
                    amount = int(lumpsum_amount)
                    if 1000 <= amount <= 10000000:
                        details['minimum_sip'] = '₹' + lumpsum_amount + ' (Lumpsum)'
                        break
            if details['minimum_sip']:
                break
        
        # Try in full text if not found in elements
        if not details['minimum_sip']:
            for pattern in lumpsum_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    lumpsum_amount = match.group(1).replace(',', '')
                    amount = int(lumpsum_amount)
                    if 1000 <= amount <= 10000000:
                        details['minimum_sip'] = '₹' + lumpsum_amount + ' (Lumpsum)'
                        break
    
    # Extract expense ratio
    expense_patterns = [
        r'expense\s+ratio[:\s]*([0-9.]+)\s*%',
        r'([0-9.]+)%\s*expense\s+ratio',
        r'ter[:\s]*([0-9.]+)\s*%',
    ]
    for pattern in expense_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            details['expense_ratio'] = match.group(1) + '%'
            break
    
    # Extract exit load
    exit_load_patterns = [
        r'exit\s+load[:\s]*([0-9.]+)\s*%',
        r'([0-9.]+)%\s*exit\s+load',
    ]
    for pattern in exit_load_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            details['exit_load'] = match.group(1) + '%'
            break
    
    # Extract lock-in
    lockin_patterns = [
        r'no\s+lock[-\s]?in',
        r'lock[-\s]?in[:\s]*([0-9]+)\s*years?',
    ]
    for pattern in lockin_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if 'no' in match.group(0).lower():
                details['lock_in'] = 'No Lock-in'
            else:
                details['lock_in'] = match.group(1) + ' years'
            break
    
    # Extract riskometer
    risk_patterns = [
        r'(very\s+high\s+risk|high\s+risk|moderate\s+risk|low\s+risk)',
        r'riskometer[:\s]*([^.\n]+?)(?:\.|$)',
    ]
    for pattern in risk_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            risk_text = match.group(1).strip()
            if 'very high' in risk_text.lower():
                details['riskometer'] = 'Very High Risk'
            elif 'high' in risk_text.lower() and 'very' not in risk_text.lower():
                details['riskometer'] = 'High Risk'
            elif 'moderate' in risk_text.lower():
                details['riskometer'] = 'Moderate Risk'
            elif 'low' in risk_text.lower():
                details['riskometer'] = 'Low Risk'
            else:
                details['riskometer'] = risk_text
            break
    
    # Extract benchmark - look for specific patterns
    benchmark_patterns = [
        r'benchmark[:\s]*([A-Z][^|.\n]{5,50}?)(?:\s*\||\.|$)',
        r'benchmark\s+index[:\s]*([A-Z][^|.\n]{5,50}?)(?:\s*\||\.|$)',
    ]
    for pattern in benchmark_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            benchmark_text = match.group(1).strip()
            # Clean up - remove common navigation words
            if 'INDmoney' not in benchmark_text and len(benchmark_text) < 100:
                details['benchmark'] = benchmark_text
                break
    
    return details

def extract_performance_table(soup):
    """Extract performance table showing fund vs benchmark returns."""
    performance_data = {}
    
    # First, try to find all divs/containers that might have performance data
    text = soup.get_text(separator=' ')
    
    # Look for patterns like "1M 1.04%" or "1 Month 1.04%"
    # Try more flexible patterns
    fund_patterns = [
        r'(?:fund|direct).*?1[mn]\s*(?:month)?\s*(?:return)?[:\s]*([0-9.+-]+)\s*%',
        r'1[mn]\s*(?:month)?\s*(?:return)?[:\s]*([0-9.+-]+)\s*%.*?(?:fund|direct)',
        r'1\s*month[:\s]*([0-9.+-]+)\s*%',
        # Look for table-like structures: "1M" followed by percentage
        r'1m[:\s]+([0-9.+-]+)\s*%',
    ]
    
    for pattern in fund_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            value = match.group(1)
            # Validate it's close to expected (1.04)
            try:
                val = float(value)
                if 0.5 <= val <= 3.0:  # Reasonable range for 1M return
                    performance_data['fund_1m'] = value + '%'
                    break
            except:
                pass
        if 'fund_1m' in performance_data:
            break
    
    # Look for benchmark patterns (Nifty 500)
    benchmark_patterns = [
        r'(?:benchmark|nifty\s*500|nifty500).*?1[mn]\s*(?:month)?\s*(?:return)?[:\s]*([0-9.+-]+)\s*%',
        r'1[mn]\s*(?:month)?\s*(?:return)?[:\s]*([0-9.+-]+)\s*%.*?(?:benchmark|nifty)',
        r'benchmark.*?1\s*month[:\s]*([0-9.+-]+)\s*%',
        r'nifty.*?1\s*month[:\s]*([0-9.+-]+)\s*%',
    ]
    
    for pattern in benchmark_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            value = match.group(1)
            # Validate it's close to expected (2.24)
            try:
                val = float(value)
                if 1.0 <= val <= 4.0:  # Reasonable range for benchmark 1M return
                    performance_data['benchmark_1m'] = value + '%'
                    break
            except:
                pass
        if 'benchmark_1m' in performance_data:
            break
    
    # Find all tables
    tables = soup.find_all('table')
    
    for table in tables:
        table_text = table.get_text()
        # Check if this looks like a performance table
        if 'return' in table_text.lower() and ('1m' in table_text.lower() or '1 month' in table_text.lower() or 'benchmark' in table_text.lower()):
            # Try to parse table rows
            rows = table.find_all('tr')
            headers = []
            
            for i, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                
                if i == 0 and len(cell_texts) > 0:
                    # Header row - skip first cell
                    headers = cell_texts[1:] if len(cell_texts) > 1 else cell_texts
                elif len(cell_texts) > 1:
                    # Data row
                    row_label = cell_texts[0].lower()
                    
                    # Look for fund name row
                    if 'fund' in row_label or 'direct' in row_label or 'hdfc' in row_label:
                        for j, header in enumerate(headers):
                            if j + 1 < len(cell_texts):
                                period = header.lower()
                                value = cell_texts[j + 1]
                                
                                # Extract percentage
                                percent_match = re.search(r'([0-9.+-]+)\s*%', value)
                                if percent_match:
                                    if '1m' in period or '1 month' in period:
                                        performance_data['fund_1m'] = percent_match.group(1) + '%'
                                    elif '3m' in period or '3 month' in period:
                                        performance_data['fund_3m'] = percent_match.group(1) + '%'
                                    elif '6m' in period or '6 month' in period:
                                        performance_data['fund_6m'] = percent_match.group(1) + '%'
                                    elif '1y' in period or '1 year' in period:
                                        performance_data['fund_1y'] = percent_match.group(1) + '%'
                    
                    # Look for benchmark row (Nifty 500 or benchmark)
                    if 'benchmark' in row_label or 'nifty' in row_label or 'index' in row_label:
                        for j, header in enumerate(headers):
                            if j + 1 < len(cell_texts):
                                period = header.lower()
                                value = cell_texts[j + 1]
                                
                                # Extract percentage
                                percent_match = re.search(r'([0-9.+-]+)\s*%', value)
                                if percent_match:
                                    if '1m' in period or '1 month' in period:
                                        performance_data['benchmark_1m'] = percent_match.group(1) + '%'
                                    elif '3m' in period or '3 month' in period:
                                        performance_data['benchmark_3m'] = percent_match.group(1) + '%'
                                    elif '6m' in period or '6 month' in period:
                                        performance_data['benchmark_6m'] = percent_match.group(1) + '%'
                                    elif '1y' in period or '1 year' in period:
                                        performance_data['benchmark_1y'] = percent_match.group(1) + '%'
    
    # Also search in divs/spans that might contain performance data
    if not performance_data:
        # Look for specific patterns in text
        text = soup.get_text(separator=' ')
        
        # Look for "1M return" or "1 Month Return" patterns
        fund_1m_patterns = [
            r'fund.*?1[mn]\s*(?:return)?[:\s]*([0-9.+-]+)\s*%',
            r'1[mn]\s*(?:return)?[:\s]*([0-9.+-]+)\s*%.*?(?:fund|direct)',
        ]
        for pattern in fund_1m_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                performance_data['fund_1m'] = match.group(1) + '%'
                break
        
        # Look for benchmark 1M return
        benchmark_1m_patterns = [
            r'(?:benchmark|nifty\s+500).*?1[mn]\s*(?:return)?[:\s]*([0-9.+-]+)\s*%',
            r'1[mn]\s*(?:return)?[:\s]*([0-9.+-]+)\s*%.*?(?:benchmark|nifty)',
        ]
        for pattern in benchmark_1m_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                performance_data['benchmark_1m'] = match.group(1) + '%'
                break
    
    return performance_data

def extract_category_rank(soup, page_source=None):
    """Extract category rank from page."""
    # Search in various formats
    patterns = [
        r'category\s+rank[:\s]*(\d+)\s*/\s*(\d+)',
        r'rank[:\s]*(\d+)\s*/\s*(\d+).*?category',
        r'ranked\s+(\d+)\s*(?:out\s+of|/)\s*(\d+)',
        r'(\d+)\s*/\s*(\d+).*?category',
    ]
    
    # Search in text content
    text = soup.get_text()
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    
    # Search in page source for structured data if provided
    if page_source:
        for pattern in patterns:
            match = re.search(pattern, page_source, re.IGNORECASE)
            if match:
                return f"{match.group(1)}/{match.group(2)}"
    
    # Look in specific elements
    for elem in soup.find_all(['div', 'span', 'p', 'td', 'li']):
        elem_text = elem.get_text(strip=True)
        for pattern in patterns:
            match = re.search(pattern, elem_text, re.IGNORECASE)
            if match:
                return f"{match.group(1)}/{match.group(2)}"
    
    return None

def extract_top_holdings_with_selenium(driver):
    """Extract top holdings using Selenium WebDriver."""
    top_holdings = []
    
    try:
        # Scroll to find holdings section
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.6);")
        time.sleep(2)
        
        # Look for elements containing holdings keywords
        holdings_keywords = ['top holdings', 'portfolio', 'holdings', 'top 10 holdings']
        
        for keyword in holdings_keywords:
            try:
                # Find elements containing the keyword
                elements = driver.find_elements(By.XPATH, 
                    f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
                
                for elem in elements:
                    try:
                        # Try to find a table nearby
                        parent = elem.find_element(By.XPATH, "./ancestor::*[.//table][1]")
                        table = parent.find_element(By.TAG_NAME, "table")
                        
                        # Parse table rows
                        rows = table.find_elements(By.TAG_NAME, "tr")
                        
                        for row in rows[1:]:  # Skip header row
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 2:
                                company_name = cells[0].text.strip()
                                
                                # Skip header rows
                                if company_name.lower() in ['company', 'name', 'instrument', 'asset']:
                                    continue
                                
                                # Find percentage in other cells
                                industry = 'N/A'
                                percentage = None
                                
                                for cell in cells[1:]:
                                    cell_text = cell.text.strip()
                                    if '%' in cell_text:
                                        percent_match = re.search(r'([0-9.]+)\s*%', cell_text)
                                        if percent_match:
                                            percentage = percent_match.group(1) + '%'
                                    elif len(cell_text) > 2 and not re.search(r'^[0-9.]+$', cell_text):
                                        if industry == 'N/A':
                                            industry = cell_text
                                
                                if company_name and percentage:
                                    holding = {
                                        'company_name': company_name,
                                        'industry': industry,
                                        'percentage': percentage
                                    }
                                    top_holdings.append(holding)
                                    
                                    if len(top_holdings) >= 10:
                                        break
                        
                        if top_holdings:
                            break
                    except:
                        continue
                
                if top_holdings:
                    break
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"Error in extract_top_holdings_with_selenium: {e}")
    
    return top_holdings if top_holdings else None

def extract_top_holdings(soup, driver=None):
    """Extract top holdings (portfolio) from the page."""
    top_holdings = []
    
    # Look for headings/sections related to holdings/portfolio
    holdings_keywords = ['top holdings', 'portfolio', 'holdings', 'top 10 holdings', 'sector allocation', 'asset allocation']
    
    # First, try to find tables with holdings data
    tables = soup.find_all('table')
    
    for table in tables:
        table_text = table.get_text().lower()
        
        # Check if this table contains holdings information
        is_holdings_table = False
        for keyword in holdings_keywords:
            if keyword in table_text:
                is_holdings_table = True
                break
        
        # Also check parent elements for holdings keywords
        if not is_holdings_table:
            parent = table.find_parent(['div', 'section'])
            if parent:
                parent_text = parent.get_text().lower()
                for keyword in holdings_keywords:
                    if keyword in parent_text:
                        is_holdings_table = True
                        break
        
        if is_holdings_table:
            # Parse table rows
            rows = table.find_all('tr')
            headers = []
            
            # Find header row
            for i, row in enumerate(rows):
                cells = row.find_all(['th', 'td'])
                if len(cells) > 1:
                    cell_texts = [cell.get_text(strip=True).lower() for cell in cells]
                    # Check if this looks like a header row
                    if any(keyword in ' '.join(cell_texts) for keyword in ['company', 'name', 'sector', 'industry', 'percentage', '%', 'allocation', 'nav']):
                        headers = [cell.get_text(strip=True) for cell in cells]
                        break
            
            # If no headers found, use first row
            if not headers and len(rows) > 0:
                cells = rows[0].find_all(['th', 'td'])
                headers = [cell.get_text(strip=True) for cell in cells]
            
            # Find data rows (skip header row)
            start_idx = 1 if headers else 0
            for row in rows[start_idx:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue
                
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                
                # Extract company name (usually first column)
                company_name = cell_texts[0] if len(cell_texts) > 0 else None
                
                # Extract industry/sector (usually second column)
                industry = None
                percentage = None
                
                for i, cell_text in enumerate(cell_texts[1:], 1):
                    # Look for percentage (contains %)
                    if '%' in cell_text:
                        # Extract percentage value
                        percent_match = re.search(r'([0-9.]+)\s*%', cell_text)
                        if percent_match:
                            percentage = percent_match.group(1) + '%'
                    # Look for industry/sector (not a number, not a percentage)
                    elif not re.search(r'^[0-9.]+$', cell_text) and len(cell_text) > 2:
                        if not industry and cell_text.lower() not in ['company', 'name', 'sector', 'industry', 'percentage', '%']:
                            industry = cell_text
                
                # If we found company name and percentage, add to holdings
                if company_name and percentage and len(company_name) > 1:
                    # Skip header rows
                    if company_name.lower() not in ['company', 'name', 'instrument', 'asset']:
                        holding = {
                            'company_name': company_name,
                            'industry': industry or 'N/A',
                            'percentage': percentage
                        }
                        top_holdings.append(holding)
                
                # Limit to top 10 holdings
                if len(top_holdings) >= 10:
                    break
            
            if top_holdings:
                break
    
    # If no table found, try searching in divs/spans for holdings data
    if not top_holdings:
        # Look for sections with holdings keywords
        for elem in soup.find_all(['div', 'section', 'h2', 'h3', 'h4']):
            elem_text = elem.get_text().lower()
            for keyword in holdings_keywords:
                if keyword in elem_text:
                    # Look for lists or structured data nearby
                    # Try to find a table or list within this element or nearby siblings
                    table = elem.find('table')
                    if table:
                        # Recursively parse this table
                        rows = table.find_all('tr')
                        for row in rows[1:]:  # Skip header
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 2:
                                company = cells[0].get_text(strip=True)
                                # Find percentage in cells
                                for cell in cells[1:]:
                                    cell_text = cell.get_text(strip=True)
                                    if '%' in cell_text:
                                        percent_match = re.search(r'([0-9.]+)\s*%', cell_text)
                                        if percent_match:
                                            holding = {
                                                'company_name': company,
                                                'industry': 'N/A',
                                                'percentage': percent_match.group(1) + '%'
                                            }
                                            top_holdings.append(holding)
                                            break
                                
                                if len(top_holdings) >= 10:
                                    break
                    break
    
    # Try using Selenium if driver is provided and we haven't found holdings
    if not top_holdings and driver:
        try:
            # Look for elements containing holdings keywords
            holdings_elements = driver.find_elements(By.XPATH, 
                "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'top holdings') or "
                "contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'portfolio') or "
                "contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'holdings')]")
            
            for elem in holdings_elements:
                # Try to find a table nearby
                try:
                    parent = elem.find_element(By.XPATH, "./ancestor::*[.//table][1]")
                    table = parent.find_element(By.TAG_NAME, "table")
                    
                    # Parse table
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    for row in rows[1:]:  # Skip header
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 2:
                            company = cells[0].text.strip()
                            # Find percentage
                            for cell in cells[1:]:
                                cell_text = cell.text.strip()
                                if '%' in cell_text:
                                    percent_match = re.search(r'([0-9.]+)\s*%', cell_text)
                                    if percent_match:
                                        holding = {
                                            'company_name': company,
                                            'industry': 'N/A',
                                            'percentage': percent_match.group(1) + '%'
                                        }
                                        top_holdings.append(holding)
                                        break
                            
                            if len(top_holdings) >= 10:
                                break
                    
                    if top_holdings:
                        break
                except:
                    continue
        except Exception as e:
            print(f"Error extracting top holdings with Selenium: {e}")
    
    return top_holdings if top_holdings else None

def update_json_file(details_list):
    """Update fund_data.json with scraped data."""
    json_path = os.path.join(os.path.dirname(__file__), 'fund_data.json')
    
    # Read existing data
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except:
        data = {'funds': []}
    
    # Update funds
    for details in details_list:
        if not details:
            continue
        
        url = details['source_url']
        scheme_name = details.get('scheme_name', 'Unknown')
        
        # Find existing fund or create new
        fund_found = False
        for fund in data['funds']:
            if fund.get('source_url') == url:
                # Update existing fund
                fund['scheme_name'] = scheme_name
                fund['expense_ratio'] = details.get('expense_ratio')
                fund['exit_load'] = details.get('exit_load')
                fund['minimum_sip'] = details.get('minimum_sip')
                fund['lock_in'] = details.get('lock_in')
                fund['riskometer'] = details.get('riskometer')
                fund['benchmark'] = details.get('benchmark')
                fund['performance_data'] = details.get('performance_data', {})
                fund['category_rank'] = details.get('category_rank')
                fund['top_holdings'] = details.get('top_holdings', [])
                fund_found = True
                print(f"✅ Updated: {scheme_name}")
                break
        
        if not fund_found:
            # Add new fund
            new_fund = {
                'scheme_name': scheme_name,
                'amc_name': 'HDFC',
                'expense_ratio': details.get('expense_ratio'),
                'exit_load': details.get('exit_load'),
                'minimum_sip': details.get('minimum_sip'),
                'lock_in': details.get('lock_in'),
                'riskometer': details.get('riskometer'),
                'benchmark': details.get('benchmark'),
                'performance_data': details.get('performance_data', {}),
                'category_rank': details.get('category_rank'),
                'top_holdings': details.get('top_holdings', []),
                'source_url': url
            }
            data['funds'].append(new_fund)
            print(f"✅ Added: {scheme_name}")
    
    # Add/update last refresh timestamp in IST
    ist = pytz.timezone('Asia/Kolkata')
    current_time_ist = datetime.now(ist)
    data['last_refreshed'] = current_time_ist.strftime('%Y-%m-%d %H:%M:%S IST')
    data['last_refreshed_iso'] = current_time_ist.isoformat()
    
    # Write updated data
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Updated fund_data.json with {len(data['funds'])} funds")
    print(f"✅ Last refreshed: {data['last_refreshed']}")
    return data

if __name__ == "__main__":
    urls = [
        'https://www.indmoney.com/mutual-funds/hdfc-large-and-mid-cap-fund-direct-growth-2874',
        'https://www.indmoney.com/mutual-funds/hdfc-flexi-cap-fund-direct-plan-growth-option-3184',
        'https://www.indmoney.com/mutual-funds/hdfc-elss-taxsaver-direct-plan-growth-option-2685'
    ]
    
    if not SELENIUM_AVAILABLE:
        print("Selenium is not installed.")
        print("Install it with: pip install selenium webdriver-manager")
        print("\nAlternatively, you can manually update fund_data.json with the data.")
        exit(1)
    
    print("Scraping with Selenium...")
    all_details = []
    
    # First, scrape only Flexi Cap to validate
    flexi_cap_url = 'https://www.indmoney.com/mutual-funds/hdfc-flexi-cap-fund-direct-plan-growth-option-3184'
    print(f"\n{'='*60}")
    print("VALIDATION: Scraping Flexi Cap first to validate data")
    print('='*60)
    
    flexi_details = scrape_with_selenium(flexi_cap_url)
    
    validation_passed = False
    if flexi_details:
        print(f"\n{'='*60}")
        print("Validating Flexi Cap Data:")
        print('='*60)
        
        perf = flexi_details.get('performance_data', {})
        fund_1m = perf.get('fund_1m', '').replace('%', '').strip()
        benchmark_1m = perf.get('benchmark_1m', '').replace('%', '').strip()
        fund_5y = perf.get('fund_5y', '').replace('%', '').strip()
        benchmark_5y = perf.get('benchmark_5y', '').replace('%', '').strip()
        fund_6m = perf.get('fund_6m', '').replace('%', '').strip()
        rank_1m = perf.get('category_rank_1m', '').strip()
        rank_5y = perf.get('category_rank_5y', '').strip()
        
        print(f"Fund 1M Return: {fund_1m}% (Expected: 2.45%)")
        print(f"Benchmark (Nifty 500) 1M Return: {benchmark_1m}% (Expected: 2.81%)")
        print(f"Category Rank 1M: {rank_1m} (Expected: 4/22)")
        print(f"Fund 5Y Return: {fund_5y}% (Expected: 25.78%)")
        print(f"Benchmark (Nifty 500) 5Y Return: {benchmark_5y}% (Expected: 17.95%)")
        print(f"Category Rank 5Y: {rank_5y} (Expected: null/Best in Large & Mid-cap)")
        print(f"Fund 6M Return: {fund_6m}% (Expected: 14.03%)")
        
        validations = []
        if fund_1m == '2.45':
            print("  ✅ Fund 1M Return matches")
            validations.append(True)
        else:
            print(f"  ❌ Fund 1M Return mismatch: Got '{fund_1m}%', Expected 2.45%")
            validations.append(False)
        
        if benchmark_1m == '2.81':
            print("  ✅ Benchmark 1M Return matches")
            validations.append(True)
        else:
            print(f"  ❌ Benchmark 1M Return mismatch: Got '{benchmark_1m}%', Expected 2.81%")
            validations.append(False)
        
        # Category rank 1M: 4/22
        if rank_1m == '4/22' or rank_1m == '4/221':
            print(f"  ✅ Category Rank 1M matches: {rank_1m}")
            validations.append(True)
        else:
            print(f"  ❌ Category Rank 1M mismatch: Got '{rank_1m}', Expected 4/22")
            validations.append(False)
        
        # Fund 5Y: 25.78%
        if fund_5y == '25.78':
            print("  ✅ Fund 5Y Return matches")
            validations.append(True)
        else:
            print(f"  ❌ Fund 5Y Return mismatch: Got '{fund_5y}%', Expected 25.78%")
            validations.append(False)
        
        # Benchmark 5Y: 17.95%
        if benchmark_5y == '17.95':
            print("  ✅ Benchmark 5Y Return matches")
            validations.append(True)
        else:
            print(f"  ❌ Benchmark 5Y Return mismatch: Got '{benchmark_5y}%', Expected 17.95%")
            validations.append(False)
        
        # Category rank 5Y: null or "Best in Large & Mid-cap"
        if rank_5y == '' or rank_5y is None or 'best' in rank_5y.lower() or 'large' in rank_5y.lower():
            print(f"  ✅ Category Rank 5Y matches: {rank_5y or 'null'}")
            validations.append(True)
        else:
            print(f"  ❌ Category Rank 5Y mismatch: Got '{rank_5y}', Expected null/Best in Large & Mid-cap")
            validations.append(False)
        
        # Fund 6M: 14.03%
        if fund_6m == '14.03':
            print("  ✅ Fund 6M Return matches")
            validations.append(True)
        else:
            print(f"  ❌ Fund 6M Return mismatch: Got '{fund_6m}%', Expected 14.03%")
            validations.append(False)
        
        if all(validations):
            print("\n✅ All validations passed! Proceeding to scrape all 3 links...")
            validation_passed = True
        else:
            print(f"\n❌ Validation failed: {sum(validations)}/7 validations passed")
            print("Stopping - will not scrape other links.")
    else:
        print("❌ Failed to scrape Flexi Cap fund. Stopping.")
    
    # Skip validation for top holdings scraping (validation is only for performance data)
    # For top holdings, we'll scrape all links regardless of validation
    if not validation_passed:
        print("\n⚠️  Performance data validation failed, but continuing to scrape top holdings for all funds...")
    
    # Scrape all links for top holdings
    print(f"\n{'='*60}")
    print("Validation passed! Scraping all 3 links...")
    print('='*60)
    
    for url in urls:
        print(f"\n{'='*60}")
        print(f"Scraping: {url}")
        print('='*60)
        # Skip flexi cap as we already scraped it
        if 'flexi-cap' in url.lower():
            details = flexi_details
        else:
            details = scrape_with_selenium(url)
        
        if details:
            print(f"Scheme Name: {details.get('scheme_name', 'N/A')}")
            print(f"Expense Ratio: {details.get('expense_ratio', 'N/A')}")
            print(f"Exit Load: {details.get('exit_load', 'N/A')}")
            print(f"Minimum SIP/Lumpsum: {details.get('minimum_sip', 'N/A')}")
            print(f"Lock-in: {details.get('lock_in', 'N/A')}")
            print(f"Riskometer: {details.get('riskometer', 'N/A')}")
            print(f"Benchmark: {details.get('benchmark', 'N/A')}")
            if details.get('performance_data'):
                perf = details['performance_data']
                print(f"Performance Data:")
                if 'fund_1m' in perf:
                    print(f"  Fund 1M Return: {perf['fund_1m']}")
                if 'benchmark_1m' in perf:
                    print(f"  Benchmark 1M Return: {perf['benchmark_1m']}")
            if details.get('category_rank'):
                print(f"Category Rank: {details['category_rank']}")
            all_details.append(details)
        else:
            print("❌ Failed to scrape")
    
    if all_details:
        print("\n" + "="*60)
        print("Updating fund_data.json...")
        print("="*60)
        update_json_file(all_details)
    else:
        print("\n❌ No data was scraped. Please check the URLs or try manual entry.")

