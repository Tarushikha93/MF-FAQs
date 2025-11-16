"""
Data Manager - Script to store and manage fund data.
Handles data ingestion, updates, and validation.
"""

import json
import os
from typing import Dict, List, Optional
from fund_repository import FundRepository, Fund, PerformanceData, FundRank
from datetime import datetime


class FundDataManager:
    """Manages fund data storage and operations."""
    
    def __init__(self, data_file: str = "fund_data.json"):
        """Initialize the data manager."""
        self.repository = FundRepository(data_file)
    
    def store_fund_data(self, fund_data: Dict) -> bool:
        """Store fund data from scraped or manual entry."""
        try:
            # Convert dict to Fund object
            performance_dict = fund_data.pop('performance_data', {})
            performance = PerformanceData(**performance_dict) if performance_dict else None
            
            # Handle ranks
            ranks_dict = {}
            category_rank = fund_data.pop('category_rank', None)
            if category_rank:
                if isinstance(category_rank, dict):
                    ranks_dict = category_rank
                elif isinstance(category_rank, str):
                    # Try to determine which period this rank belongs to
                    # For now, assign to overall
                    ranks_dict['overall_category_rank'] = category_rank
            
            # Extract rank-specific data if present in performance_data
            if performance_dict:
                if 'category_rank_1m' in performance_dict:
                    ranks_dict['rank_1m'] = performance_dict.pop('category_rank_1m')
                if 'category_rank_5y' in performance_dict:
                    ranks_dict['rank_5y'] = performance_dict.pop('category_rank_5y')
            
            ranks = FundRank(**ranks_dict) if ranks_dict else None
            
            # Determine category if not provided
            if 'category' not in fund_data and 'scheme_name' in fund_data:
                fund_data['category'] = self._infer_category(fund_data['scheme_name'])
            
            fund = Fund(
                performance=performance,
                ranks=ranks,
                **fund_data
            )
            
            return self.repository.add_fund(fund)
        except Exception as e:
            print(f"Error storing fund data: {e}")
            return False
    
    def _infer_category(self, scheme_name: str) -> Optional[str]:
        """Infer fund category from scheme name."""
        name_lower = scheme_name.lower()
        
        if 'large' in name_lower and 'mid' in name_lower:
            return "Large & Mid Cap"
        elif 'flexi' in name_lower:
            return "Flexi Cap"
        elif 'elss' in name_lower or 'taxsaver' in name_lower:
            return "ELSS (Tax Savings)"
        elif 'large' in name_lower:
            return "Large Cap"
        elif 'mid' in name_lower:
            return "Mid Cap"
        elif 'small' in name_lower:
            return "Small Cap"
        
        return None
    
    def update_fund_rank(self, scheme_name: str, amc_name: str, 
                        period: str, rank: str) -> bool:
        """Update rank for a specific fund and period."""
        fund = self.repository.get_fund(amc_name, scheme_name)
        if not fund:
            print(f"Fund not found: {amc_name} - {scheme_name}")
            return False
        
        if not fund.ranks:
            fund.ranks = FundRank()
        
        period_lower = period.lower()
        if '1m' in period_lower or '1 month' in period_lower:
            fund.ranks.rank_1m = rank
        elif '3m' in period_lower:
            fund.ranks.rank_3m = rank
        elif '6m' in period_lower:
            fund.ranks.rank_6m = rank
        elif '1y' in period_lower or '1 year' in period_lower:
            fund.ranks.rank_1y = rank
        elif '3y' in period_lower:
            fund.ranks.rank_3y = rank
        elif '5y' in period_lower or '5 year' in period_lower:
            fund.ranks.rank_5y = rank
        else:
            fund.ranks.overall_category_rank = rank
        
        return self.repository.add_fund(fund)
    
    def get_funds_info_with_ranks(self) -> Dict:
        """Get information about all funds and their ranks."""
        return {
            'summary': self.repository.get_funds_summary(),
            'detailed': self.repository.get_funds_with_ranks()
        }
    
    def load_from_json(self, json_file: str) -> bool:
        """Load fund data from a JSON file."""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            success_count = 0
            for fund_data in data.get('funds', []):
                if self.store_fund_data(fund_data):
                    success_count += 1
            
            print(f"Successfully loaded {success_count} funds from {json_file}")
            return success_count > 0
        except Exception as e:
            print(f"Error loading from JSON: {e}")
            return False


def main():
    """Main function for data management operations."""
    import sys
    
    manager = FundDataManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "load":
            # Load data from existing JSON
            json_file = sys.argv[2] if len(sys.argv) > 2 else "fund_data.json"
            manager.load_from_json(json_file)
        
        elif command == "list":
            # List all funds with their information
            info = manager.get_funds_info_with_ranks()
            print("\n" + "="*60)
            print("Fund Information Summary")
            print("="*60)
            print(f"\nTotal Funds: {info['summary']['total_funds']}\n")
            
            for fund in info['summary']['funds']:
                print(f"Fund: {fund['scheme_name']}")
                print(f"  AMC: {fund['amc_name']}")
                print(f"  Category: {fund.get('category', 'N/A')}")
                print(f"  Rank: {fund['rank']}")
                print()
        
        elif command == "ranks":
            # Show detailed rank information
            info = manager.get_funds_info_with_ranks()
            print("\n" + "="*60)
            print("Detailed Fund Information with Ranks")
            print("="*60)
            
            for fund in info['detailed']:
                print(f"\n{fund['scheme_name']} ({fund['amc_name']})")
                print(f"  Category: {fund.get('category', 'N/A')}")
                print(f"  Expense Ratio: {fund.get('expense_ratio', 'N/A')}")
                print(f"  Exit Load: {fund.get('exit_load', 'N/A')}")
                print(f"  Riskometer: {fund.get('riskometer', 'N/A')}")
                
                if fund.get('ranks'):
                    print("  Ranks:")
                    for period, rank in fund['ranks'].items():
                        if rank:
                            print(f"    {period}: {rank}")
                else:
                    print("  Ranks: Not available")
                print()
    else:
        # Default: show summary
        info = manager.get_funds_info_with_ranks()
        summary = info['summary']
        
        print("\n" + "="*60)
        print("Mutual Fund Information and Rankings")
        print("="*60)
        print(f"\nTotal Funds Available: {summary['total_funds']}\n")
        
        for i, fund in enumerate(summary['funds'], 1):
            print(f"{i}. {fund['scheme_name']}")
            print(f"   AMC: {fund['amc_name']}")
            if fund.get('category'):
                print(f"   Category: {fund['category']}")
            print(f"   Rank: {fund['rank']}")
            print()


if __name__ == "__main__":
    main()

