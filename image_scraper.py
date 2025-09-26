#!/usr/bin/env python3
"""
Simple Image Scraper - Single Subcategory Processing
Clicks on images one by one, extracts prompts from popups, closes them, and moves to next image
"""

import os
import csv
import json
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('image_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleImageScraper:
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with visual debugging enabled"""
        try:
            # Only create driver if it doesn't exist or is closed
            if self.driver is None:
                chrome_options = Options()
                
                # VISUAL DEBUGGING MODE - Browser will be visible
                # chrome_options.add_argument("--headless")  # Disabled for visual debugging
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-software-rasterizer")
                chrome_options.add_argument("--disable-background-timer-throttling")
                chrome_options.add_argument("--disable-backgrounding-occluded-windows")
                chrome_options.add_argument("--disable-renderer-backgrounding")
                chrome_options.add_argument("--disable-features=TranslateUI")
                chrome_options.add_argument("--disable-ipc-flooding-protection")
                
                # Memory and CPU optimizations
                chrome_options.add_argument("--memory-pressure-off")
                chrome_options.add_argument("--max_old_space_size=4096")
                chrome_options.add_argument("--aggressive-cache-discard")
                
                # Network optimizations
                chrome_options.add_argument("--disable-background-networking")
                chrome_options.add_argument("--disable-default-apps")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-sync")
                chrome_options.add_argument("--disable-translate")
                chrome_options.add_argument("--metrics-recording-only")
                chrome_options.add_argument("--mute-audio")
                chrome_options.add_argument("--no-first-run")
                chrome_options.add_argument("--safebrowsing-disable-auto-update")
                
                # Window and display settings for visual debugging
                chrome_options.add_argument("--window-size=1400,900")  # Larger window for better visibility
                chrome_options.add_argument("--start-maximized")  # Start maximized for better visibility
                chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # Additional performance settings
                chrome_options.add_experimental_option("useAutomationExtension", False)
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                
                # Enable images for image scraping (opposite of video scraper)
                prefs = {
                    "profile.default_content_setting_values.notifications": 2,  # Block notifications
                    # Note: We need images enabled for image scraping, so we don't block them
                }
                chrome_options.add_experimental_option("prefs", prefs)
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                # Add visual debugging JavaScript functions
                self.add_visual_debugging_functions()
                
                # Optimized timeouts for faster execution
                self.driver.implicitly_wait(5)  # Reduced from 10
                self.driver.set_page_load_timeout(15)  # Reduced from 30
                
                logger.info("✅ Chrome driver setup complete (headless mode with performance optimizations and visual debugging)")
            
        except Exception as e:
            logger.error(f"❌ Error setting up driver: {str(e)}")
            raise

    def add_visual_debugging_functions(self):
        """Add JavaScript functions for visual debugging indicators"""
        visual_debug_js = """
        // Visual debugging functions
        window.addClickIndicator = function(element) {
            if (!element) return;
            
            // Create red highlight overlay
            const indicator = document.createElement('div');
            indicator.style.position = 'absolute';
            indicator.style.border = '3px solid red';
            indicator.style.backgroundColor = 'rgba(255, 0, 0, 0.2)';
            indicator.style.pointerEvents = 'none';
            indicator.style.zIndex = '9999';
            indicator.style.borderRadius = '4px';
            indicator.className = 'scraper-click-indicator';
            
            // Position the indicator over the element
            const rect = element.getBoundingClientRect();
            indicator.style.left = (rect.left + window.scrollX - 3) + 'px';
            indicator.style.top = (rect.top + window.scrollY - 3) + 'px';
            indicator.style.width = (rect.width + 6) + 'px';
            indicator.style.height = (rect.height + 6) + 'px';
            
            document.body.appendChild(indicator);
            
            // Remove indicator after 2 seconds
            setTimeout(() => {
                if (indicator.parentNode) {
                    indicator.parentNode.removeChild(indicator);
                }
            }, 2000);
        };
        
        window.addScrollIndicator = function() {
            // Create scroll indicator
            const scrollIndicator = document.createElement('div');
            scrollIndicator.innerHTML = '📜 SCROLLING FOR MORE CONTENT...';
            scrollIndicator.style.position = 'fixed';
            scrollIndicator.style.top = '20px';
            scrollIndicator.style.right = '20px';
            scrollIndicator.style.backgroundColor = 'rgba(255, 0, 0, 0.9)';
            scrollIndicator.style.color = 'white';
            scrollIndicator.style.padding = '10px 15px';
            scrollIndicator.style.borderRadius = '5px';
            scrollIndicator.style.zIndex = '10000';
            scrollIndicator.style.fontSize = '14px';
            scrollIndicator.style.fontWeight = 'bold';
            scrollIndicator.style.boxShadow = '0 2px 10px rgba(0,0,0,0.3)';
            scrollIndicator.className = 'scraper-scroll-indicator';
            
            document.body.appendChild(scrollIndicator);
            
            // Remove after 1.5 seconds
            setTimeout(() => {
                if (scrollIndicator.parentNode) {
                    scrollIndicator.parentNode.removeChild(scrollIndicator);
                }
            }, 1500);
        };
        
        window.addActionIndicator = function(message, color = 'red') {
            // Create action indicator
            const actionIndicator = document.createElement('div');
            actionIndicator.innerHTML = message;
            actionIndicator.style.position = 'fixed';
            actionIndicator.style.top = '60px';
            actionIndicator.style.right = '20px';
            actionIndicator.style.backgroundColor = `rgba(${color === 'red' ? '255, 0, 0' : '0, 128, 0'}, 0.9)`;
            actionIndicator.style.color = 'white';
            actionIndicator.style.padding = '8px 12px';
            actionIndicator.style.borderRadius = '4px';
            actionIndicator.style.zIndex = '10000';
            actionIndicator.style.fontSize = '12px';
            actionIndicator.style.fontWeight = 'bold';
            actionIndicator.style.boxShadow = '0 2px 8px rgba(0,0,0,0.3)';
            actionIndicator.className = 'scraper-action-indicator';
            
            document.body.appendChild(actionIndicator);
            
            // Remove after 2 seconds
            setTimeout(() => {
                if (actionIndicator.parentNode) {
                    actionIndicator.parentNode.removeChild(actionIndicator);
                }
            }, 2000);
        };
        
        // Clean up any existing indicators
        window.cleanupIndicators = function() {
            const indicators = document.querySelectorAll('.scraper-click-indicator, .scraper-scroll-indicator, .scraper-action-indicator');
            indicators.forEach(indicator => {
                if (indicator.parentNode) {
                    indicator.parentNode.removeChild(indicator);
                }
            });
        };
        """
        
        try:
            self.driver.execute_script(visual_debug_js)
            logger.info("✅ Visual debugging functions added to page")
        except Exception as e:
            logger.error(f"⚠️ Could not add visual debugging functions: {e}")
    
    def visual_click(self, element, description="Clicking element"):
        """Click an element with visual indicator"""
        try:
            # Add visual indicator before clicking
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)  # Brief pause for visibility
            
            self.driver.execute_script("window.addClickIndicator(arguments[0]);", element)
            self.driver.execute_script(f"window.addActionIndicator('🖱️ {description}');")
            
            time.sleep(1)  # Pause so user can see the indicator
            
            # Perform the click
            element.click()
            logger.info(f"✅ {description}")
            
        except Exception as e:
            logger.error(f"❌ Error during visual click: {e}")
            raise
    
    def visual_scroll(self, description="Scrolling for more content"):
        """Scroll with visual indicator"""
        try:
            self.driver.execute_script("window.addScrollIndicator();")
            self.driver.execute_script(f"window.addActionIndicator('📜 {description}');")
            
            # Perform scroll
            self.driver.execute_script("window.scrollBy(0, window.innerHeight * 0.8);")
            time.sleep(1.5)  # Pause so user can see the scrolling
            
            logger.info(f"✅ {description}")
            
        except Exception as e:
            logger.error(f"❌ Error during visual scroll: {e}")
            raise

    def scrape_single_subcategory(self, subcategory_url):
        """Scrape a single subcategory by clicking figure elements one by one"""
        try:
            logger.info(f"🎯 Starting to scrape subcategory: {subcategory_url}")
            
            # Setup driver (reuse if exists)
            self.setup_driver()
            
            # Navigate to subcategory page with better error handling
            logger.info("🌐 Navigating to subcategory page...")
            try:
                self.driver.get(subcategory_url)
                logger.info(f"✅ Successfully loaded URL: {subcategory_url}")
                
                # Check if page loaded properly
                current_url = self.driver.current_url
                logger.info(f"📍 Current URL after navigation: {current_url}")
                
                # Check page title
                page_title = self.driver.title
                logger.info(f"📄 Page title: {page_title}")
                
                # Wait for page to be ready
                wait = WebDriverWait(self.driver, 10)  # Reduced from 15
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                logger.info("✅ Page body loaded successfully")
                
            except Exception as nav_error:
                logger.error(f"❌ Navigation error: {str(nav_error)}")
                logger.error(f"❌ Failed to load URL: {subcategory_url}")
                
                # Try to get current URL and page source for debugging
                try:
                    current_url = self.driver.current_url
                    logger.info(f"📍 Current URL after failed navigation: {current_url}")
                    
                    page_source_length = len(self.driver.page_source)
                    logger.info(f"📄 Page source length: {page_source_length} characters")
                    
                    if page_source_length < 100:
                        logger.warning("⚠️ Page source is very short, possible loading issue")
                        
                except Exception as debug_error:
                    logger.error(f"❌ Could not get debug info: {str(debug_error)}")
                
                raise nav_error
            
            # Wait for page loading with extended time for dynamic content
            time.sleep(5)  # Increased from 3 seconds
            logger.info("📄 Page loaded, implementing comprehensive scraping strategy...")
            
            # Additional wait for JavaScript to fully initialize
            try:
                # Wait for document ready state
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                logger.info("✅ Document ready state confirmed")
                
                # Wait for any loading indicators to disappear
                time.sleep(3)
                
            except Exception as wait_error:
                logger.warning(f"⚠️ Wait for ready state failed: {wait_error}")
                time.sleep(5)  # Fallback wait
            
            # PHASE 1: Load ALL content first by scrolling to bottom
            logger.info("🔄 PHASE 1: Loading all content by scrolling to bottom...")
            self.scroll_to_load_all_content()
            
            # PHASE 2: Count all images after complete loading
            logger.info("🔍 PHASE 2: Discovering and counting all images...")
            figures = self.find_all_image_figures()
            
            if not figures:
                logger.warning("⚠️ No figure elements found on page with primary method")
                
                # Try alternative approaches when no figures are found
                logger.info("🔄 Trying alternative image discovery methods...")
                
                # Method 1: Look for any clickable elements with images
                try:
                    alternative_elements = self.driver.find_elements(By.CSS_SELECTOR, "*[onclick] img, *[href] img, button img")
                    if alternative_elements:
                        logger.info(f"🔍 Found {len(alternative_elements)} images in clickable elements")
                        # Get parent elements
                        figures = []
                        for img in alternative_elements:
                            try:
                                parent = img.find_element(By.XPATH, "./..")
                                figures.append(parent)
                            except:
                                continue
                except Exception as e:
                    logger.debug(f"Alternative method 1 failed: {e}")
                
                # Method 2: Look for images with data attributes that might indicate interactivity
                if not figures:
                    try:
                        data_images = self.driver.find_elements(By.CSS_SELECTOR, "img[data-*], img[id], img[class*='click'], img[class*='interactive']")
                        if data_images:
                            logger.info(f"🔍 Found {len(data_images)} images with data attributes")
                            figures = data_images
                    except Exception as e:
                        logger.debug(f"Alternative method 2 failed: {e}")
                
                # Method 3: Just try all images on the page as a last resort
                if not figures:
                    try:
                        all_images = self.driver.find_elements(By.CSS_SELECTOR, "img[src]")
                        if all_images:
                            logger.warning(f"⚠️ Last resort: Found {len(all_images)} images, will try clicking them")
                            figures = all_images
                    except Exception as e:
                        logger.debug(f"Alternative method 3 failed: {e}")
                
                if not figures:
                    logger.error("❌ No images found with any method. Page might not have loaded properly or structure is different.")
                    # Add debug info about the page
                    try:
                        page_title = self.driver.title
                        current_url = self.driver.current_url
                        logger.info(f"📄 Page title: {page_title}")
                        logger.info(f"🌐 Current URL: {current_url}")
                        
                        # Check if page is still loading
                        ready_state = self.driver.execute_script("return document.readyState")
                        logger.info(f"📊 Page ready state: {ready_state}")
                        
                        # Wait a bit more and try again
                        logger.info("⏳ Waiting 5 more seconds for page to fully load...")
                        time.sleep(5)
                        figures = self.find_all_image_figures()
                        
                    except Exception as debug_error:
                        logger.error(f"❌ Debug info collection failed: {debug_error}")
                    
                    if not figures:
                        logger.warning("⚠️ Still no images found after retry - skipping this subcategory")
                        return []
                
            total_images = len(figures)
            logger.info(f"📊 TOTAL IMAGES TO PROCESS: {total_images}")
            
            # PHASE 3: Process each image systematically
            logger.info(f"🎯 PHASE 3: Processing {total_images} images systematically...")
            images_data = []
            
            # Performance tracking
            loop_start_time = time.time()
            
            # Process each figure one by one (from bottom to top for better loading)
            for i, figure in enumerate(reversed(figures)):  # Reversed for bottom-to-top processing
                try:
                    figure_start_time = time.time()
                    actual_index = total_images - i  # Calculate actual position since we're processing in reverse
                    logger.info(f"🖼️ Processing image {actual_index}/{total_images} (from bottom)")
                    
                    # Add visual indicator for current image being processed
                    self.driver.execute_script(f"window.addActionIndicator('🖼️ Processing image {actual_index}/{total_images}', 'blue');")
                    
                    # Scroll to the current figure to ensure it's visible
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", figure)
                        time.sleep(1)  # Wait for smooth scroll
                        logger.debug(f"📍 Scrolled to image {actual_index}")
                    except Exception as scroll_error:
                        logger.debug(f"Could not scroll to figure: {scroll_error}")
                    
                    # Reset image_url for each figure to prevent reusing previous values
                    figure_image_url = None
                    try:
                        # Look for image element with src attribute
                        image_element = figure.find_element(By.CSS_SELECTOR, "img[src]")
                        figure_image_url = image_element.get_attribute('src')
                        logger.info(f"🖼️ Found image URL in figure: {figure_image_url}")
                    except:
                        logger.debug("No image URL found in figure")
                    
                    # Extract unique identifier from figure for fallback
                    figure_id = None
                    try:
                        # Try to get a unique identifier from the figure's link href
                        clickable_link = figure.find_element(By.CSS_SELECTOR, "a")
                        href = clickable_link.get_attribute('href')
                        if href:
                            # Extract ID from URL path (e.g., /image/12345 -> 12345)
                            import re
                            id_match = re.search(r'/([a-f0-9-]{36}|[a-f0-9]{8,})/?$', href)
                            if id_match:
                                figure_id = id_match.group(1)
                                logger.info(f"🆔 Found figure ID from href: {figure_id}")
                        
                        # Also try data attributes for unique identifiers
                        for attr in ['data-image-id', 'data-id', 'id', 'data-key']:
                            if not figure_id:
                                try:
                                    figure_id = figure.get_attribute(attr) or clickable_link.get_attribute(attr)
                                    if figure_id:
                                        logger.info(f"🆔 Found figure ID from {attr}: {figure_id}")
                                        break
                                except:
                                    continue
                                    
                    except Exception as e:
                        logger.debug(f"Could not extract figure ID: {e}")
                    
                    # Find the clickable link within the figure
                    clickable_link = None
                    try:
                        # Try different ways to find clickable elements
                        if figure.tag_name == 'a':
                            # The figure itself is a link
                            clickable_link = figure
                            logger.debug(f"✅ Figure {actual_index} is itself a clickable link")
                        else:
                            # Look for a link inside the figure
                            clickable_link = figure.find_element(By.CSS_SELECTOR, "a")
                            logger.debug(f"✅ Found clickable link inside figure {actual_index}")
                    except:
                        # If no link found, try to make the figure itself clickable
                        logger.warning(f"⚠️ No clickable link found in figure {actual_index}, will try clicking the figure directly")
                        clickable_link = figure
                    
                    if not clickable_link:
                        logger.warning(f"⚠️ No clickable element found for image {actual_index}, skipping")
                        continue
                    
                    # If we have a figure image URL, we might not need to click the modal
                    if figure_image_url and figure_image_url.startswith('http'):
                        logger.info(f"✅ Using image URL directly from figure: {figure_image_url}")
                        
                        # Still try to get prompt by clicking modal, but use figure URL
                        clicked = False
                        try:
                            self.visual_click(clickable_link, f"Opening image {actual_index} popup for prompt")
                            clicked = True
                        except:
                            try:
                                # Method 2: JavaScript click with visual indicator
                                self.driver.execute_script("window.addClickIndicator(arguments[0]);", clickable_link)
                                self.driver.execute_script(f"window.addActionIndicator('🖱️ JavaScript click on image {actual_index}');")
                                time.sleep(1)
                                self.driver.execute_script("arguments[0].click();", clickable_link)
                                clicked = True
                                logger.info("✅ Clicked figure link (JavaScript click)")
                            except Exception as e:
                                logger.error(f"❌ Failed to click image link: {e}")
                        
                        if clicked:
                            time.sleep(3)
                            # Extract only prompt from popup, use figure URL for image
                            extracted_data = self.extract_prompt_from_popup()
                            prompt = extracted_data.get('prompt', 'No prompt found') if extracted_data else 'No prompt found'
                            
                            images_data.append({
                                'image_url': figure_image_url,
                                'prompt': prompt,
                                'figure_index': actual_index,
                                'figure_id': figure_id
                            })
                            
                            logger.info(f"✅ Extracted data for image {actual_index}: {prompt[:50]}...")
                            logger.info(f"🖼️ Image URL: {figure_image_url}")
                            
                            # Close popup
                            self.close_popup()
                            time.sleep(3)
                            continue
                    
                    # For images without direct URL, click and extract from modal (original method)
                    click_start = time.time()
                    clicked = False
                    try:
                        # Method 1: Visual click with indicator
                        self.visual_click(clickable_link, f"Opening image {actual_index} popup")
                        clicked = True
                        logger.info("✅ Clicked figure link (visual click)")
                    except:
                        try:
                            # Method 2: JavaScript click with visual indicator
                            self.driver.execute_script("window.addClickIndicator(arguments[0]);", clickable_link)
                            self.driver.execute_script(f"window.addActionIndicator('🖱️ JavaScript click on image {actual_index}');")
                            time.sleep(1)
                            self.driver.execute_script("arguments[0].click();", clickable_link)
                            clicked = True
                            logger.info("✅ Clicked figure link (JavaScript click)")
                        except:
                            try:
                                # Method 3: Action chains
                                ActionChains(self.driver).move_to_element(clickable_link).click().perform()
                                clicked = True
                                logger.info("✅ Clicked figure link (ActionChains)")
                            except Exception as e:
                                logger.error(f"❌ Failed to click image link: {e}")
                                continue
                    
                    click_time = time.time() - click_start
                    logger.debug(f"⏱️ Click time: {click_time:.2f}s")
                    
                    if not clicked:
                        logger.warning(f"⚠️ Could not click figure {i+1}, skipping")
                        continue
                    
                    # Wait for popup/modal to appear and fully load
                    time.sleep(3)
                    
                    # Extract prompt and image URL from popup with retry mechanism
                    extracted_data = None
                    for retry in range(3):  # Try up to 3 times
                        extracted_data = self.extract_prompt_from_popup()
                        
                        # Check if we got a valid, unique image URL
                        if extracted_data and extracted_data.get('image_url'):
                            current_url = extracted_data.get('image_url')
                            # Check if this URL is different from previous images
                            existing_urls = [v.get('image_url') for v in images_data if v.get('image_url')]
                            if not existing_urls or current_url not in existing_urls:
                                logger.info(f"✅ Got unique image URL on attempt {retry + 1}")
                                break
                            else:
                                logger.warning(f"⚠️ Got duplicate URL on attempt {retry + 1}, retrying...")
                                # Close and reopen modal to refresh content
                                self.close_popup()
                                time.sleep(2)
                                # Click the figure again
                                try:
                                    self.driver.execute_script("arguments[0].click();", clickable_link)
                                    time.sleep(3)
                                except:
                                    break
                        else:
                            logger.warning(f"⚠️ No image URL found on attempt {retry + 1}")
                            if retry < 2:  # Don't retry on last attempt
                                time.sleep(2)
                    
                    if extracted_data and (extracted_data.get('prompt') or extracted_data.get('image_url')):
                        # Use image URL from popup if available, otherwise use the one from figure
                        final_image_url = extracted_data.get('image_url') or figure_image_url
                        
                        # If still no image URL, create a placeholder with figure ID
                        if not final_image_url and figure_id:
                            final_image_url = f"placeholder_image_{figure_id}"
                            logger.info(f"🔄 Using placeholder URL with figure ID: {final_image_url}")
                        elif not final_image_url:
                            final_image_url = f"placeholder_image_{i+1}"
                            logger.info(f"🔄 Using placeholder URL with index: {final_image_url}")
                        
                        images_data.append({
                            'image_url': final_image_url,
                            'prompt': extracted_data.get('prompt', 'No prompt found'),
                            'figure_index': i + 1,  # Add figure index for debugging
                            'figure_id': figure_id  # Add figure ID if available
                        })
                        
                        prompt_preview = extracted_data.get('prompt', 'No prompt')[:50] if extracted_data.get('prompt') else 'No prompt'
                        logger.info(f"✅ Extracted data for figure {i+1}: {prompt_preview}...")
                        if final_image_url:
                            logger.info(f"🖼️ Image URL: {final_image_url}")
                    else:
                        # Even if no data is extracted, create an entry with unique identifier
                        final_image_url = figure_image_url
                        if not final_image_url and figure_id:
                            final_image_url = f"placeholder_image_{figure_id}"
                        elif not final_image_url:
                            final_image_url = f"placeholder_image_{i+1}"
                        
                        images_data.append({
                            'image_url': final_image_url,
                            'prompt': 'No prompt found',
                            'figure_index': i + 1,
                            'figure_id': figure_id
                        })
                        
                        logger.warning(f"⚠️ No data extracted for figure {i+1}, using placeholder")
                    
                    # Close popup after processing
                    self.close_popup()
                    
                    # Brief pause between figures for stability
                    time.sleep(2)
                    
                    figure_time = time.time() - figure_start_time
                    logger.debug(f"⏱️ Figure {i+1} processing time: {figure_time:.2f}s")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing figure {i+1}: {str(e)}")
                    # Try to close any open popup before continuing
                    try:
                        self.close_popup()
                    except:
                        pass
                    continue
            
            total_time = time.time() - loop_start_time
            logger.info(f"⏱️ Total processing time: {total_time:.2f}s for {len(figures)} figures")
            logger.info(f"🎯 Successfully scraped {len(images_data)} images from subcategory")
            
            return images_data
            
        except Exception as e:
            logger.error(f"❌ Error in scrape_single_subcategory: {str(e)}")
            return []
        finally:
            # Don't close driver here to allow reuse
            pass

    def scroll_to_load_all_content(self):
        """Scroll all the way to bottom first, wait for complete data loading, then return to top"""
        try:
            logger.info("🔄 Starting comprehensive content loading strategy...")
            
            # Add initial action indicator
            self.driver.execute_script("window.addActionIndicator('🔄 Loading ALL content first...', 'red');")
            
            # Get initial page height
            initial_height = self.driver.execute_script("return document.body.scrollHeight")
            logger.info(f"📏 Initial page height: {initial_height}px")
            
            # Phase 1: Aggressive scrolling to the very bottom
            logger.info("📜 Phase 1: Scrolling to very bottom to trigger all lazy loading...")
            self.driver.execute_script("window.addActionIndicator('📜 Phase 1: Aggressive scroll to bottom', 'red');")
            
            scroll_attempts = 0
            max_scroll_attempts = 15  # Increased for more thorough loading
            last_height = initial_height
            consecutive_same_height = 0
            
            while scroll_attempts < max_scroll_attempts and consecutive_same_height < 3:
                # Scroll to absolute bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Visual indicator for each scroll
                self.driver.execute_script(f"window.addActionIndicator('📜 Scroll {scroll_attempts + 1}: Loading more...', 'red');")
                
                # Wait longer for content to load (increased timing)
                time.sleep(3)  # Increased from 2 seconds
                
                # Check new height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                logger.info(f"📏 Scroll attempt {scroll_attempts + 1}: {last_height}px → {new_height}px")
                
                if new_height == last_height:
                    consecutive_same_height += 1
                    logger.info(f"⏸️ Same height detected {consecutive_same_height}/3 times")
                else:
                    consecutive_same_height = 0
                    
                last_height = new_height
                scroll_attempts += 1
            
            # Phase 2: Additional wait time at bottom for final loading
            logger.info("⏳ Phase 2: Waiting at bottom for final content loading...")
            self.driver.execute_script("window.addActionIndicator('⏳ Phase 2: Final loading wait...', 'red');")
            
            # Stay at bottom and wait for any remaining lazy loading
            for wait_cycle in range(3):
                time.sleep(4)  # Extended wait time
                self.driver.execute_script(f"window.addActionIndicator('⏳ Final wait cycle {wait_cycle + 1}/3', 'red');")
                
                # Try a small scroll to trigger any remaining lazy loading
                self.driver.execute_script("window.scrollBy(0, 100); setTimeout(() => window.scrollTo(0, document.body.scrollHeight), 500);")
                time.sleep(2)
            
            # Get final height after all loading
            final_height = self.driver.execute_script("return document.body.scrollHeight")
            logger.info(f"📏 Final page height after complete loading: {final_height}px")
            logger.info(f"📈 Total height increase: {final_height - initial_height}px")
            
            # Phase 3: Return to top for systematic processing
            logger.info("⬆️ Phase 3: Returning to top for systematic processing...")
            self.driver.execute_script("window.addActionIndicator('⬆️ Phase 3: Back to top for processing', 'green');")
            
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)  # Wait for scroll to complete
            
            # Final success indicator
            self.driver.execute_script("window.addActionIndicator('✅ ALL content loaded successfully!', 'green');")
            
            logger.info(f"✅ Complete content loading finished:")
            logger.info(f"   - Scroll attempts: {scroll_attempts}")
            logger.info(f"   - Height change: {initial_height}px → {final_height}px")
            logger.info(f"   - Ready for systematic image processing")
            
        except Exception as e:
            logger.error(f"❌ Error during comprehensive content loading: {str(e)}")
            self.driver.execute_script("window.addActionIndicator('❌ Content loading error', 'red');")

    def find_all_image_figures(self):
        """
        Find all job links that correspond to images on the Higgsfield Soul page.
        Based on analysis, the page uses a[href*='/job/'] links for each image.
        Returns a list of WebDriver elements.
        """
        try:
            logger.info("🔍 Looking for job links (image figures)...")
            
            # Add visual indicator for image discovery
            self.driver.execute_script("window.addActionIndicator('🔍 Discovering job links...', 'blue');")
            
            # Debug: Check what elements are actually on the page
            all_images = self.driver.find_elements(By.CSS_SELECTOR, "img")
            logger.info(f"🖼️ DEBUG: Found {len(all_images)} total img elements on page")
            
            # The key insight: Higgsfield Soul uses job links for each image
            job_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/job/']")
            logger.info(f"🎯 Found {len(job_links)} job links (clickable images)")
            
            if len(job_links) == 0:
                logger.warning("⚠️ No job links found! This might indicate:")
                logger.warning("   - The page hasn't loaded completely")
                logger.warning("   - Need to scroll more to load all images")
                logger.warning("   - The page structure has changed")
                
                # Additional debugging
                logger.info("🔍 Additional debugging info:")
                logger.info(f"   - Page URL: {self.driver.current_url}")
                logger.info(f"   - Page title: {self.driver.title}")
                
                # Check for any links
                all_links = self.driver.find_elements(By.CSS_SELECTOR, "a")
                logger.info(f"   - Total link elements: {len(all_links)}")
                
                # Check for soul links (category navigation)
                soul_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/soul/']")
                logger.info(f"   - Soul links (categories): {len(soul_links)}")
                
                # Check page source length
                page_source_length = len(self.driver.page_source)
                logger.info(f"   - Page source length: {page_source_length} characters")
                
                # Add visual indicator for no images found
                self.driver.execute_script("window.addActionIndicator('❌ No job links found - Check page structure', 'red');")
            else:
                logger.info(f"✅ Successfully found {len(job_links)} job links to process")
                
                # Log a few example URLs for debugging
                for i, link in enumerate(job_links[:3]):
                    try:
                        href = link.get_attribute('href')
                        logger.info(f"   Example {i+1}: {href}")
                    except Exception as e:
                        logger.debug(f"Error getting href for link {i+1}: {str(e)}")
                
                # Add visual indicator with count and strategy
                self.driver.execute_script(f"window.addActionIndicator('📊 Found {len(job_links)} job links - Processing bottom to top', 'green');")
                logger.info(f"🎯 Strategy: Will process {len(job_links)} job links from bottom to top")
            
            return job_links
            
        except Exception as e:
            logger.error(f"❌ Error finding job links: {str(e)}")
            self.driver.execute_script("window.addActionIndicator('❌ Error finding job links', 'red');")
            return []

    def extract_prompt_from_popup(self):
        """Extract prompt and image URL from the opened popup/modal"""
        try:
            logger.info("🔍 Extracting data from popup...")
            
            # Wait for popup to be fully loaded
            wait = WebDriverWait(self.driver, 10)
            
            # Multiple selectors for popup/modal containers
            popup_selectors = [
                "[role='dialog']",
                ".modal",
                ".popup",
                ".overlay",
                "[data-testid*='modal']",
                "[data-testid*='dialog']",
                ".MuiDialog-root",
                ".ant-modal",
                "[class*='Modal']",
                "[class*='Dialog']"
            ]
            
            popup_element = None
            for selector in popup_selectors:
                try:
                    popup_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    logger.info(f"✅ Found popup using selector: {selector}")
                    break
                except:
                    continue
            
            if not popup_element:
                logger.warning("⚠️ No popup element found, trying to extract from page body")
                popup_element = self.driver.find_element(By.TAG_NAME, "body")
            
            extracted_data = {}
            
            # Extract image URL from popup
            image_url = None
            image_selectors = [
                "img[src*='http']",  # Images with HTTP URLs
                "img[src]",  # Any image with src
                "img[srcset]",  # Images with srcset (responsive images)
                "[style*='background-image']",  # Background images
                "picture img",  # Images in picture elements
                ".image img",  # Images in image containers
                "[data-src]",  # Lazy loaded images
                "img[data-sentry-element='Image']",  # Sentry tracked images
                "img[class*='object-cover']",  # Images with object-cover class
            ]
            
            for selector in image_selectors:
                try:
                    image_elements = popup_element.find_elements(By.CSS_SELECTOR, selector)
                    for img in image_elements:
                        # Try src attribute first
                        src = img.get_attribute('src')
                        if src and src.startswith('http') and not src.endswith('.svg'):
                            image_url = src
                            logger.info(f"🖼️ Found image URL from src: {image_url}")
                            break
                        
                        # Try srcset for responsive images
                        srcset = img.get_attribute('srcset')
                        if srcset:
                            # Extract the highest quality image from srcset
                            import re
                            # Find all URLs in srcset and get the one with highest width
                            srcset_matches = re.findall(r'(https?://[^\s]+)\s+(\d+)w', srcset)
                            if srcset_matches:
                                # Sort by width and get the highest quality
                                highest_quality = max(srcset_matches, key=lambda x: int(x[1]))
                                image_url = highest_quality[0]
                                logger.info(f"🖼️ Found image URL from srcset: {image_url}")
                                break
                        
                        # Try data-src for lazy loading
                        data_src = img.get_attribute('data-src')
                        if data_src and data_src.startswith('http') and not data_src.endswith('.svg'):
                            image_url = data_src
                            logger.info(f"🖼️ Found image URL from data-src: {image_url}")
                            break
                        
                        # Try background-image from style
                        style = img.get_attribute('style')
                        if style and 'background-image' in style:
                            import re
                            bg_match = re.search(r'background-image:\s*url\(["\']?(.*?)["\']?\)', style)
                            if bg_match:
                                bg_url = bg_match.group(1)
                                if bg_url.startswith('http') and not bg_url.endswith('.svg'):
                                    image_url = bg_url
                                    logger.info(f"🖼️ Found image URL from background-image: {image_url}")
                                    break
                    
                    if image_url:
                        break
                        
                except Exception as e:
                    logger.debug(f"Error with image selector '{selector}': {e}")
                    continue
            
            extracted_data['image_url'] = image_url
            
            # Extract prompt text from popup
            prompt_text = None
            prompt_selectors = [
                # Based on the actual HTML structure provided
                "button[type='button'] .text-left",  # Button with text-left class containing prompt
                "button[class*='text-left']",  # Button with text-left in class
                "div[class*='font-light'] button",  # Button inside font-light div
                ".text-caption-m button",  # Button with caption class
                "button:has(.text-left)",  # Button containing text-left element
                # Original selectors
                "[data-testid*='prompt']",
                "[class*='prompt']",
                "[class*='description']",
                "[class*='caption']",
                "p",
                ".text",
                "[role='textbox']",
                "textarea",
                "input[type='text']",
                "[contenteditable='true']",
                ".content p",
                ".description",
                ".prompt-text"
            ]
            
            for selector in prompt_selectors:
                try:
                    prompt_elements = popup_element.find_elements(By.CSS_SELECTOR, selector)
                    for element in prompt_elements:
                        text = element.text.strip()
                        # Look for substantial text that looks like a prompt
                        if text and len(text) > 20 and not text.lower().startswith(('close', 'share', 'download', 'like', 'save', 'prompt')):
                            prompt_text = text
                            logger.info(f"📝 Found prompt text: {prompt_text[:50]}...")
                            break
                    
                    if prompt_text:
                        break
                        
                except Exception as e:
                    logger.debug(f"Error with prompt selector '{selector}': {e}")
                    continue
            
            # If no specific prompt found, try to get any meaningful text
            if not prompt_text:
                try:
                    all_text = popup_element.text.strip()
                    if all_text and len(all_text) > 10:
                        # Try to extract the most relevant part
                        lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                        # Look for lines that might be prompts (longer text, not just labels)
                        for line in lines:
                            if len(line) > 20 and not line.lower().startswith(('close', 'share', 'download', 'like', 'save')):
                                prompt_text = line
                                logger.info(f"📝 Found prompt from general text: {prompt_text[:50]}...")
                                break
                except:
                    pass
            
            extracted_data['prompt'] = prompt_text or 'No prompt found'
            
            logger.info(f"✅ Extraction complete - Image: {'Found' if image_url else 'Not found'}, Prompt: {'Found' if prompt_text else 'Not found'}")
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting from popup: {str(e)}")
            return {
                'image_url': None,
                'prompt': 'Error extracting prompt'
            }

    def close_popup(self):
        """Close the opened popup/modal"""
        try:
            logger.info("❌ Attempting to close popup...")
            
            # Multiple strategies to close popup
            close_selectors = [
                "[aria-label*='close' i]",
                "[title*='close' i]",
                ".close",
                ".close-button",
                "[data-testid*='close']",
                "[class*='close']",
                "button[aria-label*='Close']",
                "button[title*='Close']",
                "[role='button'][aria-label*='close' i]",
                ".modal-close",
                ".popup-close",
                ".overlay-close",
                "svg[class*='close']",
                "[class*='CloseIcon']",
                ".MuiIconButton-root",
                ".ant-modal-close"
            ]
            
            popup_closed = False
            
            # Try clicking close buttons
            for selector in close_selectors:
                try:
                    close_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for close_btn in close_elements:
                        if close_btn.is_displayed() and close_btn.is_enabled():
                            try:
                                self.visual_click(close_btn, f"Closing popup with {selector}")
                                popup_closed = True
                                break
                            except:
                                try:
                                    self.driver.execute_script("window.addClickIndicator(arguments[0]);", close_btn)
                                    self.driver.execute_script("window.addActionIndicator('❌ JavaScript close popup');")
                                    time.sleep(0.5)
                                    self.driver.execute_script("arguments[0].click();", close_btn)
                                    logger.info(f"✅ Closed popup using JavaScript click: {selector}")
                                    popup_closed = True
                                    break
                                except:
                                    continue
                    
                    if popup_closed:
                        break
                        
                except Exception as e:
                    logger.debug(f"Error with close selector '{selector}': {e}")
                    continue
            
            # If no close button worked, try ESC key
            if not popup_closed:
                try:
                    self.driver.execute_script("window.addActionIndicator('⌨️ Trying ESC key to close popup');")
                    time.sleep(0.5)
                    ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                    logger.info("✅ Closed popup using ESC key")
                    popup_closed = True
                except Exception as e:
                    logger.debug(f"ESC key failed: {e}")
            
            # If ESC didn't work, try clicking outside the modal
            if not popup_closed:
                try:
                    self.driver.execute_script("window.addActionIndicator('🖱️ Clicking outside popup to close');")
                    time.sleep(0.5)
                    # Click on the overlay/backdrop
                    overlay_selectors = [".overlay", ".backdrop", ".modal-backdrop", "[class*='Backdrop']"]
                    for selector in overlay_selectors:
                        try:
                            overlay = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if overlay.is_displayed():
                                self.visual_click(overlay, f"Clicking overlay to close popup ({selector})")
                                popup_closed = True
                                break
                        except:
                            continue
                except:
                    pass
            
            # Final fallback: click at a corner of the screen
            if not popup_closed:
                try:
                    self.driver.execute_script("window.addActionIndicator('🖱️ Clicking screen corner to close popup');")
                    time.sleep(0.5)
                    ActionChains(self.driver).move_by_offset(10, 10).click().perform()
                    logger.info("✅ Closed popup by clicking at screen corner")
                    popup_closed = True
                except:
                    pass
            
            if popup_closed:
                self.driver.execute_script("window.addActionIndicator('✅ Popup closed!', 'green');")
            else:
                logger.warning("⚠️ Could not close popup with any method")
                self.driver.execute_script("window.addActionIndicator('⚠️ Could not close popup', 'red');")
            
            # Brief pause to ensure popup is closed
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ Error closing popup: {str(e)}")

    def save_images_data(self, images_data, category_name="images"):
        """Save scraped images data to CSV and JSON files"""
        try:
            if not images_data:
                logger.warning("⚠️ No images data to save")
                return
            
            logger.info(f"💾 Saving {len(images_data)} images to files...")
            
            # Create category folder if it doesn't exist
            category_folder = category_name.replace(" ", "_").replace("/", "_")
            os.makedirs(category_folder, exist_ok=True)
            
            # Prepare data for saving
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save as CSV
            csv_filename = os.path.join(category_folder, "images.csv")
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['image_url', 'prompt', 'figure_index', 'figure_id']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for image_data in images_data:
                    writer.writerow({
                        'image_url': image_data.get('image_url', ''),
                        'prompt': image_data.get('prompt', ''),
                        'figure_index': image_data.get('figure_index', ''),
                        'figure_id': image_data.get('figure_id', '')
                    })
            
            logger.info(f"✅ Saved CSV file: {csv_filename}")
            
            # Save as JSON
            json_filename = os.path.join(category_folder, "images.json")
            with open(json_filename, 'w', encoding='utf-8') as jsonfile:
                json.dump({
                    'timestamp': timestamp,
                    'category': category_name,
                    'total_images': len(images_data),
                    'images': images_data
                }, jsonfile, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Saved JSON file: {json_filename}")
            
            # Print summary
            logger.info(f"📊 Summary for {category_name}:")
            logger.info(f"   Total images: {len(images_data)}")
            
            # Count images with actual URLs vs placeholders
            actual_urls = sum(1 for img in images_data if img.get('image_url') and img['image_url'].startswith('http'))
            placeholder_urls = len(images_data) - actual_urls
            
            logger.info(f"   Images with URLs: {actual_urls}")
            logger.info(f"   Placeholder entries: {placeholder_urls}")
            
            # Count images with prompts
            with_prompts = sum(1 for img in images_data if img.get('prompt') and img['prompt'] != 'No prompt found')
            logger.info(f"   Images with prompts: {with_prompts}")
            
        except Exception as e:
            logger.error(f"❌ Error saving images data: {str(e)}")

    def load_subcategories_from_metadata(self, category_folder):
        """Load subcategories from metadata.json file"""
        try:
            metadata_file = os.path.join(category_folder, "metadata.json")
            if not os.path.exists(metadata_file):
                logger.error(f"❌ Metadata file not found: {metadata_file}")
                return {}
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            logger.info(f"✅ Loaded metadata from {metadata_file}")
            
            # Convert sub_categories list to dictionary format
            subcategories = {}
            sub_categories = metadata.get('sub_categories', [])
            for subcat in sub_categories:
                subcategories[subcat['name']] = subcat['link']
            
            return subcategories
            
        except Exception as e:
            logger.error(f"❌ Error loading metadata: {str(e)}")
            return {}

    def process_category(self, category_name, process_all_subcategories=False):
        """Process a single category and its subcategories"""
        try:
            logger.info(f"🎯 Processing category: {category_name}")
            
            # Load subcategories from metadata
            subcategories = self.load_subcategories_from_metadata(category_name)
            
            if not subcategories:
                logger.error(f"❌ No subcategories found for {category_name}")
                return
            
            logger.info(f"📂 Found {len(subcategories)} subcategories")
            
            if not process_all_subcategories:
                # Show available subcategories
                print(f"\n📂 Available subcategories in {category_name}:")
                subcategory_list = list(subcategories.keys())
                for i, subcat in enumerate(subcategory_list, 1):
                    print(f"{i}. {subcat}")
                
                # Get user choice
                while True:
                    try:
                        choice = input(f"\nEnter subcategory number (1-{len(subcategory_list)}) or 'all' for all subcategories: ").strip()
                        
                        if choice.lower() == 'all':
                            process_all_subcategories = True
                            break
                        
                        choice_num = int(choice)
                        if 1 <= choice_num <= len(subcategory_list):
                            selected_subcat = subcategory_list[choice_num - 1]
                            subcategories = {selected_subcat: subcategories[selected_subcat]}
                            break
                        else:
                            print(f"❌ Please enter a number between 1 and {len(subcategory_list)}")
                    except ValueError:
                        print("❌ Please enter a valid number or 'all'")
            
            # Process selected subcategories
            for subcat_name, subcat_url in subcategories.items():
                try:
                    logger.info(f"🎯 Processing subcategory: {subcat_name}")
                    
                    # Scrape the subcategory
                    images_data = self.scrape_single_subcategory(subcat_url)
                    
                    if images_data:
                        # Save data to subcategory folder
                        subcat_folder = os.path.join(category_name, subcat_name.replace(" ", "_").replace("/", "_"))
                        self.save_images_data(images_data, subcat_folder)
                        logger.info(f"✅ Completed subcategory: {subcat_name}")
                    else:
                        logger.warning(f"⚠️ No images found in subcategory: {subcat_name}")
                    
                    # Brief pause between subcategories
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing subcategory {subcat_name}: {str(e)}")
                    continue
            
            logger.info(f"✅ Completed processing category: {category_name}")
            
        except Exception as e:
            logger.error(f"❌ Error processing category {category_name}: {str(e)}")

    def list_available_categories(self):
        """List all available categories (folders with metadata.json)"""
        try:
            categories = []
            for item in os.listdir('.'):
                if os.path.isdir(item) and os.path.exists(os.path.join(item, 'metadata.json')):
                    categories.append(item)
            
            return sorted(categories)
        except Exception as e:
            logger.error(f"❌ Error listing categories: {str(e)}")
            return []

    def run(self):
        """Main execution method"""
        try:
            logger.info("🚀 Starting Simple Image Scraper")
            
            # List available categories
            categories = self.list_available_categories()
            
            if not categories:
                logger.error("❌ No categories found. Make sure you have folders with metadata.json files.")
                return
            
            print("\n📂 Available categories:")
            for i, category in enumerate(categories, 1):
                print(f"{i}. {category}")
            
            # Automatically select category 4 (Higgsfield Soul)
            if len(categories) >= 4:
                selected_category = categories[3]  # Index 3 for category 4
                logger.info(f"🎯 Automatically selected category 4: {selected_category}")
                print(f"\n🎯 Automatically selected category 4: {selected_category}")
                
                # Process the selected category with all subcategories
                self.process_category(selected_category, process_all_subcategories=True)
            else:
                logger.error("❌ Category 4 not found. Available categories are insufficient.")
                return
            
        except KeyboardInterrupt:
            logger.info("⏹️ Scraping interrupted by user")
        except Exception as e:
            logger.error(f"❌ Error in main execution: {str(e)}")
        finally:
            # Clean up
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("✅ Browser closed")
                except:
                    pass

if __name__ == "__main__":
    scraper = SimpleImageScraper()
    scraper.run()