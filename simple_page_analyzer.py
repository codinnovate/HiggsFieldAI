#!/usr/bin/env python3
"""
Simple Page Structure Analyzer for Higgsfield Soul
Focuses on understanding the page structure and infinite scroll behavior
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimplePageAnalyzer:
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Set up Chrome WebDriver with proper options"""
        logger.info("🚀 Setting up Chrome WebDriver...")
        
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)
        
        logger.info("✅ Chrome WebDriver setup complete")
        
    def analyze_page_loading(self, url):
        """Analyze how the page loads and what elements are present"""
        logger.info(f"🔍 Analyzing page loading for: {url}")
        
        try:
            # Navigate to the page
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info(f"📄 Page title: {self.driver.title}")
            logger.info(f"🌐 Current URL: {self.driver.current_url}")
            
            # Check initial state
            initial_images = len(self.driver.find_elements(By.TAG_NAME, "img"))
            initial_height = self.driver.execute_script("return document.body.scrollHeight")
            
            logger.info(f"📊 Initial state: {initial_images} images, {initial_height}px height")
            
            # Wait a bit for any lazy loading
            time.sleep(5)
            
            # Check after waiting
            after_wait_images = len(self.driver.find_elements(By.TAG_NAME, "img"))
            after_wait_height = self.driver.execute_script("return document.body.scrollHeight")
            
            logger.info(f"📊 After 5s wait: {after_wait_images} images, {after_wait_height}px height")
            
            # Try scrolling down slowly
            logger.info("🔄 Attempting slow scroll...")
            for i in range(5):
                scroll_position = (i + 1) * 500
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(2)
                
                current_images = len(self.driver.find_elements(By.TAG_NAME, "img"))
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                
                logger.info(f"📊 After scroll {i+1}: {current_images} images, {current_height}px height")
                
                if current_images > after_wait_images:
                    logger.info("✅ New images loaded during scroll!")
                    break
            
            # Scroll to bottom
            logger.info("🔄 Scrolling to bottom...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
            
            final_images = len(self.driver.find_elements(By.TAG_NAME, "img"))
            final_height = self.driver.execute_script("return document.body.scrollHeight")
            
            logger.info(f"📊 Final state: {final_images} images, {final_height}px height")
            
            # Check for specific elements that might contain images
            self.check_image_containers()
            
        except Exception as e:
            logger.error(f"❌ Error analyzing page: {str(e)}")
            
    def check_image_containers(self):
        """Check for different types of image containers"""
        logger.info("🔍 Checking for image containers...")
        
        try:
            # Check for various container patterns
            containers = [
                ("div with images", "div img"),
                ("clickable divs", "div[class*='cursor-pointer']"),
                ("role=button", "[role='button']"),
                ("data-testid", "[data-testid]"),
                ("object-cover class", ".object-cover"),
                ("job links", "a[href*='/job/']"),
                ("soul links", "a[href*='/soul/']"),
            ]
            
            for name, selector in containers:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.info(f"📦 {name}: {len(elements)} elements")
                except Exception as e:
                    logger.warning(f"⚠️ Error checking {name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"❌ Error checking containers: {str(e)}")
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("🔚 WebDriver closed")

def main():
    analyzer = SimplePageAnalyzer()
    
    try:
        analyzer.setup_driver()
        
        # Analyze the main category page
        main_url = "https://higgsfield.ai/soul/464ea177-8d40-4940-8d9d-b438bab269c7"
        analyzer.analyze_page_loading(main_url)
        
    except Exception as e:
        logger.error(f"❌ Main error: {str(e)}")
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()