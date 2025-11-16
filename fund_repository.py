"""
Fund Repository - Backend data storage and retrieval layer.
Follows repository pattern for data management.
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum


class FundCategory(Enum):
    """Mutual fund categories."""
    LARGE_MID_CAP = "Large & Mid Cap"
    FLEXI_CAP = "Flexi Cap"
    ELSS = "ELSS (Tax Savings)"
    LARGE_CAP = "Large Cap"
    MID_CAP = "Mid Cap"
    SMALL_CAP = "Small Cap"


@dataclass
class FundRank:
    """Category rank information for a fund."""
    rank_1m: Optional[str] = None  # e.g., "4/22" or "1/22"
    rank_3m: Optional[str] = None
    rank_6m: Optional[str] = None
    rank_1y: Optional[str] = None
    rank_3y: Optional[str] = None
    rank_5y: Optional[str] = None  # e.g., "null" or "Best in Large & Mid-cap"
    overall_category_rank: Optional[str] = None


@dataclass
class PerformanceData:
    """Performance data for a fund."""
    fund_1m: Optional[str] = None  # Percentage as string, e.g., "2.45%"
    fund_3m: Optional[str] = None
    fund_6m: Optional[str] = None
    fund_1y: Optional[str] = None
    fund_3y: Optional[str] = None
    fund_5y: Optional[str] = None
    benchmark_1m: Optional[str] = None  # e.g., "2.81%"
    benchmark_3m: Optional[str] = None
    benchmark_6m: Optional[str] = None
    benchmark_1y: Optional[str] = None
    benchmark_3y: Optional[str] = None
    benchmark_5y: Optional[str] = None


@dataclass
class Fund:
    """Complete fund information structure."""
    scheme_name: str
    amc_name: str
    category: Optional[str] = None
    expense_ratio: Optional[str] = None
    exit_load: Optional[str] = None
    minimum_sip: Optional[str] = None
    lock_in: Optional[str] = None
    riskometer: Optional[str] = None
    benchmark: Optional[str] = None
    source_url: Optional[str] = None
    performance: Optional[PerformanceData] = None
    ranks: Optional[FundRank] = None
    last_updated: Optional[str] = None
    
    def __post_init__(self):
        """Convert nested dataclasses from dict if needed."""
        if isinstance(self.performance, dict):
            self.performance = PerformanceData(**self.performance)
        if isinstance(self.ranks, dict):
            self.ranks = FundRank(**self.ranks)
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()


class FundRepository:
    """Repository for managing fund data storage and retrieval."""
    
    def __init__(self, data_file: str = "fund_data.json"):
        """Initialize repository with data file path."""
        self.data_file = os.path.join(os.path.dirname(__file__), data_file)
        self.funds: Dict[str, Fund] = {}
        self._load_data()
    
    def _load_data(self):
        """Load fund data from JSON file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    for fund_data in data.get('funds', []):
                        # Make a copy to avoid modifying original
                        fund_dict = fund_data.copy()
                        
                        # Handle performance_data if present
                        performance_dict = fund_dict.pop('performance_data', {})
                        if performance_dict:
                            fund_dict['performance'] = PerformanceData(**performance_dict)
                        
                        # Handle category_rank if present (convert to FundRank)
                        category_rank = fund_dict.pop('category_rank', None)
                        rank_dict = {}
                        if category_rank:
                            # If it's a single string, try to assign to appropriate period
                            if isinstance(category_rank, str):
                                # Check if it looks like a rank (contains /)
                                if '/' in category_rank:
                                    rank_dict['overall_category_rank'] = category_rank
                                elif category_rank.lower() in ['null', 'none', '--', '-']:
                                    rank_dict['overall_category_rank'] = None
                                else:
                                    rank_dict['overall_category_rank'] = category_rank
                            elif isinstance(category_rank, dict):
                                rank_dict = category_rank
                        
                        # Also check for rank fields in performance_data
                        if performance_dict:
                            if 'category_rank_1m' in performance_dict:
                                rank_dict['rank_1m'] = performance_dict['category_rank_1m']
                            if 'category_rank_5y' in performance_dict:
                                rank_dict['rank_5y'] = performance_dict['category_rank_5y']
                        
                        if rank_dict:
                            fund_dict['ranks'] = FundRank(**rank_dict)
                        
                        # Create Fund object
                        fund = Fund(**fund_dict)
                        key = self._get_fund_key(fund.amc_name, fund.scheme_name)
                        self.funds[key] = fund
                        
        except Exception as e:
            print(f"Error loading fund data: {e}")
            self.funds = {}
    
    def _get_fund_key(self, amc_name: str, scheme_name: str) -> str:
        """Generate a unique key for a fund."""
        return f"{amc_name}_{scheme_name}".lower().replace(" ", "_")
    
    def save_data(self):
        """Save fund data to JSON file."""
        try:
            # Convert Fund objects to dictionaries
            funds_data = []
            for fund in self.funds.values():
                fund_dict = asdict(fund)
                
                # Convert PerformanceData and FundRank to dicts
                if fund_dict.get('performance'):
                    fund_dict['performance_data'] = fund_dict.pop('performance')
                if fund_dict.get('ranks'):
                    fund_dict['category_rank'] = fund_dict.pop('ranks')
                
                # Remove None values for cleaner JSON
                fund_dict = {k: v for k, v in fund_dict.items() if v is not None}
                funds_data.append(fund_dict)
            
            data = {'funds': funds_data}
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            return True
        except Exception as e:
            print(f"Error saving fund data: {e}")
            return False
    
    def add_fund(self, fund: Fund) -> bool:
        """Add or update a fund in the repository."""
        try:
            key = self._get_fund_key(fund.amc_name, fund.scheme_name)
            fund.last_updated = datetime.now().isoformat()
            self.funds[key] = fund
            return self.save_data()
        except Exception as e:
            print(f"Error adding fund: {e}")
            return False
    
    def get_fund(self, amc_name: str, scheme_name: str) -> Optional[Fund]:
        """Retrieve a specific fund by AMC and scheme name."""
        key = self._get_fund_key(amc_name, scheme_name)
        return self.funds.get(key)
    
    def get_all_funds(self) -> List[Fund]:
        """Get all funds in the repository."""
        return list(self.funds.values())
    
    def search_funds(self, query: str) -> List[Fund]:
        """Search for funds matching the query."""
        query_lower = query.lower()
        results = []
        
        for fund in self.funds.values():
            if (query_lower in fund.scheme_name.lower() or 
                query_lower in fund.amc_name.lower() or
                (fund.category and query_lower in fund.category.lower())):
                results.append(fund)
        
        return results
    
    def get_funds_with_ranks(self) -> List[Dict]:
        """Get all funds with their rank information formatted for display."""
        funds_list = []
        
        for fund in self.get_all_funds():
            fund_info = {
                'scheme_name': fund.scheme_name,
                'amc_name': fund.amc_name,
                'category': fund.category,
                'expense_ratio': fund.expense_ratio,
                'exit_load': fund.exit_load,
                'minimum_sip': fund.minimum_sip,
                'riskometer': fund.riskometer,
                'source_url': fund.source_url,
            }
            
            # Add rank information
            if fund.ranks:
                fund_info['ranks'] = {
                    '1M': fund.ranks.rank_1m,
                    '3M': fund.ranks.rank_3m,
                    '6M': fund.ranks.rank_6m,
                    '1Y': fund.ranks.rank_1y,
                    '3Y': fund.ranks.rank_3y,
                    '5Y': fund.ranks.rank_5y,
                    'Overall': fund.ranks.overall_category_rank,
                }
            else:
                fund_info['ranks'] = None
            
            funds_list.append(fund_info)
        
        return funds_list
    
    def get_funds_summary(self) -> Dict:
        """Get a summary of all funds and their rankings."""
        funds = self.get_all_funds()
        
        summary = {
            'total_funds': len(funds),
            'funds': []
        }
        
        for fund in funds:
            fund_summary = {
                'scheme_name': fund.scheme_name,
                'amc_name': fund.amc_name,
                'category': fund.category,
            }
            
            # Get the best available rank (prioritize overall, then 1Y, then 1M)
            if fund.ranks:
                rank = None
                if fund.ranks.overall_category_rank:
                    rank = fund.ranks.overall_category_rank
                elif fund.ranks.rank_1y:
                    rank = f"1Y: {fund.ranks.rank_1y}"
                elif fund.ranks.rank_1m:
                    rank = f"1M: {fund.ranks.rank_1m}"
                elif fund.ranks.rank_5y:
                    rank = f"5Y: {fund.ranks.rank_5y}"
                
                fund_summary['rank'] = rank
            else:
                fund_summary['rank'] = "Not available"
            
            summary['funds'].append(fund_summary)
        
        return summary

