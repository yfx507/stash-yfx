#!/usr/bin/env python3
"""
Rule34Video scraper using undetected_chromedriver to bypass DDoS-Guard
This approach is designed to avoid detection by anti-bot systems
"""

import undetected_chromedriver as uc
import time
import sys
import json
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def create_undetected_driver():
    """Create an undetected Chrome driver instance"""
    options = uc.ChromeOptions()
    
    # Basic options for stealth
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    
    # Uncomment for headless mode (but may be detected more easily)
    # options.add_argument('--headless')
    
    try:
        # Create driver with undetected_chromedriver
        driver = uc.Chrome(options=options, version_main=None)
        
        # Additional stealth measures
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        print(f"Error creating driver: {e}")
        return None

def bypass_ddos_guard(driver, url="https://rule34video.com/", timeout=60):
    """
    Navigate to site and wait for DDoS-Guard challenge to complete
    """
    print(f"Loading {url}...")
    driver.get(url)
    
    wait = WebDriverWait(driver, timeout)
    start_time = time.time()
    
    # Wait for page to load
    try:
        # Check if we hit DDoS-Guard
        if "DDOS-GUARD" in driver.title or "ddos-guard" in driver.page_source.lower():
            print("DDoS-Guard challenge detected, waiting for completion...")
            
            # Wait for title to change from DDoS-Guard
            def title_changed(driver):
                current_title = driver.title.lower()
                return "ddos-guard" not in current_title and "checking" not in current_title
            
            wait.until(title_changed)
            print("✓ DDoS-Guard challenge completed!")
        else:
            print("✓ No DDoS-Guard challenge detected")
        
        # Additional wait for page to fully load
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        time.sleep(3)  # Extra safety margin
        
        elapsed = time.time() - start_time
        print(f"Page loaded successfully in {elapsed:.2f} seconds")
        return True
        
    except Exception as e:
        print(f"Error during DDoS-Guard bypass: {e}")
        return False

def extract_cookies(driver):
    """Extract cookies from the driver session"""
    cookies = driver.get_cookies()
    print(f"Extracted {len(cookies)} cookies:")
    
    for cookie in cookies:
        print(f"  - {cookie['name']}: {cookie['value'][:20]}...")
    
    return cookies

def create_requests_session(cookies):
    """Create a requests session with the extracted cookies"""
    session = requests.Session()
    
    # Add cookies to session
    for cookie in cookies:
        session.cookies.set(
            name=cookie['name'],
            value=cookie['value'],
            domain=cookie.get('domain', ''),
            path=cookie.get('path', '/')
        )
    
    # Set realistic headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    return session

def test_session(session, test_url="https://rule34video.com/"):
    """Test if the requests session works without DDoS-Guard"""
    try:
        response = session.get(test_url, timeout=30)
        print(f"\nTesting session with {test_url}")
        print(f"Status Code: {response.status_code}")
        
        if "DDOS-GUARD" in response.text:
            print("❌ Session still shows DDoS-Guard")
            return False
        elif response.status_code == 200:
            print("✅ Session works! DDoS-Guard bypassed")
            return True
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Session test failed: {e}")
        return False

def scrape_video_page(session, video_url):
    """Example: Scrape a specific video page"""
    try:
        print(f"\nScraping: {video_url}")
        response = session.get(video_url, timeout=30)
        
        if response.status_code == 200:
            # Extract title
            if '<title>' in response.text:
                title_start = response.text.find('<title>') + 7
                title_end = response.text.find('</title>', title_start)
                title = response.text[title_start:title_end].strip()
                print(f"Title: {title}")
            
            # Look for video sources (example)
            video_indicators = ['<video', 'video/mp4', '.mp4', 'videojs']
            found_video = any(indicator in response.text.lower() for indicator in video_indicators)
            
            if found_video:
                print("✅ Video content detected")
            else:
                print("⚠️ No obvious video content found")
                
            return response.text
        else:
            print(f"❌ HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 undetected_scraper.py <URL> [optional_video_url]")
        print("Example: python3 undetected_scraper.py https://rule34video.com/")
        print("Example: python3 undetected_scraper.py https://rule34video.com/ https://rule34video.com/video/123/example/")
        sys.exit(1)
    
    base_url = sys.argv[1]
    video_url = sys.argv[2] if len(sys.argv) > 2 else None
    
    print("=== Undetected ChromeDriver DDoS-Guard Bypass ===")
    print(f"Target: {base_url}")
    
    # Create undetected driver
    driver = create_undetected_driver()
    if not driver:
        print("❌ Failed to create driver")
        sys.exit(1)
    
    try:
        # Bypass DDoS-Guard
        if bypass_ddos_guard(driver, base_url):
            # Extract cookies
            cookies = extract_cookies(driver)
            
            # Create requests session
            session = create_requests_session(cookies)
            
            # Test the session
            if test_session(session, base_url):
                # Optionally scrape a specific video page
                if video_url:
                    scrape_video_page(session, video_url)
                
                print("\n✅ Success! You can now use this session for scraping")
                
                # Save cookies for later use (optional)
                with open('/tmp/extracted_cookies.json', 'w') as f:
                    json.dump(cookies, f, indent=2)
                print("💾 Cookies saved to /tmp/extracted_cookies.json")
                
            else:
                print("❌ Session test failed")
        else:
            print("❌ DDoS-Guard bypass failed")
            
    finally:
        print("\nClosing browser...")
        driver.quit()

if __name__ == "__main__":
    main()

