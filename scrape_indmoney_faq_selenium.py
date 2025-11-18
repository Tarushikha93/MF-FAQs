#!/usr/bin/env python3
"""
Improved FAQ scraper for INDmoney mutual funds page
"""

import json
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def scrape_indmoney_faq_improved():
    """Scrape FAQ data from INDmoney mutual funds page"""
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    url = "https://www.indmoney.com/mutual-funds"
    
    faq_data = {
        "source": "INDmoney Mutual Funds",
        "section": "Important Questions About Investing in Mutual Funds",
        "scraped_at": datetime.now().isoformat(),
        "faqs": []
    }
    
    try:
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("🔍 Loading INDmoney mutual funds page...")
        driver.get(url)
        
        wait = WebDriverWait(driver, 20)
        
        # Wait for page to load completely
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(8)  # Wait longer for dynamic content
        
        # Scroll down to load FAQ section
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        
        # Scroll back up a bit
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
        time.sleep(3)
        
        # Get page source
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        print("📋 Extracting FAQ content...")
        
        # Method 1: Look for FAQ section specifically
        faq_section = None
        
        # Try to find section with FAQ-related text
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = element.get_text(strip=True).lower()
            if 'important questions' in text and 'mutual funds' in text:
                faq_section = element.parent
                print(f"✅ Found FAQ section: {element.get_text(strip=True)}")
                break
        
        # Method 2: If specific section not found, look for Q&A patterns throughout the page
        if not faq_section:
            print("⚠️ FAQ section not found, searching for Q&A patterns...")
            # Use entire page
            faq_section = soup
        
        # Extract Q&A pairs
        faqs = []
        
        # Look for common question patterns
        question_patterns = [
            r'^\s*(What|How|Why|When|Where|Which|Who|Can|Should|Is|Are|Do|Does)\s.+',
            r'^\s*\d+\.\s*.+\?',  # Numbered questions
            r'.+\?$',  # Any text ending with ?
        ]
        
        # Find all text elements that might be questions
        all_text_elements = faq_section.find_all(text=True)
        
        for text_element in all_text_elements:
            text = text_element.strip()
            
            # Check if it matches question patterns
            is_question = False
            for pattern in question_patterns:
                if re.match(pattern, text, re.IGNORECASE):
                    is_question = True
                    break
            
            if is_question and 10 < len(text) < 200:  # Reasonable question length
                # Look for answer nearby
                answer = ""
                
                # Get parent element
                parent = text_element.parent
                
                # Method A: Look in next siblings
                next_sibling = parent.next_sibling
                attempts = 0
                while next_sibling and attempts < 5:
                    if hasattr(next_sibling, 'get_text'):
                        sibling_text = next_sibling.get_text(strip=True)
                        if len(sibling_text) > 30 and not sibling_text.endswith('?'):
                            answer = sibling_text
                            break
                    next_sibling = next_sibling.next_sibling
                    attempts += 1
                
                # Method B: Look in parent's siblings
                if not answer:
                    parent_sibling = parent.parent.next_sibling
                    attempts = 0
                    while parent_sibling and attempts < 3:
                        if hasattr(parent_sibling, 'get_text'):
                            sibling_text = parent_sibling.get_text(strip=True)
                            if len(sibling_text) > 30 and not sibling_text.endswith('?'):
                                answer = sibling_text
                                break
                        parent_sibling = parent_sibling.next_sibling
                        attempts += 1
                
                # Method C: Look in child elements of parent
                if not answer and parent.children:
                    for child in parent.children:
                        if hasattr(child, 'get_text'):
                            child_text = child.get_text(strip=True)
                            if len(child_text) > 30 and not child_text.endswith('?') and child_text != text:
                                answer = child_text
                                break
                
                if answer:
                    # Clean up the answer
                    answer = re.sub(r'\s+', ' ', answer)  # Remove extra whitespace
                    answer = answer[:2000]  # Limit length
                    
                    faqs.append({
                        "question": text,
                        "answer": answer,
                        "source_url": url
                    })
        
        # Remove duplicates
        seen_questions = set()
        unique_faqs = []
        for faq in faqs:
            if faq["question"] not in seen_questions:
                unique_faqs.append(faq)
                seen_questions.add(faq["question"])
        
        faq_data["faqs"] = unique_faqs
        
        driver.quit()
        
        # Remove duplicates
        seen_questions = set()
        unique_faqs = []
        for faq in faq_data["faqs"]:
            if faq["question"] not in seen_questions:
                unique_faqs.append(faq)
                seen_questions.add(faq["question"])
        
        faq_data["faqs"] = unique_faqs
        
        return faq_data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'driver' in locals():
            driver.quit()
        return faq_data

if __name__ == "__main__":
    import re
    
    print("🚀 Improved INDmoney FAQ Scraper")
    print("=" * 50)
    
    # Scrape FAQ data
    data = scrape_indmoney_faq_improved()
    
    print(f"\n📊 Results:")
    print(f"Total FAQs scraped: {len(data['faqs'])}")
    
    if data['faqs']:
        print("\n📋 Sample FAQs:")
        for i, faq in enumerate(data['faqs'][:3], 1):
            print(f"\n{i}. Q: {faq['question']}")
            print(f"   A: {faq['answer'][:100]}...")
    
    # Save to JSON file
    with open('indmoney_faq_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Data saved to: indmoney_faq_data.json")
    print(f"🕒 Scraped at: {data['scraped_at']}")
