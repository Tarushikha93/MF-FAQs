#!/usr/bin/env python3
"""
Test script to verify Gemini integration works correctly.
"""

import os
import sys
from chatbot import MutualFundChatbot

def test_llm_availability():
    """Test which LLM services are available."""
    print("="*60)
    print("LLM Availability Test")
    print("="*60)
    
    chatbot = MutualFundChatbot()
    
    print(f"OpenAI Available: {chatbot.openai_client is not None}")
    print(f"Gemini Available: {chatbot.gemini_model is not None}")
    print()
    
    # Check environment variables
    openai_key = os.getenv('OPENAI_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    print(f"OPENAI_API_KEY set: {'Yes' if openai_key else 'No'}")
    print(f"GEMINI_API_KEY set: {'Yes' if gemini_key else 'No'}")
    print()

def test_gemini_integration():
    """Test Gemini integration with a simple query."""
    print("="*60)
    print("Gemini Integration Test")
    print("="*60)
    
    chatbot = MutualFundChatbot()
    
    if not chatbot.gemini_model:
        print("❌ Gemini not available. Set GEMINI_API_KEY environment variable.")
        return False
    
    # Test with a simple query
    test_query = "What is the expense ratio of HDFC Flexi Cap Fund?"
    
    print(f"Testing query: {test_query}")
    print()
    
    try:
        response = chatbot.answer_question(test_query)
        print("✅ Gemini integration successful!")
        print(f"Answer: {response['answer'][:200]}...")
        print(f"Source: {response['source_url']}")
        return True
    except Exception as e:
        print(f"❌ Gemini integration failed: {e}")
        return False

def test_fallback_behavior():
    """Test fallback behavior when no LLM is available."""
    print("="*60)
    print("Fallback Behavior Test")
    print("="*60)
    
    # Temporarily disable LLMs
    chatbot = MutualFundChatbot()
    original_gemini = chatbot.gemini_model
    original_openai = chatbot.openai_client
    
    chatbot.gemini_model = None
    chatbot.openai_client = None
    
    test_query = "What funds do you have?"
    
    print(f"Testing query without LLM: {test_query}")
    print()
    
    try:
        response = chatbot.answer_question(test_query)
        print("✅ Fallback to template works!")
        print(f"Answer: {response['answer'][:200]}...")
        return True
    except Exception as e:
        print(f"❌ Fallback failed: {e}")
        return False
    finally:
        # Restore original clients
        chatbot.gemini_model = original_gemini
        chatbot.openai_client = original_openai

if __name__ == "__main__":
    print("Testing Gemini Integration for Mutual Fund Chatbot")
    print("="*60)
    
    # Run tests
    test_llm_availability()
    
    gemini_works = test_gemini_integration()
    print()
    
    fallback_works = test_fallback_behavior()
    print()
    
    # Summary
    print("="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Gemini Integration: {'✅ PASS' if gemini_works else '❌ FAIL'}")
    print(f"Fallback Behavior: {'✅ PASS' if fallback_works else '❌ FAIL'}")
    
    if not gemini_works:
        print("\nTo enable Gemini:")
        print("1. Get a Gemini API key from https://aistudio.google.com/")
        print("2. Set environment variable: export GEMINI_API_KEY='your-key'")
        print("3. Run this test again")
