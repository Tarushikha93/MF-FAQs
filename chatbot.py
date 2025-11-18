"""
Main chatbot engine that answers questions about mutual funds.
Ensures every answer includes a source link and provides no advice.
"""

import os
import json
from typing import Dict, List, Optional
from knowledge_base import MutualFundKnowledgeBase, FundInfo
from mutual_fund_scraper import MutualFundScraper
from fund_repository import FundRepository
from data_manager import FundDataManager
import re

# Try to import dotenv, but make it optional
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try to import OpenAI, but make it optional
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Try to import Google Gemini, but make it optional
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class MutualFundChatbot:
    """Chatbot for answering mutual fund questions with source citations."""
    
    def __init__(self):
        self.knowledge_base = MutualFundKnowledgeBase()
        self.scraper = MutualFundScraper()
        self.openai_client = None
        self.gemini_model = None
        self.allowed_sources = set()  # Track allowed source URLs
        
        # Initialize repository and data manager
        self.repository = FundRepository()
        self.data_manager = FundDataManager()
        
        # Initialize OpenAI if available
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
        
        # Initialize Gemini if available
        if GEMINI_AVAILABLE:
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        # Load data from JSON file
        self._load_fund_data()
    
    def _load_fund_data(self):
        """Load fund data from JSON file."""
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'fund_data.json')
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            for fund_data in data.get('funds', []):
                fund_info = FundInfo(
                    scheme_name=fund_data.get('scheme_name', ''),
                    amc_name=fund_data.get('amc_name', ''),
                    expense_ratio=fund_data.get('expense_ratio'),
                    exit_load=fund_data.get('exit_load'),
                    minimum_sip=fund_data.get('minimum_sip'),
                    lock_in=fund_data.get('lock_in'),
                    riskometer=fund_data.get('riskometer'),
                    benchmark=fund_data.get('benchmark'),
                    statement_download_url=None,
                    source_url=fund_data.get('source_url')
                )
                self.knowledge_base.add_fund_info(fund_info)
                if fund_info.source_url:
                    self.allowed_sources.add(fund_info.source_url)
            
            # Loaded successfully (suppress print in production)
            pass
        except Exception as e:
            print(f"Error loading fund data: {e}")
    
    def extract_fund_name(self, query: str) -> Optional[str]:
        """Extract fund name from query if present."""
        query_lower = query.lower()
        
        # Check against known fund names in knowledge base
        for fund in self.knowledge_base.funds.values():
            fund_name_lower = fund.scheme_name.lower()
            # Check if query contains key words from fund name
            fund_keywords = fund_name_lower.split()
            # Remove common words
            fund_keywords = [w for w in fund_keywords if w not in ['fund', 'the', 'and', 'a', 'an']]
            
            # Check if significant keywords match
            matches = sum(1 for keyword in fund_keywords if keyword in query_lower)
            if matches >= 2 or (matches >= 1 and len(fund_keywords) <= 3):
                return fund.scheme_name
        
        # Pattern matching fallback
        patterns = [
            r'(?:hdfc\s+)?(?:large\s+and\s+mid\s+cap|flexi\s+cap|elss\s+taxsaver)',
            r'(?:fund|scheme)\s+([A-Z][A-Za-z\s]+(?:Fund|Scheme)?)',
            r'([A-Z][A-Za-z\s]+(?:Fund|Scheme)?)\s+(?:mutual\s+fund|mf|scheme)',
            r'(HDFC)\s+(Large\s+and\s+Mid\s+Cap|Flexi\s+Cap|ELSS\s+TaxSaver)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if len(match.groups()) > 1:
                    result = f"{match.group(1)} {match.group(2)}".strip()
                else:
                    result = match.group(1).strip()
                
                # Try to match with known funds
                for fund in self.knowledge_base.funds.values():
                    if result.lower() in fund.scheme_name.lower() or fund.scheme_name.lower() in result.lower():
                        return fund.scheme_name
                
                return result
        
        return None
    
    def identify_topic(self, query: str) -> str:
        """Identify the topic of the query."""
        query_lower = query.lower()
        
        # Check for fund listing/rank queries first
        if any(keyword in query_lower for keyword in ['what fund', 'list fund', 'fund information', 'which fund', 'funds do you have', 'tell me about fund']):
            if 'rank' in query_lower:
                return 'fund_list_with_ranks'
            return 'fund_list'
        
        topics = {
            'expense ratio': ['expense ratio', 'expense', 'ter', 'total expense ratio'],
            'exit load': ['exit load', 'exit', 'redemption charge'],
            'minimum sip': ['minimum sip', 'sip minimum', 'minimum investment', 'sip amount'],
            'lock-in': ['lock-in', 'lock in', 'lockin', 'elss', 'lock period'],
            'riskometer': ['riskometer', 'risk', 'risk level', 'risk rating'],
            'benchmark': ['benchmark', 'index', 'comparison'],
            'statement': ['statement', 'download statement', 'account statement', 'consolidated statement']
        }
        
        for topic, keywords in topics.items():
            if any(keyword in query_lower for keyword in keywords):
                return topic
        
        return 'general'
    
    def generate_answer_with_llm(self, query: str, context: Dict, source_url: str) -> str:
        """Generate answer using LLM if available, otherwise use template."""
        
        # Build context string
        context_str = ""
        if context.get('fund'):
            context_str += f"Fund: {context.get('fund')}\n"
        if context.get('amc'):
            context_str += f"AMC: {context.get('amc')}\n"
        if context.get('value'):
            context_str += f"Information: {context.get('value')}\n"
        
        prompt = f"""You are a factual information assistant for mutual funds. Answer the following question using ONLY the provided information. 
Do NOT provide any investment advice. Only state facts.

Question: {query}

Context: {context_str}

Instructions:
1. Answer the question factually based on the context
2. Do NOT provide investment advice or recommendations
3. State that this is general information and may vary by fund
4. Always mention that investors should check official sources
5. Keep the answer concise and factual

Answer:"""
        
        # Try Gemini first (if available), then OpenAI, then fallback to template
        if self.gemini_model:
            try:
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.3,
                        'max_output_tokens': 200,
                    }
                )
                answer = response.text.strip()
                return answer
            except Exception as e:
                print(f"Gemini error: {e}, trying OpenAI...")
        
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a factual information assistant. You provide only factual information about mutual funds with no investment advice."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.3
                )
                answer = response.choices[0].message.content.strip()
                return answer
            except Exception as e:
                print(f"OpenAI error: {e}, using template")
        
        # Fallback to template-based answer
        return self.generate_template_answer(query, context, source_url)
    
    def generate_template_answer(self, query: str, context: Dict, source_url: str) -> str:
        """Generate answer using templates."""
        topic = context.get('topic', 'general')
        value = context.get('value', '')
        fund = context.get('fund', '')
        
        templates = {
            'expense ratio': f"The expense ratio represents the annual cost of managing the fund. {f'For {fund}, the expense ratio is {value}.' if value else 'Expense ratios vary by fund and are disclosed in the scheme information document.'} This information is available on official AMC websites and AMFI.",
            'exit load': f"Exit load is a charge levied when you redeem units before a specified period. {f'For {fund}, the exit load is {value}.' if value else 'Exit loads vary by fund and redemption period.'} Check the scheme information document for specific details.",
            'minimum sip': f"The minimum SIP (Systematic Investment Plan) amount varies by fund. {f'For {fund}, the minimum SIP is {value}.' if value else 'Most funds have a minimum SIP of ₹500, but this can vary.'} This information is available in the scheme information document.",
            'lock-in': f"Lock-in period refers to the minimum period you must hold the investment. {f'For {fund}, the lock-in period is {value}.' if value else 'ELSS funds typically have a 3-year lock-in period. Other funds may have different lock-in periods.'} Check the scheme information document for specific details.",
            'riskometer': f"The riskometer indicates the risk level of a mutual fund scheme. {f'For {fund}, the riskometer rating is {value}.' if value else 'Riskometer ratings range from Low to Very High and are displayed in scheme documents.'} This is available in the scheme information document and factsheet.",
            'benchmark': f"The benchmark is an index used to compare the fund's performance. {f'For {fund}, the benchmark is {value}.' if value else 'Each fund has a specific benchmark index mentioned in its scheme information document.'} This information is available in the scheme factsheet.",
            'statement': f"To download your mutual fund statement, you can: 1) Visit your AMC's official website and log into the investor portal, 2) Use the Consolidated Account Statement (CAS) service from KFintech (https://www.kfintech.com) or CAMS (https://www.camsonline.com), 3) Check AMFI's website for consolidated statement services. {f'For {fund}, visit: {value}' if value else 'Most AMCs provide statement download options in their investor portal.'} All these are official sources for downloading statements."
        }
        
        answer = templates.get(topic, f"Information about {topic} is available on official mutual fund websites and AMFI. Please check the scheme information document for specific details.")
        
        # Add disclaimer
        answer += "\n\nNote: This is general information. Specific details may vary by fund. Please refer to official sources and scheme documents for accurate information. This is not investment advice."
        
        return answer
    
    def get_source_link(self, topic: str, fund_name: str = None) -> str:
        """Get appropriate source link for the query."""
        if fund_name:
            # Try to get fund-specific URL
            funds = self.knowledge_base.search_fund(fund_name)
            if funds and funds[0].source_url:
                return funds[0].source_url
        
        # Return topic-specific official source
        return self.knowledge_base.get_official_source_url(topic)
    
    def contains_personal_info(self, query: str) -> bool:
        """Check if query contains personal information like PAN, Aadhaar, account numbers, OTP, email, phone."""
        query_lower = query.lower()
        
        # Check for explicit mentions of personal information types
        personal_info_keywords = [
            'pan card', 'pan number', 'pan no',
            'aadhaar', 'aadhar', 'uidai',
            'account number', 'account no', 'acc no', 'account num',
            'otp', 'one time password', 'verification code',
            'phone number', 'mobile number', 'contact number', 'phone no', 'mobile no',
            '@',  # Email indicator
        ]
        
        # Check for keywords first
        for keyword in personal_info_keywords:
            if keyword in query_lower:
                return True
        
        # Patterns for specific formats (more strict to avoid false positives)
        personal_info_patterns = [
            r'\b[A-Z]{5}\d{4}[A-Z]{1}\b',  # PAN card format: ABCDE1234F (uppercase)
            r'\b[a-z]{5}\d{4}[a-z]{1}\b',  # PAN card format: abcde1234f (lowercase)
            r'\b\d{4}\s?\d{4}\s?\d{4}\b',  # Aadhaar (12 digits with optional spaces)
            r'\b\d{12}\b',  # Aadhaar (12 consecutive digits) - but be careful of false positives
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
            r'\b\+91\s?\d{10}\b',  # Indian phone number with country code
            r'\b\d{10}\s+(?:phone|mobile|contact)',  # 10 digits followed by phone/mobile/contact
        ]
        
        for pattern in personal_info_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        return False
    
    def answer_question(self, query: str) -> Dict[str, str]:
        """Answer a question about mutual funds. Only uses data from allowed sources."""
        # Check for personal information first
        if self.contains_personal_info(query):
            return {
                'answer': "I'm sorry, but I cannot and will not accept, process, or store any personal information such as PAN card numbers, Aadhaar numbers, account numbers, OTPs, email addresses, or phone numbers. For security reasons, please do not share such information. If you need assistance with account-related matters, please contact your AMC (Asset Management Company) directly through their official channels.",
                'source_url': None,
                'topic': 'personal_info_declined'
            }
        
        # Identify topic
        topic = self.identify_topic(query)
        
        # Handle fund listing queries
        if topic == 'fund_list' or topic == 'fund_list_with_ranks':
            return self._answer_fund_list_query(query, topic)
        
        # First check if this is a general FAQ query
        faq_result = self.knowledge_base.search_faq(query)
        if faq_result:
            return {
                'answer': faq_result['answer'],
                'source': faq_result.get('source_url', 'INDmoney'),
                'topic': 'general',
                'fund': None
            }
        
        # Extract fund name if present
        fund_name = self.extract_fund_name(query)
        
        # Get information from knowledge base (only from loaded data)
        info = self.knowledge_base.get_info_by_topic(topic, fund_name)
        
        # If fund name provided, try to get data directly from fund
        if fund_name:
            funds = self.knowledge_base.search_fund(fund_name)
            if funds:
                fund = funds[0]
                # Get the field for this topic
                topic_field_map = {
                    'expense ratio': 'expense_ratio',
                    'exit load': 'exit_load',
                    'minimum sip': 'minimum_sip',
                    'lock-in': 'lock_in',
                    'riskometer': 'riskometer',
                    'risk': 'riskometer',
                    'benchmark': 'benchmark',
                    'statement': 'statement_download_url',
                    'download statement': 'statement_download_url'
                }
                field = topic_field_map.get(topic.lower())
                if field:
                    value = getattr(fund, field, None)
                    if value:
                        info = {
                            'topic': topic,
                            'fund': fund.scheme_name,
                            'amc': fund.amc_name,
                            'value': value,
                            'source_url': fund.source_url
                        }
        
        # Check if we have information from allowed sources
        source_url = info.get('source_url')
        
        # If no info found or source not in allowed sources, return out-of-context message
        if not info.get('value'):
            return {
                'answer': "I'm sorry I cannot answer this question of yours. Kindly visit the official website https://v.hdfcbank.com/htdocs/common/focus-funds/LP.html",
                'source_url': None,
                'topic': topic
            }
        
        # Verify source URL is in allowed sources
        if source_url and source_url not in self.allowed_sources:
            # Try to find a matching fund with allowed source
            if fund_name:
                funds = self.knowledge_base.search_fund(fund_name)
                for fund in funds:
                    if fund.source_url and fund.source_url in self.allowed_sources:
                        source_url = fund.source_url
                        # Get the value for the topic
                        topic_field = {
                            'expense ratio': 'expense_ratio',
                            'exit load': 'exit_load',
                            'minimum sip': 'minimum_sip',
                            'lock-in': 'lock_in',
                            'riskometer': 'riskometer',
                            'benchmark': 'benchmark'
                        }.get(topic.lower())
                        if topic_field:
                            value = getattr(fund, topic_field, None)
                            if value:
                                info['value'] = value
                                info['fund'] = fund.scheme_name
                                info['amc'] = fund.amc_name
                                break
            
            # If still no valid source, return out-of-context message
            if not source_url or source_url not in self.allowed_sources:
                return {
                    'answer': "I'm sorry I cannot answer this question of yours. Kindly visit the official website https://v.hdfcbank.com/htdocs/common/focus-funds/LP.html",
                    'source_url': None,
                    'topic': topic
                }
        
        # Ensure source URL is from allowed sources
        if not source_url or source_url not in self.allowed_sources:
            # Try to get source from fund info
            if fund_name:
                funds = self.knowledge_base.search_fund(fund_name)
                if funds and funds[0].source_url and funds[0].source_url in self.allowed_sources:
                    source_url = funds[0].source_url
                else:
                    return {
                        'answer': "I'm sorry I cannot answer this question of yours. Kindly visit the official website https://v.hdfcbank.com/htdocs/common/focus-funds/LP.html",
                        'source_url': None,
                        'topic': topic
                    }
            else:
                return {
                    'answer': "I'm sorry I cannot answer this question of yours. Kindly visit the official website https://v.hdfcbank.com/htdocs/common/focus-funds/LP.html",
                    'source_url': None,
                    'topic': topic
                }
        
        # Generate answer
        answer = self.generate_answer_with_llm(query, info, source_url)
        
        # Ensure source link is included in answer (only if not already present)
        if source_url:
            # Check if source URL is already in the answer
            if source_url not in answer:
                answer += f"\n\nSource: {source_url}"
            else:
                # Remove duplicate if present
                answer = answer.replace(f"Source: {source_url}\n\nSource: {source_url}", f"Source: {source_url}")
                answer = answer.replace(f"Source: {source_url}\nSource: {source_url}", f"Source: {source_url}")
        
        return {
            'answer': answer,
            'source_url': source_url,
            'topic': topic
        }
    
    def _answer_fund_list_query(self, query: str, topic: str) -> Dict[str, str]:
        """Answer queries about listing funds and their ranks."""
        # Get fund information from repository
        funds_info = self.data_manager.get_funds_info_with_ranks()
        
        if topic == 'fund_list_with_ranks':
            # Detailed answer with ranks
            answer_parts = []
            answer_parts.append(f"We have information about {funds_info['summary']['total_funds']} mutual fund(s):\n")
            
            for fund in funds_info['summary']['funds']:
                answer_parts.append(f"• {fund['scheme_name']} ({fund['amc_name']})")
                if fund.get('category'):
                    answer_parts.append(f"  Category: {fund['category']}")
                answer_parts.append(f"  Rank: {fund['rank']}")
                answer_parts.append("")
            
            answer = "\n".join(answer_parts)
        else:
            # Simple listing
            answer_parts = []
            answer_parts.append(f"We have information about {funds_info['summary']['total_funds']} mutual fund(s):\n")
            
            for fund in funds_info['summary']['funds']:
                answer_parts.append(f"• {fund['scheme_name']} ({fund['amc_name']})")
            
            answer = "\n".join(answer_parts)
        
        answer += "\n\nNote: This information is based on data from official sources. Please verify details from scheme documents."
        
        # Get source URL (use first fund's source or AMFI)
        source_url = None
        if funds_info['detailed'] and funds_info['detailed'][0].get('source_url'):
            source_url = funds_info['detailed'][0]['source_url']
        
        if not source_url or source_url not in self.allowed_sources:
            source_url = self.knowledge_base.get_official_source_url('general')
        
        return {
            'answer': answer,
            'source_url': source_url,
            'topic': topic
        }
    
    def is_valid_question(self, query: str) -> bool:
        """Check if query is about supported topics."""
        query_lower = query.lower()
        
        # Check for fund listing queries
        if any(keyword in query_lower for keyword in ['what fund', 'list fund', 'fund information', 'which fund', 'funds do you have', 'tell me about fund', 'fund']):
            return True
        
        supported_topics = [
            'expense ratio', 'exit load', 'minimum sip', 'sip',
            'lock-in', 'lock in', 'elss', 'riskometer', 'risk',
            'benchmark', 'statement', 'download'
        ]
        
        return any(topic in query_lower for topic in supported_topics)
    
    def has_data_for_query(self, query: str) -> bool:
        """Check if we have data to answer this query."""
        topic = self.identify_topic(query)
        
        # Fund list queries are always answerable if we have any funds
        if topic in ['fund_list', 'fund_list_with_ranks']:
            return len(self.repository.get_all_funds()) > 0
        
        fund_name = self.extract_fund_name(query)
        info = self.knowledge_base.get_info_by_topic(topic, fund_name)
        
        # Check if we have a value or if it's a general question we can answer
        if info.get('value'):
            source_url = info.get('source_url')
            if source_url and source_url in self.allowed_sources:
                return True
        
        # If fund name provided, check if we have that fund
        if fund_name:
            funds = self.knowledge_base.search_fund(fund_name)
            if funds:
                return True
        
        return False

