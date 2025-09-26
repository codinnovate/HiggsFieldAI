#!/usr/bin/env python3
"""
Page Structure Analyzer for Higgsfield Soul
Analyzes the DOM structure and URL patterns to understand how images are organized and clicked.
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PageStructureAnalyzer:
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        logger.info("🚀 Setting up Chrome WebDriver...")
        
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        # Remove headless mode to see what's happening
        # chrome_options.add_argument("--headless")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)
        
        logger.info("✅ Chrome WebDriver setup complete")
        
    def analyze_main_page(self, url):
        """Analyze the main category page structure"""
        logger.info(f"🔍 Analyzing main page: {url}")
        
        self.driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        logger.info(f"📄 Page title: {self.driver.title}")
        logger.info(f"🌐 Current URL: {self.driver.current_url}")
        
        # FIRST: Perform infinite scroll to load all content
        logger.info("🔄 Simulating infinite scroll to load all images...")
        initial_img_count = len(self.driver.find_elements(By.TAG_NAME, "img"))
        logger.info(f"📊 Initial image count: {initial_img_count}")
        
        # Get initial page height
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        logger.info(f"📏 Initial page height: {last_height}px")
        
        # Scroll down multiple times to trigger infinite scroll
        for scroll_attempt in range(10):  # Increased attempts
            logger.info(f"🔄 Scroll attempt {scroll_attempt + 1}/10...")
            
            # Scroll to bottom with more aggressive approach
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for content to load
            time.sleep(4)  # Increased wait time
            
            # Check if page height changed (indicates new content loaded)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            new_img_count = len(self.driver.find_elements(By.TAG_NAME, "img"))
            
            logger.info(f"📊 After scroll {scroll_attempt + 1}: {new_img_count} images, height: {new_height}px")
            
            # If no new content loaded for 2 consecutive attempts, stop
            if new_height == last_height and new_img_count == initial_img_count:
                logger.info("📊 No new content loaded, stopping scroll")
                break
                
            last_height = new_height
            initial_img_count = new_img_count
            
            # Additional scroll techniques to trigger lazy loading
            self.driver.execute_script("window.scrollBy(0, -100);")  # Scroll up a bit
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # Back to bottom
            time.sleep(2)
        
        # Return to top
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)  # Wait for scroll to complete
        
        final_img_count = len(self.driver.find_elements(By.TAG_NAME, "img"))
        final_height = self.driver.execute_script("return document.body.scrollHeight")
        logger.info(f"📊 Final results: {final_img_count} images, {final_height}px height")
        
        # NOW: Count basic elements after loading all content
        images = self.driver.find_elements(By.TAG_NAME, "img")
        links = self.driver.find_elements(By.TAG_NAME, "a")
        
        logger.info(f"🖼️ Found {len(images)} img elements")
        logger.info(f"🔗 Found {len(links)} link elements")
        
        # Check for clickable images (images inside links)
        clickable_images = self.driver.find_elements(By.CSS_SELECTOR, "a img")
        logger.info(f"🎯 Found {len(clickable_images)} clickable images (img inside a)")
        
        # Analyze specific patterns
        self.analyze_image_patterns()
        
        # Try to find job links
        job_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/soul/job/']")
        logger.info(f"💼 Found {len(job_links)} job links")
        
        if job_links:
            logger.info("📋 Job link examples:")
            for i, link in enumerate(job_links[:3]):  # Show first 3
                href = link.get_attribute('href')
                logger.info(f"   {i+1}. {href}")
                
        return job_links
        
    def analyze_image_patterns(self):
        """Analyze different image patterns on the page"""
        logger.info("🔍 Analyzing image patterns...")
        
        # Pattern 1: Images with srcset
        srcset_images = self.driver.find_elements(By.CSS_SELECTOR, "img[srcset]")
        logger.info(f"📸 Images with srcset: {len(srcset_images)}")
        
        # Pattern 2: Images with data attributes (fix the selector)
        try:
            data_images = self.driver.find_elements(By.CSS_SELECTOR, "img[data-testid]")
            logger.info(f"📊 Images with data-testid: {len(data_images)}")
        except:
            logger.info("📊 Images with data attributes: selector failed")
        
        # Check for specific data attributes
        try:
            sentry_images = self.driver.find_elements(By.CSS_SELECTOR, "img[data-sentry-element]")
            logger.info(f"🔍 Images with data-sentry-element: {len(sentry_images)}")
        except:
            pass
        
        # Pattern 3: Images with specific classes
        class_patterns = [
            "img[class*='object-cover']",
            "img[class*='rounded']",
            "img[class*='aspect']",
            "img[class*='w-full']",
            "img[class*='h-full']"
        ]
        
        for pattern in class_patterns:
            elements = self.driver.find_elements(By.CSS_SELECTOR, pattern)
            logger.info(f"🎨 {pattern}: {len(elements)} elements")
            
        # Check for figure elements
        figures = self.driver.find_elements(By.CSS_SELECTOR, "figure")
        logger.info(f"📦 Figure elements: {len(figures)}")
        
        # Check for div containers with images
        div_with_images = self.driver.find_elements(By.CSS_SELECTOR, "div:has(img)")
        logger.info(f"📦 Divs containing images: {len(div_with_images)}")
        

        
        # Look for clickable images with different patterns
        clickable_patterns = [
            "div[class*='cursor-pointer'] img",
            "div[role='button'] img", 
            "[onclick] img",
            "div[class*='clickable'] img",
            "div[class*='hover'] img",
            "div[class*='cursor-pointer']",  # Just the clickable divs
            "div[role='button']",
            "[onclick]"
        ]
        
        for pattern in clickable_patterns:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, pattern)
                logger.info(f"🔍 Selector '{pattern}': {len(elements)} elements")
                
                # If we find clickable divs, check if they contain images
                if len(elements) > 0 and 'img' not in pattern:
                    images_in_clickable = 0
                    for elem in elements[:5]:  # Check first 5
                        imgs = elem.find_elements(By.TAG_NAME, "img")
                        if imgs:
                            images_in_clickable += 1
                    logger.info(f"   └─ {images_in_clickable} of first 5 contain images")
                    
            except Exception as e:
                logger.info(f"🔍 Selector '{pattern}': failed - {str(e)}")
        
        # Try to find the actual clickable elements that lead to job pages
        try:
            # Look for elements with href containing '/job/'
            job_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/job/']")
            logger.info(f"🎯 Direct job links: {len(job_links)} elements")
            
            # Look for any clickable elements that might navigate to job pages
            all_clickable = self.driver.find_elements(By.CSS_SELECTOR, "[onclick], [role='button'], .cursor-pointer, a")
            logger.info(f"🎯 All potentially clickable elements: {len(all_clickable)} elements")
            
        except Exception as e:
            logger.info(f"🎯 Error finding job links: {str(e)}")
        
    def analyze_job_page(self, job_url):
        """Analyze the job/image detail page structure"""
        logger.info(f"🔍 Analyzing job page: {job_url}")
        
        self.driver.get(job_url)
        time.sleep(3)
        
        logger.info(f"📄 Job page title: {self.driver.title}")
        logger.info(f"🌐 Job page URL: {self.driver.current_url}")
        
        # Look for the main image
        main_images = self.driver.find_elements(By.CSS_SELECTOR, "img")
        logger.info(f"🖼️ Images on job page: {len(main_images)}")
        
        # Look for prompt text
        text_elements = self.driver.find_elements(By.CSS_SELECTOR, "p, div, span")
        logger.info(f"📝 Text elements: {len(text_elements)}")
        
        # Try to find prompt-like content
        for element in text_elements[:10]:  # Check first 10 text elements
            text = element.text.strip()
            if len(text) > 50:  # Likely a prompt if it's long
                logger.info(f"📝 Potential prompt: {text[:100]}...")
                
    def click_first_image_and_analyze(self, main_page_url):
        """Click the first available image and analyze the result"""
        logger.info(f"🎯 Attempting to click first image on: {main_page_url}")
        
        self.driver.get(main_page_url)
        time.sleep(5)
        
        # Try different selectors to find clickable images
        selectors = [
            "a[href*='/soul/job/'] img",  # Images inside job links
            "a img",  # Any image inside a link
            "img[srcset]",  # Images with srcset (might be clickable)
            "div[class*='cursor-pointer'] img",  # Images in clickable divs
        ]
        
        for selector in selectors:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            logger.info(f"🔍 Selector '{selector}': {len(elements)} elements")
            
            if elements:
                try:
                    # Get the clickable parent if it's an image
                    if selector.endswith(" img"):
                        # Find the parent link
                        clickable = elements[0].find_element(By.XPATH, "./..")
                    else:
                        clickable = elements[0]
                    
                    logger.info(f"🎯 Clicking element with tag: {clickable.tag_name}")
                    
                    # Get the href if it's a link
                    if clickable.tag_name == 'a':
                        href = clickable.get_attribute('href')
                        logger.info(f"🔗 Link href: {href}")
                    
                    # Click the element
                    clickable.click()
                    time.sleep(3)
                    
                    # Analyze the result
                    new_url = self.driver.current_url
                    logger.info(f"🎯 After click - New URL: {new_url}")
                    
                    if '/soul/job/' in new_url:
                        logger.info("✅ Successfully navigated to job page!")
                        self.analyze_job_page(new_url)
                        return new_url
                    else:
                        logger.warning("⚠️ Click didn't lead to job page")
                        
                except Exception as e:
                    logger.error(f"❌ Error clicking element: {e}")
                    continue
                    
        logger.warning("⚠️ No clickable images found")
        return None
        
    def run_analysis(self):
        """Run the complete page structure analysis"""
        try:
            self.setup_driver()
            
            # URLs to analyze
            main_page = "https://higgsfield.ai/soul/464ea177-8d40-4940-8d9d-b438bab269c7"
            job_page = "https://higgsfield.ai/soul/job/91f2c2fc-d243-4519-b47a-999ea80e7daf"
            
            logger.info("=" * 60)
            logger.info("🔍 ANALYZING MAIN PAGE STRUCTURE")
            logger.info("=" * 60)
            
            job_links = self.analyze_main_page(main_page)
            
            logger.info("=" * 60)
            logger.info("🎯 TESTING IMAGE CLICKING")
            logger.info("=" * 60)
            
            clicked_url = self.click_first_image_and_analyze(main_page)
            
            logger.info("=" * 60)
            logger.info("🔍 ANALYZING JOB PAGE STRUCTURE")
            logger.info("=" * 60)
            
            self.analyze_job_page(job_page)
            
            logger.info("=" * 60)
            logger.info("📊 ANALYSIS COMPLETE")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🔚 WebDriver closed")

if __name__ == "__main__":
    analyzer = PageStructureAnalyzer()
    analyzer.run_analysis()