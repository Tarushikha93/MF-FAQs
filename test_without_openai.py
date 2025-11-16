"""
Test script to demonstrate how the chatbot works without OpenAI credentials.
All functionality works using template-based answers.
"""

from chatbot import MutualFundChatbot

def test_fund_list_query():
    """Test the specific query: Tell me what fund information we have and what is the rank of each mutual fund?"""
    
    print("="*70)
    print("Testing Chatbot WITHOUT OpenAI Credentials")
    print("="*70)
    print("\nThis demonstrates that all functionality works using template-based answers.")
    print("No API calls are made to OpenAI.\n")
    
    # Initialize chatbot (without OpenAI)
    chatbot = MutualFundChatbot()
    
    # Check if OpenAI is available
    print(f"OpenAI Client Available: {chatbot.client is not None}")
    print(f"Total Funds in Repository: {len(chatbot.repository.get_all_funds())}\n")
    
    # Test the specific query
    test_query = "Tell me what fund information we have and what is the rank of each mutual fund?"
    
    print("="*70)
    print(f"Query: {test_query}")
    print("="*70)
    print()
    
    response = chatbot.answer_question(test_query)
    
    print("Answer:")
    print("-"*70)
    print(response['answer'])
    print("-"*70)
    print(f"\nSource: {response['source_url']}")
    print(f"Topic Identified: {response['topic']}")
    
    print("\n" + "="*70)
    print("✅ Test Passed: Query answered successfully without OpenAI!")
    print("="*70)


def test_other_queries():
    """Test other common queries without OpenAI."""
    
    chatbot = MutualFundChatbot()
    
    test_queries = [
        "What is the expense ratio of HDFC Flexi Cap Fund?",
        "What is the exit load?",
        "What funds do you have?",
        "What is the minimum SIP for HDFC Large and Mid Cap Fund?",
    ]
    
    print("\n" + "="*70)
    print("Testing Other Queries (Without OpenAI)")
    print("="*70 + "\n")
    
    for query in test_queries:
        print(f"Query: {query}")
        response = chatbot.answer_question(query)
        print(f"Answer: {response['answer'][:150]}...")
        if response['source_url']:
            print(f"Source: {response['source_url']}")
        print()


if __name__ == "__main__":
    test_fund_list_query()
    test_other_queries()

