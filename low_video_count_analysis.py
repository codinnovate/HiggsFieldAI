#!/usr/bin/env python3
"""
Script to analyze metadata.json files and extract categories/subcategories with 0 or 1 video counts
"""

import os
import json
from pathlib import Path

def analyze_low_video_counts():
    """Analyze all metadata.json files and find subcategories with 0 or 1 video counts."""
    root_directory = Path(".")
    results = {}
    
    # Find all metadata.json files
    for root, dirs, files in os.walk(root_directory):
        if 'metadata.json' in files:
            metadata_path = Path(root) / 'metadata.json'
            
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                category_name = metadata.get('category_name', 'Unknown')
                sub_categories = metadata.get('sub_categories', [])
                
                # Filter subcategories with 0 or 1 video counts
                low_count_subcategories = []
                for subcategory in sub_categories:
                    video_count = subcategory.get('video_count', 0)
                    if video_count <= 1:
                        low_count_subcategories.append({
                            'name': subcategory.get('name', 'Unknown'),
                            'video_count': video_count,
                            'link': subcategory.get('link', '')
                        })
                
                if low_count_subcategories:
                    results[category_name] = {
                        'total_subcategories': len(sub_categories),
                        'low_count_subcategories': low_count_subcategories,
                        'low_count_total': len(low_count_subcategories)
                    }
                    
            except Exception as e:
                print(f"Error processing {metadata_path}: {str(e)}")
    
    return results

def save_results_to_file(results):
    """Save the analysis results to a text file."""
    output_file = "low_video_count_categories.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("CATEGORIES AND SUBCATEGORIES WITH 0 OR 1 VIDEO COUNTS\n")
        f.write("=" * 60 + "\n\n")
        
        total_low_count = 0
        total_categories = len(results)
        
        for category_name, data in results.items():
            f.write(f"CATEGORY: {category_name}\n")
            f.write(f"Total subcategories: {data['total_subcategories']}\n")
            f.write(f"Low count subcategories: {data['low_count_total']}\n")
            f.write("-" * 40 + "\n")
            
            for subcategory in data['low_count_subcategories']:
                f.write(f"  • {subcategory['name']} (Count: {subcategory['video_count']})\n")
                total_low_count += 1
            
            f.write("\n")
        
        f.write("SUMMARY\n")
        f.write("=" * 20 + "\n")
        f.write(f"Total categories analyzed: {total_categories}\n")
        f.write(f"Categories with low count subcategories: {len(results)}\n")
        f.write(f"Total subcategories with 0 or 1 videos: {total_low_count}\n")
    
    return output_file

def main():
    """Main function to run the analysis."""
    print("Analyzing metadata files for low video counts...")
    results = analyze_low_video_counts()
    
    if results:
        output_file = save_results_to_file(results)
        print(f"Analysis complete! Results saved to: {output_file}")
        
        # Print summary to console
        total_low_count = sum(data['low_count_total'] for data in results.values())
        print(f"\nSummary:")
        print(f"- Categories with low count subcategories: {len(results)}")
        print(f"- Total subcategories with 0 or 1 videos: {total_low_count}")
    else:
        print("No categories found with subcategories having 0 or 1 video counts.")

if __name__ == "__main__":
    main()