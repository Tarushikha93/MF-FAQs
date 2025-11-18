"""
Main entry point for the Mutual Fund Chatbot CLI.
"""

import sys
from chatbot import MutualFundChatbot


def print_welcome():
    """Print welcome message."""
    print("=" * 60)
    print("Mutual Fund Information Chatbot")
    print("=" * 60)
    print("\nAsk questions about mutual funds including:")
    print("• Expense ratio")
    print("• Exit load")
    print("• SIP (Systematic Investment Plan)")
    print("• Lock-in period")
    print("• Riskometer")
    print("• Benchmark")
    print("• How to download statements")
    print("\nI provide answers from INDmoney FAQs with:")
    print("• Compressed answers (3 sentences or less)")
    print("• Refresh timestamps")
    print("• Source links")
    print("\nNote: I provide factual information only, not investment advice.")
    print("\nType 'quit' or 'exit' to end the conversation.")
    print("=" * 60)
    print()


def main():
    """Main CLI loop."""
    chatbot = MutualFundChatbot()
    print_welcome()
    
    print(f"Loaded {len(chatbot.knowledge_base.faqs)} FAQs from knowledge base")
    if chatbot.knowledge_base.faq_refresh_info:
        print(f"FAQ data: {chatbot.knowledge_base.faq_refresh_info}")
    
    while True:
        try:
            query = input("\nYou: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nThank you for using the Mutual Fund Chatbot. Goodbye!")
                break
            
            # Get answer
            response = chatbot.answer_question(query)
            
            # Display answer
            print(f"\nBot: {response['answer']}")
            if response.get('source_url'):
                print(f"\nSource: {response['source_url']}")
            
        except KeyboardInterrupt:
            print("\n\nThank you for using the Mutual Fund Chatbot. Goodbye!")
            break
        except Exception as e:
            print(f"\nBot: I encountered an error: {e}")
            print("Please try rephrasing your question or try again later.")


if __name__ == "__main__":
    main()

