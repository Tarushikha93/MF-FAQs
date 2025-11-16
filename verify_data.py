"""
Script to verify the scraped data matches expected values.
"""

import json
import os

# Expected values for first link
EXPECTED_DATA = {
    'url': 'https://www.indmoney.com/mutual-funds/hdfc-large-and-mid-cap-fund-direct-growth-2874',
    'expense_ratio': '0.85%',
    'exit_load': '1%',
    'riskometer': 'Very High Risk',
    'lock_in': 'No Lock-in'
}

def verify_data():
    """Verify the data in fund_data.json matches expected values."""
    json_path = os.path.join(os.path.dirname(__file__), 'fund_data.json')
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Find the first fund
        first_fund = None
        for fund in data.get('funds', []):
            if fund.get('source_url') == EXPECTED_DATA['url']:
                first_fund = fund
                break
        
        if not first_fund:
            print(f"❌ Fund with URL {EXPECTED_DATA['url']} not found in data")
            return False
        
        print("=" * 60)
        print("Verification for first link:")
        print("=" * 60)
        print(f"URL: {EXPECTED_DATA['url']}\n")
        
        all_match = True
        
        for key, expected_value in EXPECTED_DATA.items():
            if key == 'url':
                continue
            
            actual_value = first_fund.get(key)
            if actual_value == expected_value:
                print(f"✅ {key}: '{actual_value}' (matches expected)")
            else:
                print(f"❌ {key}: Got '{actual_value}', Expected '{expected_value}'")
                all_match = False
        
        print()
        if all_match:
            print("✅ All data matches expected values!")
            return True
        else:
            print("⚠️  Some data does not match expected values")
            return False
            
    except Exception as e:
        print(f"Error verifying data: {e}")
        return False

if __name__ == "__main__":
    verify_data()

