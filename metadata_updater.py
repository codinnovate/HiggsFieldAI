#!/usr/bin/env python3
"""
Metadata Updater Script

This script traverses all directories, finds videos.json files, 
extracts video count and URL length information, and updates 
the corresponding metadata.json files with this information.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('metadata_updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MetadataUpdater:
    """Class to handle metadata updates for video collections."""
    
    def __init__(self, root_directory: str = "."):
        """
        Initialize the MetadataUpdater.
        
        Args:
            root_directory: The root directory to start scanning from
        """
        self.root_directory = Path(root_directory).resolve()
        self.video_data = {}
        self.updated_categories = []
        
    def find_videos_json_files(self) -> List[Path]:
        """
        Find all videos.json files in the directory structure.
        
        Returns:
            List of Path objects pointing to videos.json files
        """
        videos_json_files = []
        
        for root, dirs, files in os.walk(self.root_directory):
            if 'videos.json' in files:
                videos_json_path = Path(root) / 'videos.json'
                videos_json_files.append(videos_json_path)
                logger.info(f"Found videos.json: {videos_json_path}")
        
        logger.info(f"Total videos.json files found: {len(videos_json_files)}")
        return videos_json_files
    
    def analyze_videos_json(self, videos_json_path: Path) -> Dict[str, Any]:
        """
        Analyze a videos.json file and extract relevant information.
        
        Args:
            videos_json_path: Path to the videos.json file
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            with open(videos_json_path, 'r', encoding='utf-8') as f:
                videos_data = json.load(f)
            
            if not isinstance(videos_data, list):
                logger.warning(f"Unexpected format in {videos_json_path}: not a list")
                return {}
            
            video_count = len(videos_data)
            url_lengths = []
            valid_urls = 0
            
            for video in videos_data:
                if isinstance(video, dict) and 'video_url' in video:
                    url = video['video_url']
                    if url and isinstance(url, str):
                        url_lengths.append(len(url))
                        valid_urls += 1
            
            analysis = {
                'video_count': video_count,
                'subcategory_path': videos_json_path.parent.name,
                'category_path': videos_json_path.parent.parent.name
            }
            
            logger.info(f"Analyzed {videos_json_path}: {video_count} videos, {valid_urls} valid URLs")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing {videos_json_path}: {str(e)}")
            return {}
    
    def find_metadata_json(self, category_path: Path) -> Optional[Path]:
        """
        Find the metadata.json file for a given category.
        
        Args:
            category_path: Path to the category directory
            
        Returns:
            Path to metadata.json if found, None otherwise
        """
        metadata_path = category_path / 'metadata.json'
        if metadata_path.exists():
            return metadata_path
        return None
    
    def update_metadata_json(self, metadata_path: Path, video_analyses: List[Dict[str, Any]]) -> bool:
        """
        Update a metadata.json file with video count information.
        
        Args:
            metadata_path: Path to the metadata.json file
            video_analyses: List of video analysis results for this category
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Read existing metadata
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            if 'sub_categories' not in metadata:
                logger.warning(f"No sub_categories found in {metadata_path}")
                return False
            
            # Create a mapping of subcategory names to video data
            video_data_map = {}
            for analysis in video_analyses:
                subcategory_name = analysis['subcategory_path']
                video_data_map[subcategory_name] = analysis
            
            # Update each subcategory with video count
            updated_count = 0
            for subcategory in metadata['sub_categories']:
                subcategory_name = subcategory['name']
                
                # Try to find matching video data (handle name variations)
                matching_data = None
                for key, data in video_data_map.items():
                    if key == subcategory_name or key.replace(' ', '') == subcategory_name.replace(' ', ''):
                        matching_data = data
                        break
                
                if matching_data:
                    subcategory['video_count'] = matching_data['video_count']
                    updated_count += 1
                    logger.info(f"Updated {subcategory_name}: {matching_data['video_count']} videos")
                else:
                    # Set default values if no video data found
                    subcategory['video_count'] = 0
                    logger.warning(f"No video data found for subcategory: {subcategory_name}")
            
            # Write updated metadata back to file
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Updated {metadata_path}: {updated_count} subcategories updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating {metadata_path}: {str(e)}")
            return False
    
    def run(self) -> Dict[str, Any]:
        """
        Run the complete metadata update process.
        
        Returns:
            Summary of the update process
        """
        logger.info("Starting metadata update process...")
        
        # Find all videos.json files
        videos_json_files = self.find_videos_json_files()
        
        if not videos_json_files:
            logger.warning("No videos.json files found!")
            return {'status': 'no_files_found'}
        
        # Analyze all videos.json files
        all_analyses = []
        for videos_json_path in videos_json_files:
            analysis = self.analyze_videos_json(videos_json_path)
            if analysis:
                all_analyses.append(analysis)
        
        # Group analyses by category
        category_analyses = {}
        for analysis in all_analyses:
            category = analysis['category_path']
            if category not in category_analyses:
                category_analyses[category] = []
            category_analyses[category].append(analysis)
        
        # Update metadata.json files
        updated_categories = []
        failed_categories = []
        
        for category, analyses in category_analyses.items():
            category_path = self.root_directory / category
            metadata_path = self.find_metadata_json(category_path)
            
            if metadata_path:
                if self.update_metadata_json(metadata_path, analyses):
                    updated_categories.append(category)
                else:
                    failed_categories.append(category)
            else:
                logger.warning(f"No metadata.json found for category: {category}")
                failed_categories.append(category)
        
        # Generate summary
        summary = {
            'status': 'completed',
            'total_videos_json_files': len(videos_json_files),
            'total_video_analyses': len(all_analyses),
            'categories_found': len(category_analyses),
            'categories_updated': len(updated_categories),
            'categories_failed': len(failed_categories),
            'updated_categories': updated_categories,
            'failed_categories': failed_categories
        }
        
        logger.info("Metadata update process completed!")
        logger.info(f"Summary: {summary}")
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """
        Print a formatted summary of the update process.
        
        Args:
            summary: Summary dictionary from run() method
        """
        print("\n" + "="*60)
        print("METADATA UPDATE SUMMARY")
        print("="*60)
        print(f"Status: {summary['status']}")
        print(f"Videos.json files found: {summary.get('total_videos_json_files', 0)}")
        print(f"Video analyses completed: {summary.get('total_video_analyses', 0)}")
        print(f"Categories found: {summary.get('categories_found', 0)}")
        print(f"Categories updated: {summary.get('categories_updated', 0)}")
        print(f"Categories failed: {summary.get('categories_failed', 0)}")
        
        if summary.get('updated_categories'):
            print(f"\nUpdated categories:")
            for category in summary['updated_categories']:
                print(f"  ✓ {category}")
        
        if summary.get('failed_categories'):
            print(f"\nFailed categories:")
            for category in summary['failed_categories']:
                print(f"  ✗ {category}")
        
        print("="*60)


def main():
    """Main function to run the metadata updater."""
    updater = MetadataUpdater()
    summary = updater.run()
    updater.print_summary(summary)


if __name__ == "__main__":
    main()