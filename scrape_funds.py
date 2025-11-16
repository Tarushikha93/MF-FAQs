"""
Script to scrape data from indmoney.com for specific funds.
"""

from mutual_fund_scraper import MutualFundScraper
import json

# URLs to scrape
FUND_URLS = [
    'https://www.indmoney.com/mutual-funds/hdfc-flexi-cap-fund-direct-plan-growth-option-3184',
    'https://www.indmoney.com/mutual-funds/hdfc-elss-taxsaver-direct-plan-growth-option-2685',
    'https://www.indmoney.com/mutual-funds/hdfc-large-and-mid-cap-fund-direct-growth-2874'
]

def scrape_fund_data():
    """Scrape data from the specified URLs."""
    scraper = MutualFundScraper()
    
    results = []
    
    for url in FUND_URLS:
        print(f"\n{'='*60}")
        print(f"Scraping: {url}")
        print('='*60)
        
        details = scraper.extract_fund_details_from_indmoney(url)
        
        if details:
            print(f"Scheme Name: {details.get('scheme_name', 'N/A')}")
            print(f"AMC Name: {details.get('amc_name', 'N/A')}")
            print(f"Expense Ratio: {details.get('expense_ratio', 'N/A')}")
            print(f"Exit Load: {details.get('exit_load', 'N/A')}")
            print(f"Minimum SIP: {details.get('minimum_sip', 'N/A')}")
            print(f"Lock-in: {details.get('lock_in', 'N/A')}")
            print(f"Riskometer: {details.get('riskometer', 'N/A')}")
            print(f"Benchmark: {details.get('benchmark', 'N/A')}")
            
            results.append({
                'url': url,
                'data': details
            })
        else:
            print("❌ Failed to scrape data")
            results.append({
                'url': url,
                'data': None
            })
    
    return results

if __name__ == "__main__":
    results = scrape_fund_data()
    
    print("\n" + "="*60)
    print("Scraping Summary")
    print("="*60)
    for result in results:
        if result['data']:
            print(f"\n✅ {result['url']}")
            print(f"   Scheme: {result['data'].get('scheme_name', 'N/A')}")
        else:
            print(f"\n❌ {result['url']} - Failed")

