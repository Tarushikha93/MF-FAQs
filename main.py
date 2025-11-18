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
    print("\nAsk questions about expense ratio, exit load, SIP, lock-in, riskometer, benchmark, and statements about the funds in HDFC : Large & Mid Cap, Flexi and ELSS tax saver.")
    print("I can also answer FAQs related to Mutual Funds.")
    print("\nNote: I provide factual information only, not investment advice.")
    print("Every answer includes a source link to official pages.")
    print("\nType 'quit' or 'exit' to end the conversation.")
    print("=" * 60)
    print()


def main():
    """Main CLI loop."""
    chatbot = MutualFundChatbot()
    print_welcome()
    
    while True:
        try:
            query = input("\nYou: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nThank you for using the Mutual Fund Chatbot. Goodbye!")
                break
            
            # Check if question is valid
            if not chatbot.is_valid_question(query):
                print("\nBot: I can only answer questions about expense ratio, exit load, minimum SIP, "
                      "lock-in period (ELSS), riskometer, benchmark, and statement downloads. "
                      "Please ask about one of these topics.")
                continue
            
            # Get answer
            response = chatbot.answer_question(query)
            
            # Display answer
            print(f"\nBot: {response['answer']}")
            if response['source_url']:
                print(f"\nSource: {response['source_url']}")
            
        except KeyboardInterrupt:
            print("\n\nThank you for using the Mutual Fund Chatbot. Goodbye!")
            break
        except Exception as e:
            print(f"\nBot: I encountered an error: {e}")
            print("Please try rephrasing your question or try again later.")


if __name__ == "__main__":
    main()

