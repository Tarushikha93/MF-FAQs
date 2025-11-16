"""
Web scraper for official mutual fund information from AMFI and AMC websites.
Fetches data about expense ratio, exit load, minimum SIP, lock-in, riskometer, benchmark, and statements.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re
from urllib.parse import urljoin, urlparse
import time


class MutualFundScraper:
    """Scraper for official mutual fund websites."""
    
    # Official sources for mutual fund data
    AMFI_BASE_URL = "https://www.amfiindia.com"
    AMFI_NAV_URL = "https://www.amfiindia.com/nav-history-download"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Referer': 'https://www.google.com/'
        })
        self.cache = {}
    
    def fetch_page(self, url: str, timeout: int = 10) -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage."""
        try:
            if url in self.cache:
                return self.cache[url]
            
            # Add a small delay to appear more human-like
            import time
            time.sleep(1)
            
            # Update referer to the domain
            domain = url.split('/')[2]
            self.session.headers['Referer'] = f'https://{domain}/'
            
            response = self.session.get(url, timeout=timeout, allow_redirects=True)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            self.cache[url] = soup
            return soup
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def search_amfi_scheme_info(self, scheme_name: str) -> Dict:
        """Search for scheme information on AMFI website."""
        # AMFI provides scheme information through their NAV download
        # This is a placeholder - actual implementation would search their database
        info = {
            'scheme_name': scheme_name,
            'source_url': f"{self.AMFI_BASE_URL}/scheme-information",
            'data': {}
        }
        return info
    
    def get_scheme_factsheet_url(self, amc_name: str, scheme_name: str) -> Optional[str]:
        """Construct URL to scheme factsheet on AMC website."""
        # Common patterns for AMC factsheet URLs
        amc_domains = {
            'sbi': 'https://www.sbimf.com',
            'hdfc': 'https://www.hdfcfund.com',
            'icici': 'https://www.icicipruamc.com',
            'axis': 'https://www.axismf.com',
            'kotak': 'https://www.kotakmutual.com',
            'uti': 'https://www.utimf.com',
            'reliance': 'https://www.reliancemutual.com',
            'aditya birla': 'https://www.adityabirlacapital.com',
        }
        
        amc_lower = amc_name.lower()
        for key, domain in amc_domains.items():
            if key in amc_lower:
                # Most AMCs have factsheets at /schemes/[scheme-name] or similar
                return f"{domain}/schemes"
        
        return None
    
    def extract_fund_details_from_indmoney(self, url: str) -> Dict:
        """Extract fund details from indmoney.com pages."""
        soup = self.fetch_page(url)
        if not soup:
            return {}
        
        details = {
            'scheme_name': None,
            'amc_name': 'HDFC',
            'expense_ratio': None,
            'exit_load': None,
            'minimum_sip': None,
            'lock_in': None,
            'riskometer': None,
            'benchmark': None,
            'statement_download_info': None,
            'source_url': url
        }
        
        # Extract scheme name from URL or page
        scheme_name_elem = soup.find('h1') or soup.find('title')
        if scheme_name_elem:
            scheme_text = scheme_name_elem.get_text(strip=True)
            # Clean up scheme name
            scheme_text = re.sub(r'\s*-\s*Direct.*', '', scheme_text, flags=re.IGNORECASE)
            scheme_text = re.sub(r'\s*Direct Plan.*', '', scheme_text, flags=re.IGNORECASE)
            details['scheme_name'] = scheme_text.strip()
        
        # Extract text content for pattern matching
        text = soup.get_text(separator=' ', strip=True)
        
        # Look for data in structured elements (divs, spans, etc.)
        # Expense Ratio - look for patterns like "0.85%" or "Expense Ratio: 0.85%"
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
        
        # Exit Load - look for patterns like "1%" or "Exit Load: 1%"
        exit_load_patterns = [
            r'exit\s+load[:\s]*([0-9.]+)\s*%',
            r'([0-9.]+)%\s*exit\s+load',
            r'redemption\s+charge[:\s]*([0-9.]+)\s*%',
        ]
        for pattern in exit_load_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                details['exit_load'] = match.group(1) + '%'
                break
        
        # Minimum SIP
        sip_patterns = [
            r'minimum\s+sip[:\s]+(?:rs\.?|₹)?\s*([0-9,]+)',
            r'min\s+investment[:\s]+(?:rs\.?|₹)?\s*([0-9,]+)',
        ]
        for pattern in sip_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                details['minimum_sip'] = '₹' + match.group(1).replace(',', '')
                break
        
        # Lock-in - look for "No Lock-in", "3 years", etc.
        lockin_patterns = [
            r'no\s+lock[-\s]?in',
            r'lock[-\s]?in[:\s]*([0-9]+)\s*years?',
            r'lock[-\s]?in[:\s]*none',
        ]
        for pattern in lockin_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'no' in match.group(0).lower() or 'none' in match.group(0).lower():
                    details['lock_in'] = 'No Lock-in'
                else:
                    details['lock_in'] = match.group(1) + ' years'
                break
        
        # Riskometer - look for risk levels
        risk_patterns = [
            r'riskometer[:\s]*([^.\n]+?)(?:\.|$)',
            r'risk[:\s]*([^.\n]+?)(?:\.|$)',
            r'(very\s+high\s+risk|high\s+risk|moderate\s+risk|low\s+risk)',
        ]
        for pattern in risk_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                risk_text = match.group(1).strip()
                # Normalize risk text
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
        
        # Benchmark
        benchmark_patterns = [
            r'benchmark[:\s]*([^.\n]+?)(?:\.|$)',
            r'benchmark\s+index[:\s]*([^.\n]+?)(?:\.|$)',
        ]
        for pattern in benchmark_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                details['benchmark'] = match.group(1).strip()
                break
        
        # Try to find data in specific HTML elements
        # Look for data in divs with common class names
        for elem in soup.find_all(['div', 'span', 'td', 'li']):
            elem_text = elem.get_text(strip=True)
            # Expense ratio
            if not details['expense_ratio']:
                match = re.search(r'([0-9.]+)%', elem_text)
                if 'expense' in elem_text.lower() and 'ratio' in elem_text.lower() and match:
                    details['expense_ratio'] = match.group(1) + '%'
            # Exit load
            if not details['exit_load']:
                match = re.search(r'([0-9.]+)%', elem_text)
                if 'exit' in elem_text.lower() and 'load' in elem_text.lower() and match:
                    details['exit_load'] = match.group(1) + '%'
            # Risk
            if not details['riskometer']:
                if 'very high risk' in elem_text.lower():
                    details['riskometer'] = 'Very High Risk'
                elif 'high risk' in elem_text.lower() and 'very' not in elem_text.lower():
                    details['riskometer'] = 'High Risk'
            # Lock-in
            if not details['lock_in']:
                if 'no lock-in' in elem_text.lower() or 'no lock in' in elem_text.lower():
                    details['lock_in'] = 'No Lock-in'
        
        return details
    
    def extract_fund_details(self, url: str) -> Dict:
        """Extract fund details from a factsheet or scheme page."""
        # Check if it's an indmoney.com URL
        if 'indmoney.com' in url:
            return self.extract_fund_details_from_indmoney(url)
        
        soup = self.fetch_page(url)
        if not soup:
            return {}
        
        details = {
            'expense_ratio': None,
            'exit_load': None,
            'minimum_sip': None,
            'lock_in': None,
            'riskometer': None,
            'benchmark': None,
            'statement_download_info': None,
            'source_url': url
        }
        
        # Extract text content
        text = soup.get_text(separator=' ', strip=True)
        
        # Pattern matching for common terms
        # Expense Ratio
        expense_pattern = r'expense\s+ratio[:\s]+([0-9.]+)\s*%'
        match = re.search(expense_pattern, text, re.IGNORECASE)
        if match:
            details['expense_ratio'] = match.group(1) + '%'
        
        # Exit Load
        exit_load_pattern = r'exit\s+load[:\s]+([^%\n]+%)'
        match = re.search(exit_load_pattern, text, re.IGNORECASE)
        if match:
            details['exit_load'] = match.group(1).strip()
        
        # Minimum SIP
        sip_pattern = r'minimum\s+sip[:\s]+(?:rs\.?|₹)?\s*([0-9,]+)'
        match = re.search(sip_pattern, text, re.IGNORECASE)
        if match:
            details['minimum_sip'] = '₹' + match.group(1)
        
        # Lock-in (ELSS)
        lockin_pattern = r'lock[-\s]?in[:\s]+([0-9]+)\s*years?'
        match = re.search(lockin_pattern, text, re.IGNORECASE)
        if match:
            details['lock_in'] = match.group(1) + ' years'
        
        # Riskometer
        risk_pattern = r'riskometer[:\s]+([^.\n]+)'
        match = re.search(risk_pattern, text, re.IGNORECASE)
        if match:
            details['riskometer'] = match.group(1).strip()
        
        # Benchmark
        benchmark_pattern = r'benchmark[:\s]+([^.\n]+)'
        match = re.search(benchmark_pattern, text, re.IGNORECASE)
        if match:
            details['benchmark'] = match.group(1).strip()
        
        # Statement download
        statement_pattern = r'statement[:\s]+([^.\n]+download[^.\n]+)'
        match = re.search(statement_pattern, text, re.IGNORECASE)
        if match:
            details['statement_download_info'] = match.group(1).strip()
        
        return details
    
    def search_official_sources(self, query: str, fund_name: str = None) -> List[Dict]:
        """Search official sources for mutual fund information."""
        results = []
        
        # Search AMFI website
        amfi_url = f"{self.AMFI_BASE_URL}/investor-corner"
        soup = self.fetch_page(amfi_url)
        if soup:
            results.append({
                'title': 'AMFI Investor Corner',
                'url': amfi_url,
                'content': soup.get_text(separator=' ', strip=True)[:1000],
                'source': 'AMFI Official'
            })
        
        # If fund name provided, try to find specific fund page
        if fund_name:
            # Try common AMC websites
            common_amcs = ['sbi', 'hdfc', 'icici', 'axis', 'kotak']
            for amc in common_amcs:
                url = self.get_scheme_factsheet_url(amc, fund_name)
                if url:
                    details = self.extract_fund_details(url)
                    if any(details.values()):
                        results.append({
                            'title': f'{amc.upper()} Mutual Fund - {fund_name}',
                            'url': url,
                            'content': str(details),
                            'source': f'{amc.upper()} AMC Official'
                        })
                    break
        
        return results

