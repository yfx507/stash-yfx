#!/usr/bin/env python3
"""
Stash-compatible DDoS-Guard Bypass Proxy
This creates a local proxy server that Stash can use to scrape Rule34Video
while automatically handling DDoS-Guard challenges with undetected_chromedriver
"""

import undetected_chromedriver as uc
import time
import json
import logging
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from selenium.webdriver.support.ui import WebDriverWait

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DDoSGuardBypassManager:
    def __init__(self):
        self.session = None
        self.last_bypass_time = 0
        self.bypass_interval = 300  # 5 minutes
        self.driver = None
        self._lock = threading.Lock()
        
    def get_valid_session(self):
        """Get a valid session that can bypass DDoS-Guard"""
        with self._lock:
            current_time = time.time()
            
            # Check if we need to refresh the session
            if (not self.session or 
                current_time - self.last_bypass_time > self.bypass_interval):
                
                logger.info("Creating new DDoS-Guard bypass session...")
                self.session = self._create_bypass_session()
                if self.session:
                    self.last_bypass_time = current_time
                else:
                    return None
            
            return self.session
    
    def _create_bypass_session(self):
        """Create a new session with DDoS-Guard bypass using undetected_chromedriver"""
        try:
            # Close existing driver if any
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            
            # Create new undetected Chrome driver
            options = uc.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-gpu')
            
            self.driver = uc.Chrome(options=options, version_main=None)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Load Rule34Video to bypass DDoS-Guard
            logger.info("Loading Rule34Video to bypass DDoS-Guard...")
            self.driver.get("https://rule34video.com/")
            
            # Wait for DDoS-Guard challenge to complete
            wait = WebDriverWait(self.driver, 60)
            
            # Wait for title to change from DDoS-Guard
            def title_changed(driver):
                current_title = driver.title.lower()
                return "ddos-guard" not in current_title and "checking" not in current_title
            
            if "ddos-guard" in self.driver.title.lower():
                logger.info("DDoS-Guard challenge detected, waiting for completion...")
                wait.until(title_changed)
                logger.info("✓ DDoS-Guard challenge completed!")
            else:
                logger.info("✓ No DDoS-Guard challenge detected")
            
            # Wait for page to fully load
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            time.sleep(3)
            
            # Extract cookies
            cookies = self.driver.get_cookies()
            logger.info(f"Extracted {len(cookies)} cookies")
            
            # Create requests session with cookies
            session = requests.Session()
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
            
            # Test the session
            test_response = session.get("https://rule34video.com/", timeout=30)
            logger.info(f"Session validation response status: {test_response.status_code}")
            
            if test_response.status_code == 200:
                if "DDOS-GUARD" not in test_response.text:
                    logger.info("✓ Session validation successful!")
                    return session
                else:
                    logger.warning("Session still shows DDoS-Guard, but returning anyway")
                    return session  # Sometimes works anyway
            else:
                logger.error(f"Session validation failed with status {test_response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating bypass session: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

class StashProxyHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, bypass_manager=None, **kwargs):
        self.bypass_manager = bypass_manager
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests from Stash"""
        try:
            # Parse the requested URL
            parsed_path = urlparse(self.path)
            
            # Extract the target URL from query parameters
            if parsed_path.path == '/proxy':
                query_params = parse_qs(parsed_path.query)
                if 'url' in query_params:
                    target_url = unquote(query_params['url'][0])
                else:
                    self.send_error(400, "Missing 'url' parameter")
                    return
            else:
                self.send_error(404, "Use /proxy?url=<rule34video_url>")
                return
            
            # Validate that it's a Rule34Video URL
            if not target_url.startswith('https://rule34video.com/'):
                self.send_error(403, "Only Rule34Video URLs are allowed")
                return
            
            logger.info(f"Proxying Stash request to: {target_url}")
            
            # Get valid session
            session = self.bypass_manager.get_valid_session()
            if not session:
                self.send_error(503, "Failed to create bypass session")
                return
            
            # Make the request
            response = session.get(target_url, timeout=30)
            
            # Check if we got DDoS-Guard challenge again
            if "DDOS-GUARD" in response.text:
                logger.warning("DDoS-Guard challenge detected, refreshing session...")
                self.bypass_manager.session = None  # Force session refresh
                session = self.bypass_manager.get_valid_session()
                if session:
                    response = session.get(target_url, timeout=30)
            
            # Send response back to Stash
            self.send_response(response.status_code)
            
            # Copy headers (exclude some that might cause issues)
            excluded_headers = {'transfer-encoding', 'content-encoding', 'connection'}
            for header, value in response.headers.items():
                if header.lower() not in excluded_headers:
                    self.send_header(header, value)
            
            # Add CORS headers for Stash
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', '*')
            
            self.end_headers()
            self.wfile.write(response.content)
            
            logger.info(f"✓ Successfully proxied {target_url} (Status: {response.status_code})")
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_error(500, f"Proxy error: {str(e)}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")

def create_handler_with_bypass_manager(bypass_manager):
    """Create a handler class with the bypass manager injected"""
    def handler(*args, **kwargs):
        return StashProxyHandler(*args, bypass_manager=bypass_manager, **kwargs)
    return handler

def main():
    """Main function to start the proxy server"""
    port = 8890
    
    print("=" * 60)
    print("Stash DDoS-Guard Bypass Proxy Server")
    print("=" * 60)
    print(f"Starting proxy server on port {port}")
    print(f"Usage in Stash: http://localhost:{port}/proxy?url=<rule34video_url>")
    print("Scraper file: Rule34Video_Bypass.yml")
    print("=" * 60)
    
    # Create DDoS-Guard bypass manager
    bypass_manager = DDoSGuardBypassManager()
    
    # Create HTTP server
    handler_class = create_handler_with_bypass_manager(bypass_manager)
    server = HTTPServer(('localhost', port), handler_class)
    
    logger.info(f"Proxy server ready on http://localhost:{port}")
    logger.info("Stash can now use the Rule34Video_Bypass.yml scraper")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down proxy server...")
        bypass_manager.cleanup()
        server.shutdown()

if __name__ == "__main__":
    main()

