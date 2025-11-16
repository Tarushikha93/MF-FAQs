"""
Script to scrape data from specific indmoney.com links.
"""

from mutual_fund_scraper import MutualFundScraper
import json
import os

# URLs to scrape
URLS_TO_SCRAPE = [
    'https://www.indmoney.com/mutual-funds/hdfc-flexi-cap-fund-direct-plan-growth-option-3184',
    'https://www.indmoney.com/mutual-funds/hdfc-elss-taxsaver-direct-plan-growth-option-2685'
]

def scrape_funds():
    """Scrape data from the specified URLs."""
    scraper = MutualFundScraper()
    scraped_data = []
    
    for url in URLS_TO_SCRAPE:
        print(f"\n{'='*60}")
        print(f"Scraping: {url}")
        print('='*60)
        
        details = scraper.extract_fund_details_from_indmoney(url)
        
        if details:
            print(f"Scheme Name: {details.get('scheme_name', 'N/A')}")
            print(f"Expense Ratio: {details.get('expense_ratio', 'N/A')}")
            print(f"Exit Load: {details.get('exit_load', 'N/A')}")
            print(f"Minimum SIP: {details.get('minimum_sip', 'N/A')}")
            print(f"Lock-in: {details.get('lock_in', 'N/A')}")
            print(f"Riskometer: {details.get('riskometer', 'N/A')}")
            print(f"Benchmark: {details.get('benchmark', 'N/A')}")
            
            scraped_data.append({
                'url': url,
                'data': details
            })
        else:
            print("❌ Failed to scrape data")
            scraped_data.append({
                'url': url,
                'data': None,
                'error': 'Failed to fetch or parse page'
            })
    
    return scraped_data

def update_fund_data_json(scraped_data):
    """Update fund_data.json with scraped data."""
    json_path = os.path.join(os.path.dirname(__file__), 'fund_data.json')
    
    # Read existing data
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except:
        data = {'funds': []}
    
    # Update or add funds
    for item in scraped_data:
        if not item['data']:
            print(f"\n⚠️  Skipping {item['url']} - no data scraped")
            continue
        
        details = item['data']
        url = item['url']
        
        # Determine fund name from URL or scraped data
        scheme_name = details.get('scheme_name')
        if not scheme_name:
            if 'flexi-cap' in url.lower():
                scheme_name = 'HDFC Flexi Cap Fund'
            elif 'elss' in url.lower() or 'taxsaver' in url.lower():
                scheme_name = 'HDFC ELSS TaxSaver'
            else:
                scheme_name = 'Unknown Fund'
        
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
                fund_found = True
                print(f"\n✅ Updated: {scheme_name}")
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
                'source_url': url
            }
            data['funds'].append(new_fund)
            print(f"\n✅ Added: {scheme_name}")
    
    # Write updated data
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Updated fund_data.json with {len(data['funds'])} funds")
    return data

if __name__ == "__main__":
    print("Starting data scraping...")
    scraped = scrape_funds()
    
    print("\n" + "="*60)
    print("Updating fund_data.json...")
    print("="*60)
    
    updated_data = update_fund_data_json(scraped)
    
    print("\n" + "="*60)
    print("Summary:")
    print("="*60)
    for fund in updated_data['funds']:
        print(f"\n{fund['scheme_name']}:")
        print(f"  Expense Ratio: {fund.get('expense_ratio', 'N/A')}")
        print(f"  Exit Load: {fund.get('exit_load', 'N/A')}")
        print(f"  Riskometer: {fund.get('riskometer', 'N/A')}")
        print(f"  Lock-in: {fund.get('lock_in', 'N/A')}")

