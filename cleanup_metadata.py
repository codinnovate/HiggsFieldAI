#!/usr/bin/env python3
"""
Cleanup script to remove unwanted fields from metadata.json files
"""

import os
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_metadata_file(metadata_path: Path):
    """Remove unwanted fields from a metadata.json file."""
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        if 'sub_categories' not in metadata:
            logger.warning(f"No sub_categories found in {metadata_path}")
            return False
        
        cleaned_count = 0
        for subcategory in metadata['sub_categories']:
            # Remove unwanted fields
            fields_to_remove = ['valid_urls', 'url_length_stats']
            for field in fields_to_remove:
                if field in subcategory:
                    del subcategory[field]
                    cleaned_count += 1
        
        # Write cleaned metadata back to file
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Cleaned {metadata_path}: removed {cleaned_count} unwanted fields")
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning {metadata_path}: {str(e)}")
        return False

def main():
    """Main function to clean all metadata.json files."""
    root_directory = Path(".")
    
    # Find all metadata.json files
    metadata_files = []
    for root, dirs, files in os.walk(root_directory):
        if 'metadata.json' in files:
            metadata_path = Path(root) / 'metadata.json'
            metadata_files.append(metadata_path)
    
    logger.info(f"Found {len(metadata_files)} metadata.json files")
    
    # Clean each file
    cleaned_count = 0
    for metadata_path in metadata_files:
        if cleanup_metadata_file(metadata_path):
            cleaned_count += 1
    
    logger.info(f"Cleanup completed! Cleaned {cleaned_count} files")

if __name__ == "__main__":
    main()