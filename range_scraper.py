#!/usr/bin/env python3
"""
Range Video Scraper - Single Subcategory Processing with Range Selection
Clicks on videos one by one based on specified range, extracts prompts from popups, closes them, and moves to next video
Supports range input like: 1-5, 1,2,3,4,5, or 0 for all videos
"""

import os
import csv
import json
import time
import logging
import re
from pathlib import Path
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
        logging.FileHandler('range_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RangeVideoScraper:
    def __init__(self):
        self.driver = None
        
    def parse_low_video_count_file(self, file_path="low_video_count_categories.txt"):
        """Parse the low video count categories file and extract categories/subcategories with 0-1 videos"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"❌ Low video count file not found: {file_path}")
                return {}
            
            logger.info(f"📄 Parsing low video count file: {file_path}")
            
            low_count_data = {}
            current_category = None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines and headers
                if not line or line.startswith('=') or line.startswith('-') or line.startswith('CATEGORIES') or line.startswith('SUMMARY'):
                    continue
                
                # Parse category line
                if line.startswith('CATEGORY:'):
                    current_category = line.replace('CATEGORY:', '').strip()
                    low_count_data[current_category] = []
                    logger.debug(f"📂 Found category: {current_category}")
                    continue
                
                # Skip metadata lines
                if line.startswith('Total subcategories:') or line.startswith('Low count subcategories:'):
                    continue
                
                # Parse subcategory line
                if line.startswith('•') and current_category:
                    # Extract subcategory name and count
                    # Format: "  • Subcategory Name (Count: X)"
                    match = re.match(r'\s*•\s*(.+?)\s*\(Count:\s*(\d+)\)', line)
                    if match:
                        subcategory_name = match.group(1).strip()
                        video_count = int(match.group(2))
                        
                        low_count_data[current_category].append({
                            'name': subcategory_name,
                            'video_count': video_count
                        })
                        logger.debug(f"📹 Found subcategory: {subcategory_name} (Count: {video_count})")
            
            # Remove categories with no subcategories
            low_count_data = {k: v for k, v in low_count_data.items() if v}
            
            total_subcategories = sum(len(subcats) for subcats in low_count_data.values())
            logger.info(f"✅ Parsed {len(low_count_data)} categories with {total_subcategories} low-count subcategories")
            
            return low_count_data
            
        except Exception as e:
            logger.error(f"❌ Error parsing low video count file: {str(e)}")
            return {}
    
    def load_metadata_for_category(self, category_name):
        """Load metadata.json for a specific category to get subcategory URLs"""
        try:
            # Search for metadata.json file in category directory
            root_directory = Path(".")
            
            for root, dirs, files in os.walk(root_directory):
                if 'metadata.json' in files:
                    metadata_path = Path(root) / 'metadata.json'
                    
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        # Check if this is the correct category
                        if metadata.get('category_name') == category_name:
                            logger.info(f"✅ Found metadata for category: {category_name}")
                            return metadata
                            
                    except Exception as e:
                        logger.debug(f"Error reading {metadata_path}: {str(e)}")
                        continue
            
            logger.warning(f"⚠️ No metadata found for category: {category_name}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error loading metadata for category {category_name}: {str(e)}")
            return None
    
    def get_subcategory_url(self, category_metadata, subcategory_name):
        """Get the URL for a specific subcategory from category metadata"""
        try:
            if not category_metadata:
                return None
            
            sub_categories = category_metadata.get('sub_categories', [])
            
            for subcategory in sub_categories:
                if subcategory.get('name') == subcategory_name:
                    url = subcategory.get('link', '')
                    if url:
                        logger.info(f"🔗 Found URL for {subcategory_name}: {url}")
                        return url
            
            logger.warning(f"⚠️ No URL found for subcategory: {subcategory_name}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting URL for subcategory {subcategory_name}: {str(e)}")
            return None
    
    def auto_rescrape_low_count_categories(self, low_count_file="low_video_count_categories.txt"):
        """Automatically rescrape all categories/subcategories with 0-1 video counts"""
        try:
            logger.info("🚀 Starting automatic rescraping of low video count categories...")
            
            # Parse the low count file
            low_count_data = self.parse_low_video_count_file(low_count_file)
            
            if not low_count_data:
                logger.error("❌ No low count data found. Exiting.")
                return
            
            total_categories = len(low_count_data)
            total_subcategories = sum(len(subcats) for subcats in low_count_data.values())
            
            logger.info(f"📊 Found {total_categories} categories with {total_subcategories} low-count subcategories to rescrape")
            
            # Process each category
            processed_categories = 0
            processed_subcategories = 0
            
            for category_name, subcategories in low_count_data.items():
                try:
                    processed_categories += 1
                    logger.info(f"📂 Processing category {processed_categories}/{total_categories}: {category_name}")
                    logger.info(f"📹 Found {len(subcategories)} subcategories to rescrape")
                    
                    # Load metadata for this category
                    category_metadata = self.load_metadata_for_category(category_name)
                    
                    if not category_metadata:
                        logger.warning(f"⚠️ Skipping category {category_name} - no metadata found")
                        continue
                    
                    # Process each subcategory
                    for subcategory in subcategories:
                        try:
                            processed_subcategories += 1
                            subcategory_name = subcategory['name']
                            video_count = subcategory['video_count']
                            
                            logger.info(f"🎯 Processing subcategory {processed_subcategories}/{total_subcategories}: {subcategory_name} (Current count: {video_count})")
                            
                            # Get subcategory URL
                            subcategory_url = self.get_subcategory_url(category_metadata, subcategory_name)
                            
                            if not subcategory_url:
                                logger.warning(f"⚠️ Skipping {subcategory_name} - no URL found")
                                continue
                            
                            # Scrape this subcategory (all videos)
                            logger.info(f"🔄 Scraping all videos from: {subcategory_name}")
                            videos_data = self.scrape_single_subcategory(subcategory_url)
                            
                            if videos_data:
                                # Save the scraped data
                                folder_name = f"{category_name}_{subcategory_name}"
                                self.save_videos_data(videos_data, folder_name)
                                
                                logger.info(f"✅ Successfully scraped {len(videos_data)} videos from {subcategory_name}")
                            else:
                                logger.warning(f"⚠️ No videos found for {subcategory_name}")
                            
                            # Small delay between subcategories
                            time.sleep(2)
                            
                        except Exception as e:
                            logger.error(f"❌ Error processing subcategory {subcategory_name}: {str(e)}")
                            continue
                    
                    logger.info(f"✅ Completed category: {category_name}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing category {category_name}: {str(e)}")
                    continue
            
            logger.info(f"🎉 Auto-rescraping completed!")
            logger.info(f"📊 Processed {processed_categories}/{total_categories} categories")
            logger.info(f"📹 Processed {processed_subcategories}/{total_subcategories} subcategories")
            
        except Exception as e:
            logger.error(f"❌ Error in auto-rescraping: {str(e)}")
            raise
        
    def setup_driver(self):
        """Setup Chrome driver with optimized options for performance"""
        try:
            # Only create driver if it doesn't exist or is closed
            if self.driver is None:
                chrome_options = Options()
                
                # Performance optimizations
                chrome_options.add_argument("--headless")  # Run in headless mode for speed
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
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
                chrome_options.add_argument("--hide-scrollbars")
                chrome_options.add_argument("--metrics-recording-only")
                chrome_options.add_argument("--mute-audio")
                chrome_options.add_argument("--no-first-run")
                chrome_options.add_argument("--safebrowsing-disable-auto-update")
                
                # Window and display settings
                chrome_options.add_argument("--window-size=1280,720")  # Smaller window for better performance
                chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # Additional performance settings
                chrome_options.add_experimental_option("useAutomationExtension", False)
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                
                # Disable images and CSS for faster loading (optional - comment out if needed)
                prefs = {
                    "profile.managed_default_content_settings.images": 2,  # Block images
                    "profile.default_content_setting_values.notifications": 2,  # Block notifications
                    "profile.managed_default_content_settings.stylesheets": 2,  # Block CSS (optional)
                }
                chrome_options.add_experimental_option("prefs", prefs)
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                # Optimized timeouts for faster execution
                self.driver.implicitly_wait(5)  # Reduced from 10
                self.driver.set_page_load_timeout(15)  # Reduced from 30
                
                logger.info("✅ Chrome driver setup complete (headless mode with performance optimizations)")
            
        except Exception as e:
            logger.error(f"❌ Error setting up driver: {str(e)}")
            raise

    def parse_range_input(self, range_input, max_videos):
        """
        Parse range input and return list of video indices to process
        Supports formats:
        - "0" or "all": all videos
        - "1-5": range from 1 to 5
        - "1,2,3,4,5": comma-separated list
        - "1-3,5,7-9": mixed format
        """
        try:
            range_input = range_input.strip().lower()
            
            # Handle "all" or "0" case
            if range_input in ["0", "all"]:
                return list(range(1, max_videos + 1))
            
            # Parse the input
            indices = set()
            
            # Split by comma first
            parts = [part.strip() for part in range_input.split(',')]
            
            for part in parts:
                if '-' in part and not part.startswith('-'):
                    # Handle range like "1-5"
                    try:
                        start, end = part.split('-', 1)
                        start = int(start.strip())
                        end = int(end.strip())
                        
                        if start > end:
                            start, end = end, start  # Swap if reversed
                        
                        for i in range(start, end + 1):
                            if 1 <= i <= max_videos:
                                indices.add(i)
                    except ValueError:
                        logger.warning(f"⚠️ Invalid range format: {part}")
                        continue
                else:
                    # Handle single number
                    try:
                        num = int(part)
                        if 1 <= num <= max_videos:
                            indices.add(num)
                        else:
                            logger.warning(f"⚠️ Number {num} is out of range (1-{max_videos})")
                    except ValueError:
                        logger.warning(f"⚠️ Invalid number format: {part}")
                        continue
            
            # Convert to sorted list
            result = sorted(list(indices))
            logger.info(f"📋 Parsed range input '{range_input}' -> videos: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error parsing range input '{range_input}': {str(e)}")
            return []

    def scrape_single_subcategory(self, subcategory_url, video_range=None):
        """Scrape a single subcategory by clicking figure elements based on specified range"""
        try:
            logger.info(f"🎯 Starting to scrape subcategory: {subcategory_url}")
            if video_range:
                logger.info(f"📋 Video range specified: {video_range}")
            
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
            
            # Wait for page loading
            time.sleep(3)
            logger.info("📄 Page loaded, looking for figure elements...")
            
            # Scroll to load all videos (handle lazy loading)
            logger.info("🔄 Scrolling to load all videos...")
            self.scroll_to_load_all_content()
            
            # Find all figure elements that contain videos with multiple selectors
            figures = self.find_all_video_figures()
            
            if not figures:
                logger.warning("⚠️ No figure elements found on page")
                return []
                
            logger.info(f"🎬 Found {len(figures)} figure elements")
            
            # Determine which videos to process
            if video_range is None:
                # Process all videos if no range specified
                videos_to_process = list(range(len(figures)))
                logger.info(f"📋 Processing all {len(figures)} videos")
            else:
                # Convert 1-based user input to 0-based array indices
                videos_to_process = [i - 1 for i in video_range if 1 <= i <= len(figures)]
                logger.info(f"📋 Processing {len(videos_to_process)} videos from range: {[i+1 for i in videos_to_process]}")
            
            if not videos_to_process:
                logger.warning("⚠️ No valid videos to process based on range")
                return []
            
            videos_data = []
            
            # Performance tracking
            loop_start_time = time.time()
            
            # Process each selected figure
            for idx, figure_index in enumerate(videos_to_process):
                try:
                    figure = figures[figure_index]
                    figure_start_time = time.time()
                    logger.info(f"🎥 Processing video {figure_index+1} ({idx+1}/{len(videos_to_process)})")
                    
                    # Reset video_url for each figure to prevent reusing previous values
                    figure_video_url = None
                    try:
                        video_element = figure.find_element(By.CSS_SELECTOR, "video[src]")
                        figure_video_url = video_element.get_attribute('src')
                        logger.info(f"🎬 Found video URL in figure: {figure_video_url}")
                    except:
                        logger.debug("No video URL found in figure")
                    
                    # Extract unique identifier from figure for fallback
                    figure_id = None
                    try:
                        # Try to get a unique identifier from the figure's link href
                        clickable_link = figure.find_element(By.CSS_SELECTOR, "a")
                        href = clickable_link.get_attribute('href')
                        if href:
                            # Extract ID from URL path (e.g., /video/12345 -> 12345)
                            id_match = re.search(r'/([a-f0-9-]{36}|[a-f0-9]{8,})/?$', href)
                            if id_match:
                                figure_id = id_match.group(1)
                                logger.info(f"🆔 Found figure ID from href: {figure_id}")
                        
                        # Also try data attributes for unique identifiers
                        for attr in ['data-video-id', 'data-id', 'id', 'data-key']:
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
                        clickable_link = figure.find_element(By.CSS_SELECTOR, "a")
                    except:
                        logger.warning(f"⚠️ No clickable link found in figure {figure_index+1}")
                        continue
                    
                    # If we have a figure video URL, we might not need to click the modal
                    if figure_video_url and figure_video_url.startswith('http'):
                        logger.info(f"✅ Using video URL directly from figure: {figure_video_url}")
                        
                        # Still try to get prompt by clicking modal, but use figure URL
                        clicked = False
                        try:
                            clickable_link.click()
                            clicked = True
                            logger.info("✅ Clicked figure link (regular click)")
                        except:
                            try:
                                # Method 2: JavaScript click
                                self.driver.execute_script("arguments[0].click();", clickable_link)
                                clicked = True
                                logger.info("✅ Clicked figure link (JavaScript click)")
                            except Exception as e:
                                logger.error(f"❌ Failed to click video link: {e}")
                        
                        if clicked:
                            time.sleep(3)
                            # Extract only prompt from popup, use figure URL for video
                            extracted_data = self.extract_prompt_from_popup()
                            prompt = extracted_data.get('prompt', 'No prompt found') if extracted_data else 'No prompt found'
                            
                            videos_data.append({
                                'video_url': figure_video_url,
                                'prompt': prompt,
                                'figure_index': figure_index + 1,
                                'figure_id': figure_id
                            })
                            
                            logger.info(f"✅ Extracted data for figure {figure_index+1}: {prompt[:50]}...")
                            logger.info(f"🎬 Video URL: {figure_video_url}")
                            
                            # Close popup
                            self.close_popup()
                            time.sleep(3)
                            continue
                    
                    # Scroll to figure to ensure it's visible
                    scroll_start = time.time()
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", figure)
                    time.sleep(1)  # Reduced from 2 seconds
                    scroll_time = time.time() - scroll_start
                    logger.debug(f"⏱️ Scroll time: {scroll_time:.2f}s")
                    
                    # Fallback: click and extract from modal (original method)
                    click_start = time.time()
                    clicked = False
                    try:
                        # Method 1: Regular click
                        clickable_link.click()
                        clicked = True
                        logger.info("✅ Clicked figure link (regular click)")
                    except:
                        try:
                            # Method 2: JavaScript click
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
                                logger.error(f"❌ Failed to click video link: {e}")
                                continue
                    
                    click_time = time.time() - click_start
                    logger.debug(f"⏱️ Click time: {click_time:.2f}s")
                    
                    if not clicked:
                        logger.warning(f"⚠️ Could not click figure {figure_index+1}, skipping")
                        continue
                    
                    # Wait for popup/modal to appear and fully load
                    time.sleep(3)
                    
                    # Extract prompt and video URL from popup with retry mechanism
                    extracted_data = None
                    for retry in range(3):  # Try up to 3 times
                        extracted_data = self.extract_prompt_from_popup()
                        
                        # Check if we got a valid, unique video URL
                        if extracted_data and extracted_data.get('video_url'):
                            current_url = extracted_data.get('video_url')
                            # Check if this URL is different from previous videos
                            existing_urls = [v.get('video_url') for v in videos_data if v.get('video_url')]
                            if not existing_urls or current_url not in existing_urls:
                                logger.info(f"✅ Got unique video URL on attempt {retry + 1}")
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
                            logger.warning(f"⚠️ No video URL found on attempt {retry + 1}")
                            if retry < 2:  # Don't retry on last attempt
                                time.sleep(2)
                    
                    if extracted_data and (extracted_data.get('prompt') or extracted_data.get('video_url')):
                        # Use video URL from popup if available, otherwise use the one from figure
                        final_video_url = extracted_data.get('video_url') or figure_video_url
                        
                        # If still no video URL, create a placeholder with figure ID
                        if not final_video_url and figure_id:
                            final_video_url = f"placeholder_video_{figure_id}"
                            logger.info(f"🔄 Using placeholder URL with figure ID: {final_video_url}")
                        elif not final_video_url:
                            final_video_url = f"placeholder_video_{figure_index+1}"
                            logger.info(f"🔄 Using placeholder URL with index: {final_video_url}")
                        
                        videos_data.append({
                            'video_url': final_video_url,
                            'prompt': extracted_data.get('prompt', 'No prompt found'),
                            'figure_index': figure_index + 1,  # Add figure index for debugging
                            'figure_id': figure_id  # Add figure ID if available
                        })
                        
                        prompt_preview = extracted_data.get('prompt', 'No prompt')[:50] if extracted_data.get('prompt') else 'No prompt'
                        logger.info(f"✅ Extracted data for figure {figure_index+1}: {prompt_preview}...")
                        if final_video_url:
                            logger.info(f"🎬 Video URL: {final_video_url}")
                    else:
                        # Even if no data is extracted, create an entry with unique identifier
                        final_video_url = figure_video_url
                        if not final_video_url and figure_id:
                            final_video_url = f"placeholder_video_{figure_id}"
                        elif not final_video_url:
                            final_video_url = f"placeholder_video_{figure_index+1}"
                        
                        videos_data.append({
                            'video_url': final_video_url,
                            'prompt': 'No prompt found',
                            'figure_index': figure_index + 1,
                            'figure_id': figure_id
                        })
                        logger.warning(f"⚠️ No data found for figure {figure_index+1}, using placeholder: {final_video_url}")
                    
                    # Close popup and return to main page
                    self.close_popup()
                    
                    # Performance logging
                    figure_time = time.time() - figure_start_time
                    logger.debug(f"⏱️ Figure {figure_index+1} processing time: {figure_time:.2f}s")
                    
                    # Small delay between videos to avoid overwhelming the server
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing figure {figure_index+1}: {str(e)}")
                    continue
            
            # Performance summary
            total_time = time.time() - loop_start_time
            avg_time = total_time / len(videos_to_process) if videos_to_process else 0
            logger.info(f"⏱️ Total processing time: {total_time:.2f}s")
            logger.info(f"⏱️ Average time per video: {avg_time:.2f}s")
            
            logger.info(f"🎉 Scraping completed! Extracted {len(videos_data)} videos from range")
            return videos_data
            
        except Exception as e:
            logger.error(f"❌ Error in scrape_single_subcategory: {str(e)}")
            return []
        finally:
            # Clean up driver
            if self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                    logger.info("🧹 Driver cleaned up")
                except:
                    pass

    def scroll_to_load_all_content(self):
        """Scroll down the page to trigger lazy loading of all videos"""
        try:
            logger.info("🔄 Starting scroll to load all content...")
            
            # Get initial page height
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scroll_attempts = 10  # Prevent infinite scrolling
            
            while scroll_attempts < max_scroll_attempts:
                # Scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait for new content to load
                time.sleep(2)
                
                # Calculate new scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                # If height hasn't changed, we've reached the end
                if new_height == last_height:
                    logger.info(f"✅ Finished scrolling after {scroll_attempts + 1} attempts")
                    break
                    
                last_height = new_height
                scroll_attempts += 1
                logger.debug(f"📏 Scroll attempt {scroll_attempts}: height = {new_height}")
            
            # Scroll back to top for consistent starting position
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ Error during scrolling: {str(e)}")

    def find_all_video_figures(self):
        """Find all figure elements that contain videos using multiple selectors"""
        try:
            figures = []
            
            # Try multiple selectors to find video figures
            selectors = [
                "figure",  # Basic figure elements
                "div[class*='video']",  # Divs with 'video' in class name
                "div[data-video-id]",  # Divs with video ID data attribute
                "article",  # Article elements (sometimes used for video cards)
                ".video-card",  # Common video card class
                ".video-item",  # Common video item class
                "[data-testid*='video']",  # Elements with video in test ID
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    # Filter elements that actually contain video-related content
                    for element in elements:
                        try:
                            # Check if element contains a clickable link and video-related content
                            has_link = element.find_elements(By.CSS_SELECTOR, "a")
                            has_video_content = (
                                element.find_elements(By.CSS_SELECTOR, "video") or
                                element.find_elements(By.CSS_SELECTOR, "img") or
                                "video" in element.get_attribute("class").lower() if element.get_attribute("class") else False
                            )
                            
                            if has_link and (has_video_content or selector == "figure"):
                                if element not in figures:  # Avoid duplicates
                                    figures.append(element)
                                    
                        except Exception as e:
                            logger.debug(f"Error checking element: {e}")
                            continue
                            
                    if figures:
                        logger.info(f"✅ Found {len(figures)} figures using selector: {selector}")
                        break  # Use the first successful selector
                        
                except Exception as e:
                    logger.debug(f"Selector '{selector}' failed: {e}")
                    continue
            
            # Remove duplicates while preserving order
            unique_figures = []
            seen = set()
            for fig in figures:
                fig_id = id(fig)  # Use object ID to identify unique elements
                if fig_id not in seen:
                    seen.add(fig_id)
                    unique_figures.append(fig)
            
            logger.info(f"🎬 Found {len(unique_figures)} unique video figures")
            return unique_figures
            
        except Exception as e:
            logger.error(f"❌ Error finding video figures: {str(e)}")
            return []

    def extract_prompt_from_popup(self):
        """Extract prompt and video URL from the opened popup/modal"""
        try:
            logger.debug("🔍 Extracting data from popup...")
            
            # Wait for popup to be fully loaded
            wait = WebDriverWait(self.driver, 10)
            
            # Try to find the popup/modal container
            popup_selectors = [
                "[role='dialog']",
                ".modal",
                ".popup",
                ".overlay",
                "[data-testid*='modal']",
                "[data-testid*='dialog']",
                ".video-modal",
                ".video-popup"
            ]
            
            popup_element = None
            for selector in popup_selectors:
                try:
                    popup_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    logger.debug(f"✅ Found popup using selector: {selector}")
                    break
                except:
                    continue
            
            if not popup_element:
                logger.warning("⚠️ Could not find popup element, searching in entire page")
                popup_element = self.driver.find_element(By.TAG_NAME, "body")
            
            # Extract video URL
            video_url = None
            video_selectors = [
                "video[src]",
                "source[src]",
                "[data-video-url]",
                "[data-src*='.mp4']",
                "video source[src]"
            ]
            
            for selector in video_selectors:
                try:
                    video_element = popup_element.find_element(By.CSS_SELECTOR, selector)
                    video_url = video_element.get_attribute('src') or video_element.get_attribute('data-src')
                    if video_url:
                        logger.debug(f"🎬 Found video URL using selector: {selector}")
                        break
                except:
                    continue
            
            # Extract prompt text
            prompt = None
            prompt_selectors = [
                "[data-testid*='prompt']",
                ".prompt",
                ".description",
                ".video-description",
                ".caption",
                ".video-caption",
                "p",
                ".text",
                "[class*='prompt']",
                "[class*='description']"
            ]
            
            for selector in prompt_selectors:
                try:
                    prompt_elements = popup_element.find_elements(By.CSS_SELECTOR, selector)
                    for element in prompt_elements:
                        text = element.text.strip()
                        if text and len(text) > 10:  # Filter out very short text
                            prompt = text
                            logger.debug(f"📝 Found prompt using selector: {selector}")
                            break
                    if prompt:
                        break
                except:
                    continue
            
            # If no specific prompt found, try to get any meaningful text
            if not prompt:
                try:
                    all_text = popup_element.text.strip()
                    # Filter out common UI text and get meaningful content
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                    meaningful_lines = [
                        line for line in lines 
                        if len(line) > 15 and not any(ui_text in line.lower() for ui_text in 
                        ['close', 'share', 'download', 'like', 'follow', 'subscribe', 'view', 'play'])
                    ]
                    if meaningful_lines:
                        prompt = meaningful_lines[0]  # Take the first meaningful line
                        logger.debug("📝 Found prompt from general text extraction")
                except:
                    pass
            
            result = {
                'video_url': video_url,
                'prompt': prompt or 'No prompt found'
            }
            
            logger.debug(f"✅ Extracted data: video_url={bool(video_url)}, prompt_length={len(prompt) if prompt else 0}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error extracting data from popup: {str(e)}")
            return {
                'video_url': None,
                'prompt': 'Error extracting prompt'
            }

    def close_popup(self):
        """Close the opened popup/modal and return to main page"""
        try:
            logger.debug("🔒 Attempting to close popup...")
            
            # Try multiple methods to close the popup
            close_methods = [
                # Method 1: Click close button
                lambda: self._click_close_button(),
                # Method 2: Press Escape key
                lambda: self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE),
                # Method 3: Click overlay/backdrop
                lambda: self._click_overlay(),
                # Method 4: Browser back button
                lambda: self.driver.back(),
            ]
            
            for i, method in enumerate(close_methods, 1):
                try:
                    method()
                    time.sleep(2)  # Wait for popup to close
                    
                    # Check if popup is closed by looking for main page elements
                    if self._is_popup_closed():
                        logger.debug(f"✅ Popup closed using method {i}")
                        return True
                        
                except Exception as e:
                    logger.debug(f"Close method {i} failed: {e}")
                    continue
            
            logger.warning("⚠️ Could not close popup with any method")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error closing popup: {str(e)}")
            return False

    def _click_close_button(self):
        """Try to click a close button"""
        close_selectors = [
            "[aria-label*='close' i]",
            "[title*='close' i]",
            ".close",
            ".close-button",
            ".modal-close",
            ".popup-close",
            "button[class*='close']",
            "[data-testid*='close']",
            "svg[class*='close']",
            ".icon-close",
            "button:contains('×')",
            "button:contains('✕')"
        ]
        
        for selector in close_selectors:
            try:
                close_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                if close_button.is_displayed():
                    close_button.click()
                    return True
            except:
                continue
        
        raise Exception("No close button found")

    def _click_overlay(self):
        """Try to click the overlay/backdrop to close popup"""
        overlay_selectors = [
            ".overlay",
            ".backdrop",
            ".modal-backdrop",
            ".popup-overlay",
            "[class*='overlay']",
            "[class*='backdrop']"
        ]
        
        for selector in overlay_selectors:
            try:
                overlay = self.driver.find_element(By.CSS_SELECTOR, selector)
                if overlay.is_displayed():
                    # Click on the overlay (not the content)
                    ActionChains(self.driver).move_to_element(overlay).click().perform()
                    return True
            except:
                continue
        
        raise Exception("No overlay found")

    def _is_popup_closed(self):
        """Check if popup is closed by looking for main page elements"""
        try:
            # Look for figure elements that should be visible on main page
            figures = self.driver.find_elements(By.CSS_SELECTOR, "figure")
            return len(figures) > 0
        except:
            return False

    def save_videos_data(self, videos_data, category_name="videos"):
        """Save videos data to JSON and CSV files"""
        if not videos_data:
            logger.warning("⚠️ No videos data to save")
            return
        
        # Parse category and subcategory from category_name (format: "Category_Subcategory")
        if "_" in category_name:
            category, subcategory = category_name.split("_", 1)
            # Create folder structure: Category/Subcategory
            folder_path = os.path.join(category, subcategory)
        else:
            # Fallback to original behavior if no underscore
            safe_name = "".join(c for c in category_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            folder_path = safe_name
        
        os.makedirs(folder_path, exist_ok=True)
        
        # Remove duplicates based on video_url while preserving order
        seen_urls = set()
        unique_videos = []
        for video in videos_data:
            video_url = video.get('video_url', '')
            if video_url and video_url not in seen_urls:
                seen_urls.add(video_url)
                unique_videos.append(video)
            elif not video_url:
                # Keep videos without URLs but make them unique by adding index
                unique_videos.append(video)
        
        logger.info(f"📊 Removed {len(videos_data) - len(unique_videos)} duplicate videos")
        logger.info(f"📊 Saving {len(unique_videos)} unique videos")
        
        # Filter out figure_id and figure_index from saved data
        filtered_videos = []
        for video in unique_videos:
            filtered_video = {k: v for k, v in video.items() if k not in ['figure_id', 'figure_index']}
            filtered_videos.append(filtered_video)
        
        # Save as JSON
        json_path = os.path.join(folder_path, 'videos.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_videos, f, indent=2, ensure_ascii=False)
        
        # Save as CSV
        csv_path = os.path.join(folder_path, 'videos.csv')
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            if filtered_videos:
                # Get all possible fieldnames from all video entries (excluding figure_id and figure_index)
                fieldnames = set()
                for video in filtered_videos:
                    fieldnames.update(video.keys())
                fieldnames = sorted(list(fieldnames))
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(filtered_videos)
        
        logger.info(f"💾 Saved {len(filtered_videos)} unique videos to {folder_path}/")

    def load_subcategories_from_metadata(self, category_folder):
        """Load subcategories from metadata.json file"""
        try:
            metadata_path = os.path.join(category_folder, "metadata.json")
            
            if not os.path.exists(metadata_path):
                logger.error(f"❌ metadata.json not found in {category_folder}")
                return []
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            subcategories = metadata.get('sub_categories', [])
            logger.info(f"📋 Loaded {len(subcategories)} subcategories from {metadata_path}")
            
            return subcategories
            
        except Exception as e:
            logger.error(f"❌ Error loading metadata from {category_folder}: {str(e)}")
            return []

    def process_category(self, category_name, process_all_subcategories=False):
        """Process a single category, optionally processing all its subcategories"""
        try:
            logger.info(f"📂 Processing category: {category_name}")
            
            # Load subcategories
            subcategories = self.load_subcategories_from_metadata(category_name)
            if not subcategories:
                logger.error(f"❌ No subcategories found in {category_name}")
                return
            
            if process_all_subcategories:
                # Process all subcategories
                for subcat in subcategories:
                    logger.info(f"🎬 Processing subcategory: {subcat['name']}")
                    videos_data = self.scrape_single_subcategory(subcat['link'])
                    
                    if videos_data:
                        folder_name = f"{category_name}_{subcat['name']}"
                        self.save_videos_data(videos_data, folder_name)
                        logger.info(f"✅ Completed {subcat['name']}: {len(videos_data)} videos")
                    else:
                        logger.warning(f"⚠️ No videos extracted from {subcat['name']}")
            else:
                # This shouldn't happen in the current flow, but kept for completeness
                logger.info("Single subcategory processing not implemented in this method")
                
        except Exception as e:
            logger.error(f"❌ Error processing category {category_name}: {str(e)}")

    def list_available_categories(self):
        """List all available categories (folders with metadata.json)"""
        try:
            categories = []
            current_dir = os.getcwd()
            
            for item in os.listdir(current_dir):
                item_path = os.path.join(current_dir, item)
                if os.path.isdir(item_path):
                    metadata_path = os.path.join(item_path, "metadata.json")
                    if os.path.exists(metadata_path):
                        categories.append(item_path)
            
            return sorted(categories)
            
        except Exception as e:
            logger.error(f"❌ Error listing categories: {str(e)}")
            return []

    def run(self):
        """Main execution method with range selection and auto-rescraping option"""
        try:
            logger.info("🚀 Starting Range Video Scraper - Single Subcategory Mode with Range Selection")
            
            # Add auto-rescraping option
            print("\n🎯 Range Video Scraper Options:")
            print("  1. Manual category/subcategory selection (original mode)")
            print("  2. Auto-rescrape low video count categories (0-1 videos)")
            
            try:
                mode_choice = int(input("\nSelect mode (1-2): ").strip())
                
                if mode_choice == 2:
                    # Auto-rescraping mode
                    logger.info("🔄 Starting auto-rescraping mode for low video count categories...")
                    
                    # Check if low count file exists
                    low_count_file = "low_video_count_categories.txt"
                    if not os.path.exists(low_count_file):
                        logger.error(f"❌ Low video count file not found: {low_count_file}")
                        logger.info("💡 Please run low_video_count_analysis.py first to generate the file")
                        return
                    
                    # Confirm auto-rescraping
                    print(f"\n⚠️  This will automatically rescrape ALL categories/subcategories with 0-1 videos")
                    print(f"📄 Using file: {low_count_file}")
                    confirm = input("Proceed with auto-rescraping? (y/n): ").strip().lower()
                    
                    if confirm not in ['y', 'yes']:
                        logger.info("🛑 Auto-rescraping cancelled by user")
                        return
                    
                    # Start auto-rescraping
                    self.auto_rescrape_low_count_categories(low_count_file)
                    return
                    
                elif mode_choice != 1:
                    logger.error("❌ Invalid mode selection")
                    return
                    
            except ValueError:
                logger.error("❌ Please enter a valid number")
                return
            
            # Original manual mode continues below
            logger.info("📋 Manual category/subcategory selection mode")
            
            # List available categories
            categories = self.list_available_categories()
            if not categories:
                logger.error("❌ No categories with metadata.json found!")
                return
            
            print("\n📂 Available categories:")
            print("  0. All categories (process consecutively)")
            for i, category in enumerate(categories, 1):
                print(f"  {i}. {os.path.basename(category)}")
            
            # Get category choice
            try:
                choice = int(input(f"\nSelect category (0-{len(categories)}): ").strip())
                if choice == 0:
                    # Process all categories consecutively
                    logger.info("🔄 Processing all categories consecutively...")
                    for category in categories:
                        logger.info(f"\n📂 Processing category: {os.path.basename(category)}")
                        self.process_category(category, process_all_subcategories=True)
                    logger.info("🎉 All categories processed!")
                    return
                elif 1 <= choice <= len(categories):
                    selected_category = categories[choice - 1]
                else:
                    logger.error("❌ Invalid category selection")
                    return
            except ValueError:
                logger.error("❌ Please enter a valid number")
                return
            
            # Load subcategories from selected category
            subcategories = self.load_subcategories_from_metadata(selected_category)
            if not subcategories:
                logger.error(f"❌ No subcategories found in {os.path.basename(selected_category)}")
                return
            
            print(f"\n🎬 Available subcategories in {os.path.basename(selected_category)}:")
            print("  0. All subcategories (process consecutively)")
            for i, subcat in enumerate(subcategories, 1):
                print(f"  {i}. {subcat['name']}")
            
            # Get subcategory choice (support multiple selections)
            print("\n📋 Selection Options:")
            print("  - Single: Enter one number (e.g., 5)")
            print("  - Multiple: Enter comma-separated numbers (e.g., 1,3,5,7)")
            print("  - All: Enter 0")
            
            choice_input = input(f"\nSelect subcategory(ies) (0-{len(subcategories)}): ").strip()
            
            try:
                if choice_input == "0":
                    # Process all subcategories consecutively
                    self.process_category(selected_category, process_all_subcategories=True)
                    return
                
                # Parse multiple choices
                choices = []
                for choice_str in choice_input.split(','):
                    choice_str = choice_str.strip()
                    if choice_str:
                        choice = int(choice_str)
                        if 1 <= choice <= len(subcategories):
                            choices.append(choice)
                        else:
                            logger.error(f"❌ Invalid subcategory selection: {choice}")
                            return
                
                if not choices:
                    logger.error("❌ No valid subcategory selections found")
                    return
                
                # Get selected subcategories
                selected_subcats = [subcategories[choice - 1] for choice in choices]
                
            except ValueError:
                logger.error("❌ Please enter valid numbers separated by commas")
                return
            
            # Process each selected subcategory
            for i, selected_subcat in enumerate(selected_subcats, 1):
                print(f"\n{'='*60}")
                print(f"🎯 Processing {i}/{len(selected_subcats)}: {selected_subcat['name']} from {os.path.basename(selected_category)}")
                print(f"🔗 URL: {selected_subcat['link']}")
                print(f"📋 Will scrape ALL videos from this subcategory")
                print(f"{'='*60}")
                
                # Get total number of videos available
                logger.info("🔍 Checking total number of videos available...")
                
                # Do a quick scan to count videos
                temp_scraper = RangeVideoScraper()
                try:
                    temp_scraper.setup_driver()
                    temp_scraper.driver.get(selected_subcat['link'])
                    time.sleep(3)
                    temp_scraper.scroll_to_load_all_content()
                    figures = temp_scraper.find_all_video_figures()
                    total_videos = len(figures)
                    temp_scraper.driver.quit()
                    
                    logger.info(f"📊 Found {total_videos} total videos available")
                    
                    if total_videos == 0:
                        logger.error("❌ No videos found in subcategory, skipping")
                        continue
                    
                except Exception as e:
                    logger.error(f"❌ Error counting videos: {str(e)}, skipping this subcategory")
                    continue
                
                # Set video range to all videos (1 to total_videos)
                video_range = list(range(1, total_videos + 1))
                logger.info(f"📋 Will process ALL {len(video_range)} videos")
                
                # Confirm with user for each subcategory
                confirm = input(f"\nProceed to scrape ALL {total_videos} videos from '{selected_subcat['name']}'? (y/n/skip): ").strip().lower()
                if confirm in ['n', 'no']:
                    logger.info("🛑 Operation cancelled by user")
                    return
                elif confirm in ['skip', 's']:
                    logger.info(f"⏭️ Skipping '{selected_subcat['name']}'")
                    continue
                elif confirm not in ['y', 'yes']:
                    logger.info(f"⏭️ Invalid input, skipping '{selected_subcat['name']}'")
                    continue
                
                # Scrape the selected subcategory with all videos
                videos_data = self.scrape_single_subcategory(selected_subcat['link'], video_range)
                
                if videos_data:
                    # Save with proper category and subcategory names
                    folder_name = f"{os.path.basename(selected_category)}_{selected_subcat['name']}"
                    self.save_videos_data(videos_data, folder_name)
                    logger.info(f"🎉 Scraping completed for '{selected_subcat['name']}'! Extracted {len(videos_data)} videos")
                else:
                    logger.warning(f"⚠️ No videos were extracted from '{selected_subcat['name']}'")
            
            logger.info(f"✅ Finished processing all {len(selected_subcats)} selected subcategories")
                
        except KeyboardInterrupt:
            logger.info("🛑 Scraping interrupted by user")
        except Exception as e:
            logger.error(f"❌ Error in main execution: {str(e)}")

if __name__ == "__main__":
    scraper = RangeVideoScraper()
    scraper.run()