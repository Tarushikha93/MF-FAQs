#!/usr/bin/env python3
"""
Test script to validate expense ratio query response
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot import MutualFundChatbot

def test_expense_ratio_query():
    """Test the chatbot's response to 'what is expense ratio' query"""
    
    print("🔍 Testing Expense Ratio Query")
    print("=" * 50)
    
    # Initialize chatbot
    chatbot = MutualFundChatbot()
    
    # Test query
    query = "what is expense ratio"
    print(f"Query: {query}")
    print("-" * 50)
    
    # Get response
    response_data = chatbot.answer_question(query)
    response = response_data.get('answer', '')
    
    print(f"Response:\n{response}")
    print("=" * 50)
    
    # Expected answer (from INDmoney FAQ)
    expected = """The Expense Ratio is the annual fee a mutual fund charges its investors to cover its expenses. It compensates for costs such as management fees, administrative fees, and any other operational expenses the AMC incurs to run the fund.
Expense Ratio is calculated as a percentage of total annual expenses divided by the average AUM (Assets under Management) of the mutual fund. For example, an expense ratio of 1.5% represents that ₹1.5 will be charged for every ₹100 invested in the fund annually.
A higher expense ratio indicates that more investors' money is being used to cover operational expenses rather than directed toward the fund's investment pool, which can lead to lower returns over time. It is also used by investors as a comparison tool when choosing between similar funds within a category.
SEBI has set limits on the maximum and minimum expense ratio that an AMC can charge for a specific mutual fund. The limits are set based on the funds' AUMs and have a tiered structure. For Equity funds, the maximum expense ratio that can be charged is 2.25% vs. 2.0% for Debt funds."""
    
    # Check if key terms are present
    key_terms = [
        "annual fee",
        "management fees",
        "administrative fees",
        "AUM",
        "Assets under Management",
        "SEBI",
        "2.25%",
        "2.0%"
    ]
    
    print("\n📊 Validation Results:")
    print("-" * 50)
    
    found_terms = []
    missing_terms = []
    
    for term in key_terms:
        if term.lower() in response.lower():
            found_terms.append(term)
        else:
            missing_terms.append(term)
    
    print(f"✅ Found key terms ({len(found_terms)}/{len(key_terms)}):")
    for term in found_terms:
        print(f"   - {term}")
    
    if missing_terms:
        print(f"\n❌ Missing key terms ({len(missing_terms)}/{len(key_terms)}):")
        for term in missing_terms:
            print(f"   - {term}")
    
    # Overall assessment
    if len(found_terms) >= len(key_terms) * 0.7:  # 70% match
        print("\n✅ PASS: Response contains most key information about expense ratio")
        return True
    else:
        print("\n❌ FAIL: Response missing critical information about expense ratio")
        return False

if __name__ == "__main__":
    success = test_expense_ratio_query()
    sys.exit(0 if success else 1)
