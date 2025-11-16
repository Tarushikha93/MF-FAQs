"""
Script to store fund data following the repository architecture.
Use this script to add/update fund data in the repository.
"""

import sys
import json
from data_manager import FundDataManager
from fund_repository import Fund, PerformanceData, FundRank


def store_fund_from_dict(fund_data: dict):
    """Store a fund from a dictionary."""
    manager = FundDataManager()
    success = manager.store_fund_data(fund_data)
    
    if success:
        print(f"✅ Successfully stored: {fund_data.get('scheme_name', 'Unknown')}")
    else:
        print(f"❌ Failed to store: {fund_data.get('scheme_name', 'Unknown')}")
    
    return success


def store_fund_manually():
    """Manually enter and store a fund."""
    print("\n" + "="*60)
    print("Store Fund Data")
    print("="*60 + "\n")
    
    fund_data = {}
    
    # Required fields
    fund_data['scheme_name'] = input("Scheme Name: ").strip()
    fund_data['amc_name'] = input("AMC Name: ").strip()
    
    # Optional fields
    print("\nOptional fields (press Enter to skip):")
    fund_data['category'] = input("Category: ").strip() or None
    fund_data['expense_ratio'] = input("Expense Ratio (e.g., 0.85%): ").strip() or None
    fund_data['exit_load'] = input("Exit Load (e.g., 1%): ").strip() or None
    fund_data['minimum_sip'] = input("Minimum SIP (e.g., ₹100): ").strip() or None
    fund_data['lock_in'] = input("Lock-in Period: ").strip() or None
    fund_data['riskometer'] = input("Riskometer: ").strip() or None
    fund_data['benchmark'] = input("Benchmark: ").strip() or None
    fund_data['source_url'] = input("Source URL: ").strip() or None
    
    # Performance data
    print("\nPerformance Data (optional):")
    performance = {}
    performance['fund_1m'] = input("Fund 1M Return (%): ").strip() or None
    performance['benchmark_1m'] = input("Benchmark 1M Return (%): ").strip() or None
    performance['fund_5y'] = input("Fund 5Y Return (%): ").strip() or None
    performance['benchmark_5y'] = input("Benchmark 5Y Return (%): ").strip() or None
    performance['fund_6m'] = input("Fund 6M Return (%): ").strip() or None
    
    if any(performance.values()):
        fund_data['performance_data'] = {k: v for k, v in performance.items() if v}
    
    # Rank data
    print("\nRank Data (optional):")
    ranks = {}
    ranks['rank_1m'] = input("Category Rank 1M (e.g., 4/22): ").strip() or None
    ranks['rank_5y'] = input("Category Rank 5Y (e.g., null or Best in...): ").strip() or None
    ranks['overall_category_rank'] = input("Overall Category Rank: ").strip() or None
    
    if any(ranks.values()):
        fund_data['category_rank'] = {k: v for k, v in ranks.items() if v}
    
    # Remove None values
    fund_data = {k: v for k, v in fund_data.items() if v is not None}
    
    # Store
    manager = FundDataManager()
    return manager.store_fund_data(fund_data)


def store_from_json(json_file: str):
    """Store funds from a JSON file."""
    manager = FundDataManager()
    return manager.load_from_json(json_file)


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "from-json":
            json_file = sys.argv[2] if len(sys.argv) > 2 else "fund_data.json"
            store_from_json(json_file)
        
        elif command == "manual":
            store_fund_manually()
        
        elif command == "update-rank":
            if len(sys.argv) < 5:
                print("Usage: python store_fund_data.py update-rank <scheme_name> <amc_name> <period> <rank>")
                print("Example: python store_fund_data.py update-rank 'HDFC Flexi Cap Fund' HDFC 1M '4/22'")
                return
            
            scheme_name = sys.argv[2]
            amc_name = sys.argv[3]
            period = sys.argv[4]
            rank = sys.argv[5] if len(sys.argv) > 5 else None
            
            manager = FundDataManager()
            if rank:
                success = manager.update_fund_rank(scheme_name, amc_name, period, rank)
                if success:
                    print(f"✅ Updated rank for {scheme_name}")
                else:
                    print(f"❌ Failed to update rank")
            else:
                print("Error: Rank value required")
        
        else:
            print(f"Unknown command: {command}")
            print("\nAvailable commands:")
            print("  from-json [file]  - Load funds from JSON file")
            print("  manual            - Manually enter fund data")
            print("  update-rank       - Update rank for a fund")
    else:
        # Default: load from fund_data.json
        store_from_json("fund_data.json")


if __name__ == "__main__":
    main()

