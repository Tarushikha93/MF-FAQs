"""
Knowledge base for mutual fund information with source tracking.
Stores information about expense ratio, exit load, minimum SIP, lock-in, riskometer, benchmark, and statements.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class FundInfo:
    """Structure for mutual fund information."""
    scheme_name: str
    amc_name: str
    expense_ratio: Optional[str] = None
    exit_load: Optional[str] = None
    minimum_sip: Optional[str] = None
    lock_in: Optional[str] = None
    riskometer: Optional[str] = None
    benchmark: Optional[str] = None
    statement_download_url: Optional[str] = None
    source_url: Optional[str] = None
    last_updated: Optional[str] = None


class MutualFundKnowledgeBase:
    """Knowledge base for mutual fund queries."""
    
    def __init__(self):
        self.funds: Dict[str, FundInfo] = {}
        self.faqs: List[Dict[str, str]] = []
        self.official_sources = {
            'amfi': 'https://www.amfiindia.com',
            'sebi': 'https://www.sebi.gov.in',
            'amfi_nav': 'https://www.amfiindia.com/nav-history-download',
            'amfi_scheme_info': 'https://www.amfiindia.com/scheme-information'
        }
        self.load_faq_data()
    
    def add_fund_info(self, fund_info: FundInfo):
        """Add or update fund information."""
        key = f"{fund_info.amc_name}_{fund_info.scheme_name}".lower()
        fund_info.last_updated = datetime.now().isoformat()
        self.funds[key] = fund_info
    
    def search_fund(self, query: str) -> List[FundInfo]:
        """Search for funds matching the query."""
        query_lower = query.lower()
        results = []
        
        for fund in self.funds.values():
            if (query_lower in fund.scheme_name.lower() or 
                query_lower in fund.amc_name.lower()):
                results.append(fund)
        
        return results
    
    def load_faq_data(self):
        """Load FAQ data from JSON file."""
        try:
            with open('indmoney_faq_data.json', 'r', encoding='utf-8') as f:
                faq_data = json.load(f)
                self.faqs = faq_data.get('faqs', [])
                print(f"Loaded {len(self.faqs)} FAQs from indmoney_faq_data.json")
        except FileNotFoundError:
            print("FAQ data file not found. Using empty FAQ list.")
            self.faqs = []
        except Exception as e:
            print(f"Error loading FAQ data: {e}")
            self.faqs = []
    
    def search_faq(self, query: str) -> Optional[Dict[str, str]]:
        """Search for FAQ matching the query."""
        query_lower = query.lower()
        
        # Check for exact matches first
        for faq in self.faqs:
            if query_lower == faq['question'].lower():
                return faq
        
        # Check for partial matches
        for faq in self.faqs:
            question_lower = faq['question'].lower()
            # Check if query words are in the question
            query_words = query_lower.split()
            if len(query_words) > 0:
                # If all query words appear in the question
                if all(word in question_lower for word in query_words if len(word) > 2):
                    return faq
        
        # Check for keyword matching
        keywords = {
            'expense ratio': ['expense ratio', 'expense', 'ratio', 'fees', 'charges'],
            'nav': ['nav', 'net asset value', 'asset value'],
            'sip': ['sip', 'systematic investment', 'systematic', 'investment plan'],
            'exit load': ['exit load', 'exit', 'load', 'withdrawal', 'redemption'],
            'aum': ['aum', 'assets under management', 'assets'],
            'risk': ['risk', 'riskometer', 'risk level'],
            'benchmark': ['benchmark', 'index', 'comparison'],
            'tax': ['tax', 'taxation', 'capital gains', 'tax saving'],
        }
        
        # Find matching keywords
        for keyword, related_terms in keywords.items():
            if keyword in query_lower:
                for faq in self.faqs:
                    question_lower = faq['question'].lower()
                    if any(term in question_lower for term in related_terms):
                        return faq
        
        return None
    
    def get_info_by_topic(self, topic: str, fund_name: str = None) -> Dict:
        """Get information about a specific topic."""
        topic_lower = topic.lower()
        
        # Map topics to information fields
        topic_mapping = {
            'expense ratio': 'expense_ratio',
            'expense': 'expense_ratio',
            'exit load': 'exit_load',
            'exit': 'exit_load',
            'minimum sip': 'minimum_sip',
            'sip': 'minimum_sip',
            'lock-in': 'lock_in',
            'lock in': 'lock_in',
            'elss': 'lock_in',
            'riskometer': 'riskometer',
            'risk': 'riskometer',
            'benchmark': 'benchmark',
            'statement': 'statement_download_url',
            'download statement': 'statement_download_url',
            'download': 'statement_download_url'
        }
        
        field = None
        for key, value in topic_mapping.items():
            if key in topic_lower:
                field = value
                break
        
        if not field:
            return {}
        
        # If fund name provided, search for specific fund
        if fund_name:
            funds = self.search_fund(fund_name)
            if funds:
                fund = funds[0]
                value = getattr(fund, field, None)
                if value:
                    return {
                        'topic': topic,
                        'fund': fund.scheme_name,
                        'amc': fund.amc_name,
                        'value': value,
                        'source_url': fund.source_url or self.official_sources['amfi']
                    }
        
        # Return general information with source
        return {
            'topic': topic,
            'general_info': True,
            'source_url': self.official_sources['amfi']
        }
    
    def get_official_source_url(self, topic: str) -> str:
        """Get official source URL for a topic."""
        topic_lower = topic.lower()
        
        if 'statement' in topic_lower or 'download' in topic_lower:
            # For statements, provide AMFI as primary source, but also mention KFintech/CAMS
            return self.official_sources['amfi']
        elif 'expense' in topic_lower or 'exit' in topic_lower or 'sip' in topic_lower:
            return self.official_sources['amfi_scheme_info']
        elif 'risk' in topic_lower or 'benchmark' in topic_lower:
            return self.official_sources['amfi_scheme_info']
        elif 'lock' in topic_lower or 'elss' in topic_lower:
            return self.official_sources['amfi_scheme_info']
        else:
            return self.official_sources['amfi']

