#!/usr/bin/env python3
"""
Test script to verify job link detection on Higgsfield Soul pages
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_driver():
    """Setup Chrome driver with optimized settings"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def test_job_links(url):
    """Test job link detection on a specific URL"""
    driver = setup_driver()
    
    try:
        logger.info(f"🌐 Navigating to: {url}")
        driver.get(url)
        time.sleep(5)  # Wait for page load
        
        logger.info(f"📄 Page title: {driver.title}")
        logger.info(f"📍 Current URL: {driver.current_url}")
        
        # Check basic page elements
        all_images = driver.find_elements(By.CSS_SELECTOR, "img")
        logger.info(f"🖼️ Total img elements: {len(all_images)}")
        
        all_links = driver.find_elements(By.CSS_SELECTOR, "a")
        logger.info(f"🔗 Total link elements: {len(all_links)}")
        
        # Test job link detection
        job_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/job/']")
        logger.info(f"🎯 Job links found: {len(job_links)}")
        
        if len(job_links) > 0:
            logger.info("✅ SUCCESS: Job links detected!")
            for i, link in enumerate(job_links[:5]):  # Show first 5
                try:
                    href = link.get_attribute('href')
                    logger.info(f"   {i+1}. {href}")
                except Exception as e:
                    logger.error(f"   {i+1}. Error getting href: {e}")
        else:
            logger.warning("❌ No job links found!")
            
            # Additional debugging
            logger.info("🔍 Debugging info:")
            
            # Check for soul links
            soul_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/soul/']")
            logger.info(f"   - Soul links: {len(soul_links)}")
            
            # Check page source length
            page_source_length = len(driver.page_source)
            logger.info(f"   - Page source length: {page_source_length} chars")
            
            # Check if we need to scroll
            page_height = driver.execute_script("return document.body.scrollHeight")
            logger.info(f"   - Page height: {page_height}px")
            
            # Try scrolling to load more content
            logger.info("🔄 Trying to scroll to load more content...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Check again after scroll
            job_links_after_scroll = driver.find_elements(By.CSS_SELECTOR, "a[href*='/job/']")
            logger.info(f"🎯 Job links after scroll: {len(job_links_after_scroll)}")
            
            if len(job_links_after_scroll) > 0:
                logger.info("✅ SUCCESS: Job links found after scrolling!")
                for i, link in enumerate(job_links_after_scroll[:5]):
                    try:
                        href = link.get_attribute('href')
                        logger.info(f"   {i+1}. {href}")
                    except Exception as e:
                        logger.error(f"   {i+1}. Error getting href: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error during test: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    # Test URLs from our analysis
    test_urls = [
        "https://higgsfield.ai/soul/464ea177-8d40-4940-8d9d-b438bab269c7",  # General
        "https://higgsfield.ai/soul/88126a43-86fb-4047-a2d6-c9146d6ca6ce",  # Duplicate
        "https://higgsfield.ai/soul/8dd89de9-1cff-402e-88a8-580c29d91473",  # 0.5 Selfie
    ]
    
    for url in test_urls:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing URL: {url}")
        logger.info(f"{'='*60}")
        test_job_links(url)
        time.sleep(2)  # Brief pause between tests