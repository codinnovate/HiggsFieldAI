#!/usr/bin/env python3
"""
Automated Video Scraper
Automatically scrapes all missing/incomplete subcategories without manual intervention.
Inherits from SimpleVideoScraper and uses the detection logic to find missing subcategories.
"""

import os
import json
import logging
import time
from datetime import datetime
from simple_scraper import SimpleVideoScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomatedVideoScraper(SimpleVideoScraper):
    """Automated scraper that processes all missing subcategories without manual intervention"""
    
    def __init__(self):
        super().__init__()
        self.processed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
    def check_videos_json(self, videos_json_path):
        """Check if videos.json exists and has sufficient content"""
        if not os.path.exists(videos_json_path):
            return 'missing', 0
        
        try:
            with open(videos_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, list):
                return 'invalid', 0
                
            count = len(data)
            if count == 0:
                return 'empty', 0
            elif count <= 2:  # Consider 2 or fewer videos as needing more content
                return 'single_item', count
            else:
                return 'populated', count
                
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Error reading {videos_json_path}: {e}")
            return 'invalid', 0
    
    def find_missing_subcategories(self, root_dir="."):
        """Find all subcategories that need scraping (missing or incomplete)"""
        missing_subcategories = []
        
        logger.info(f"🔍 Scanning for missing subcategories in: {root_dir}")
        
        # First check if root_dir itself has metadata.json (like Visual Effects)
        root_metadata_path = os.path.join(root_dir, 'metadata.json')
        if os.path.exists(root_metadata_path):
            try:
                with open(root_metadata_path, 'r', encoding='utf-8') as f:
                    root_metadata = json.load(f)
                    
                root_category_name = root_metadata.get('category_name', os.path.basename(root_dir))
                root_subcategories = root_metadata.get('sub_categories', [])
                
                logger.info(f"📂 Found root category: {root_category_name} ({len(root_subcategories)} subcategories)")
                
                for subcat in root_subcategories:
                    subcat_name = subcat.get('name', 'Unknown')
                    subcat_link = subcat.get('link', '')
                    
                    if not subcat_link:
                        logger.warning(f"⚠️ No link for subcategory: {subcat_name}")
                        continue
                        
                    # Check if subcategory directory exists and has videos.json
                    subcat_path = os.path.join(root_dir, subcat_name)
                    videos_json_path = os.path.join(subcat_path, 'videos.json')
                    
                    status, count = self.check_videos_json(videos_json_path)
                    
                    logger.debug(f"📊 Checking {root_category_name}/{subcat_name}: status={status}, count={count}")
                    
                    if status in ['missing', 'empty', 'single_item', 'invalid']:
                        missing_subcategories.append({
                            'category': root_category_name,
                            'subcategory': subcat_name,
                            'url': subcat_link,
                            'path': subcat_path,
                            'status': status,
                            'current_count': count
                        })
                        logger.info(f"🎯 Found missing: {root_category_name}/{subcat_name} (status: {status}, count: {count})")
                    else:
                        logger.debug(f"✅ Skipping {root_category_name}/{subcat_name} (status: {status}, count: {count})")
                        
                logger.info(f"📊 Found {len(missing_subcategories)} subcategories to scrape")
                return missing_subcategories
                        
            except Exception as e:
                logger.error(f"❌ Error processing root metadata: {e}")
        
        # If no root metadata, scan subdirectories for individual categories
        for item in os.listdir(root_dir):
            item_path = os.path.join(root_dir, item)
            
            if not os.path.isdir(item_path):
                continue
                
            metadata_path = os.path.join(item_path, 'metadata.json')
            if not os.path.exists(metadata_path):
                logger.debug(f"⏭️ Skipping {item} - no metadata.json")
                continue
                
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    
                category_name = metadata.get('category_name', item)
                subcategories = metadata.get('sub_categories', [])
                
                logger.info(f"📂 Checking category: {category_name} ({len(subcategories)} subcategories)")
                
                # Check if this is a category with subcategories listed in metadata
                if subcategories:
                    # This is a parent category with subcategories defined in metadata
                    for subcat in subcategories:
                        subcat_name = subcat.get('name', 'Unknown')
                        subcat_link = subcat.get('link', '')
                        
                        if not subcat_link:
                            logger.warning(f"⚠️ No link for subcategory: {subcat_name}")
                            continue
                            
                        # Check if subcategory directory exists and has videos.json
                        subcat_path = os.path.join(item_path, subcat_name)
                        videos_json_path = os.path.join(subcat_path, 'videos.json')
                        
                        status, count = self.check_videos_json(videos_json_path)
                        
                        logger.debug(f"📊 Checking {category_name}/{subcat_name}: status={status}, count={count}")
                        
                        if status in ['missing', 'empty', 'single_item', 'invalid']:
                            missing_subcategories.append({
                                'category': category_name,
                                'subcategory': subcat_name,
                                'url': subcat_link,
                                'path': subcat_path,
                                'status': status,
                                'current_count': count
                            })
                            logger.info(f"🎯 Found missing: {category_name}/{subcat_name} (status: {status}, count: {count})")
                        else:
                            logger.debug(f"✅ Skipping {category_name}/{subcat_name} (status: {status}, count: {count})")
                else:
                    # This might be a standalone category/subcategory, check if it needs scraping
                    videos_json_path = os.path.join(item_path, 'videos.json')
                    status, count = self.check_videos_json(videos_json_path)
                    
                    logger.debug(f"📊 Checking standalone {category_name}: status={status}, count={count}")
                    
                    if status in ['missing', 'empty', 'single_item', 'invalid']:
                        # For standalone categories, we need to find the link from parent metadata if available
                        parent_metadata_path = os.path.join(os.path.dirname(item_path), 'metadata.json')
                        subcat_link = ""
                        
                        if os.path.exists(parent_metadata_path):
                            try:
                                with open(parent_metadata_path, 'r', encoding='utf-8') as f:
                                    parent_metadata = json.load(f)
                                    parent_subcats = parent_metadata.get('sub_categories', [])
                                    for subcat in parent_subcats:
                                        if subcat.get('name') == category_name:
                                            subcat_link = subcat.get('link', '')
                                            break
                            except Exception as e:
                                logger.debug(f"Could not read parent metadata: {e}")
                        
                        if subcat_link:
                            missing_subcategories.append({
                                'category': os.path.basename(os.path.dirname(item_path)),
                                'subcategory': category_name,
                                'url': subcat_link,
                                'path': item_path,
                                'status': status,
                                'current_count': count
                            })
                            logger.info(f"🎯 Found missing standalone: {category_name} (status: {status}, count: {count})")
                        else:
                            logger.debug(f"✅ Skipping standalone {category_name} - no link found")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {item}: {e}")
                continue
        
        logger.info(f"📊 Found {len(missing_subcategories)} subcategories to scrape")
        return missing_subcategories
    
    def scrape_subcategory_with_retry(self, subcategory_info, max_retries=2):
        """Scrape a single subcategory with retry logic"""
        category = subcategory_info['category']
        subcategory = subcategory_info['subcategory']
        url = subcategory_info['url']
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"🎬 Scraping {category}/{subcategory} (attempt {attempt + 1}/{max_retries + 1})")
                
                # Use the parent class scraping method
                videos_data = self.scrape_single_subcategory(url)
                
                if videos_data:
                    # Save using category_subcategory format for proper folder structure
                    category_name = f"{category}_{subcategory}"
                    self.save_videos_data(videos_data, category_name)
                    
                    logger.info(f"✅ Successfully scraped {len(videos_data)} videos for {category}/{subcategory}")
                    return True
                else:
                    logger.warning(f"⚠️ No videos found for {category}/{subcategory}")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Error scraping {category}/{subcategory} (attempt {attempt + 1}): {e}")
                if attempt < max_retries:
                    logger.info(f"🔄 Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    logger.error(f"💥 Failed to scrape {category}/{subcategory} after {max_retries + 1} attempts")
                    return False
        
        return False
    
    def run_automated_scraping(self, root_dir=".", max_subcategories=None, dry_run=False):
        """Run automated scraping of all missing subcategories"""
        start_time = datetime.now()
        logger.info(f"🚀 Starting automated scraping at {start_time}")
        
        # Find all missing subcategories
        missing_subcategories = self.find_missing_subcategories(root_dir)
        
        if not missing_subcategories:
            logger.info("🎉 No missing subcategories found! All data appears complete.")
            return
        
        # Limit processing if specified
        if max_subcategories:
            missing_subcategories = missing_subcategories[:max_subcategories]
            logger.info(f"📊 Limited to processing {len(missing_subcategories)} subcategories")
        
        if dry_run:
            logger.info("🔍 DRY RUN - Would process the following subcategories:")
            for i, subcat in enumerate(missing_subcategories, 1):
                logger.info(f"  {i}. {subcat['category']}/{subcat['subcategory']} ({subcat['status']}, {subcat['current_count']} videos)")
            return
        
        logger.info(f"📊 Processing {len(missing_subcategories)} missing subcategories...")
        
        # Process each subcategory
        for i, subcategory_info in enumerate(missing_subcategories, 1):
            category = subcategory_info['category']
            subcategory = subcategory_info['subcategory']
            
            logger.info(f"📈 Progress: {i}/{len(missing_subcategories)} - Processing {category}/{subcategory}")
            
            try:
                success = self.scrape_subcategory_with_retry(subcategory_info)
                
                if success:
                    self.processed_count += 1
                    logger.info(f"✅ Completed {category}/{subcategory}")
                else:
                    self.failed_count += 1
                    logger.error(f"❌ Failed {category}/{subcategory}")
                
                # Add delay between subcategories to be respectful
                if i < len(missing_subcategories):
                    logger.info("⏳ Waiting 3 seconds before next subcategory...")
                    time.sleep(3)
                    
            except KeyboardInterrupt:
                logger.info("🛑 Scraping interrupted by user")
                break
            except Exception as e:
                logger.error(f"💥 Unexpected error processing {category}/{subcategory}: {e}")
                self.failed_count += 1
                continue
        
        # Final summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("🏁 Automated scraping completed!")
        logger.info(f"📊 Summary:")
        logger.info(f"  ✅ Successfully processed: {self.processed_count}")
        logger.info(f"  ❌ Failed: {self.failed_count}")
        logger.info(f"  ⏱️ Total time: {duration}")
        logger.info(f"  📈 Success rate: {(self.processed_count / (self.processed_count + self.failed_count) * 100):.1f}%")
        
        # Close driver
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
            logger.info("🔒 Browser closed")

def main():
    """Main function with command line argument support"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated Video Scraper')
    parser.add_argument('--root-dir', default='.', help='Root directory to scan (default: current directory)')
    parser.add_argument('--max-subcategories', type=int, help='Maximum number of subcategories to process')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without actually scraping')
    
    args = parser.parse_args()
    
    scraper = AutomatedVideoScraper()
    scraper.run_automated_scraping(
        root_dir=args.root_dir,
        max_subcategories=args.max_subcategories,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    main()