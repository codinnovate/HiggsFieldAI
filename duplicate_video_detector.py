#!/usr/bin/env python3
"""
Duplicate Video URL Detector

This script scans all video.json and video.csv files in the project directory
and detects duplicate video URLs across all files.
"""

import os
import json
import csv
from collections import defaultdict
from pathlib import Path
import argparse


def find_video_files(root_dir):
    """Find all video.json and video.csv files in the directory tree."""
    video_files = []
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file in ['videos.json', 'video.json']:
                video_files.append({
                    'path': os.path.join(root, file),
                    'type': 'json',
                    'relative_path': os.path.relpath(os.path.join(root, file), root_dir)
                })
            elif file in ['videos.csv', 'video.csv']:
                video_files.append({
                    'path': os.path.join(root, file),
                    'type': 'csv',
                    'relative_path': os.path.relpath(os.path.join(root, file), root_dir)
                })
    
    return video_files


def extract_urls_from_json(file_path):
    """Extract video URLs from JSON file."""
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and 'video_url' in item:
                    urls.append(item['video_url'])
        elif isinstance(data, dict) and 'video_url' in data:
            urls.append(data['video_url'])
            
    except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError) as e:
        print(f"Error reading JSON file {file_path}: {e}")
    
    return urls


def extract_urls_from_csv(file_path):
    """Extract video URLs from CSV file."""
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Try to detect if there's a header
            sample = f.read(1024)
            f.seek(0)
            
            # Check if 'video_url' is in the first line (header)
            has_header = 'video_url' in sample.split('\n')[0].lower()
            
            reader = csv.DictReader(f) if has_header else csv.reader(f)
            
            if has_header:
                for row in reader:
                    # Look for video_url column (case insensitive)
                    for key, value in row.items():
                        if key.lower() == 'video_url' and value.strip():
                            urls.append(value.strip())
            else:
                # If no header, assume video URLs are in the last column
                for row in reader:
                    if row and len(row) > 0:
                        # Take the last non-empty column
                        for col in reversed(row):
                            if col.strip() and 'http' in col:
                                urls.append(col.strip())
                                break
                                
    except (FileNotFoundError, UnicodeDecodeError) as e:
        print(f"Error reading CSV file {file_path}: {e}")
    
    return urls


def detect_duplicates(root_dir='.'):
    """Main function to detect duplicate video URLs within individual files."""
    print(f"Scanning for video files in: {os.path.abspath(root_dir)}")
    print("=" * 60)
    
    # Find all video files
    video_files = find_video_files(root_dir)
    
    if not video_files:
        print("No video.json or video.csv files found!")
        return
    
    print(f"Found {len(video_files)} video files:")
    for file_info in video_files:
        print(f"  - {file_info['relative_path']} ({file_info['type']})")
    
    print("\n" + "=" * 60)
    
    # Check each file for internal duplicates
    files_with_duplicates = {}
    file_url_counts = {}
    total_duplicates = 0
    
    for file_info in video_files:
        file_path = file_info['path']
        file_type = file_info['type']
        relative_path = file_info['relative_path']
        
        if file_type == 'json':
            urls = extract_urls_from_json(file_path)
        else:  # csv
            urls = extract_urls_from_csv(file_path)
        
        file_url_counts[relative_path] = len(urls)
        
        # Count occurrences of each URL within this file
        url_counts = defaultdict(int)
        for url in urls:
            if url:  # Skip empty URLs
                url_counts[url] += 1
        
        # Find duplicates within this file
        file_duplicates = {url: count for url, count in url_counts.items() if count > 1}
        
        if file_duplicates:
            files_with_duplicates[relative_path] = file_duplicates
            total_duplicates += len(file_duplicates)
    
    # Print file statistics
    print("File Statistics:")
    for file_path, count in file_url_counts.items():
        duplicate_count = len(files_with_duplicates.get(file_path, {}))
        status = f" ({duplicate_count} duplicates)" if duplicate_count > 0 else " (no duplicates)"
        print(f"  {file_path}: {count} video URLs{status}")
    
    print("\n" + "=" * 60)
    
    # Report duplicates
    if files_with_duplicates:
        print(f"DUPLICATES FOUND: {total_duplicates} duplicate video URLs in {len(files_with_duplicates)} files")
        print("=" * 60)
        
        file_counter = 1
        for file_path, duplicates in files_with_duplicates.items():
            print(f"\n{file_counter}. File: {file_path}")
            print(f"   Contains {len(duplicates)} duplicate URLs:")
            
            url_counter = 1
            for url, count in duplicates.items():
                print(f"   {url_counter}. URL appears {count} times:")
                print(f"      {url}")
                url_counter += 1
            
            file_counter += 1
        
        # Summary
        print(f"\n" + "=" * 60)
        print("SUMMARY:")
        print(f"Total video files scanned: {len(video_files)}")
        print(f"Files with duplicate URLs: {len(files_with_duplicates)}")
        print(f"Total duplicate URLs found: {total_duplicates}")
        total_duplicate_instances = sum(sum(duplicates.values()) for duplicates in files_with_duplicates.values())
        print(f"Total duplicate instances: {total_duplicate_instances}")
        
    else:
        print("✅ NO DUPLICATES FOUND!")
        print(f"All video URLs are unique within their respective files.")
    
    return files_with_duplicates


def main():
    parser = argparse.ArgumentParser(description='Detect duplicate video URLs within individual video.json and video.csv files')
    parser.add_argument('--dir', '-d', default='.', help='Directory to scan (default: current directory)')
    parser.add_argument('--output', '-o', help='Output results to a file')
    
    args = parser.parse_args()
    
    # Detect duplicates
    files_with_duplicates = detect_duplicates(args.dir)
    
    # Optionally save results to file
    if args.output and files_with_duplicates:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write("Duplicate Video URLs Report (Within Individual Files)\n")
            f.write("=" * 60 + "\n\n")
            
            file_counter = 1
            for file_path, duplicates in files_with_duplicates.items():
                f.write(f"{file_counter}. File: {file_path}\n")
                f.write(f"   Contains {len(duplicates)} duplicate URLs:\n")
                
                url_counter = 1
                for url, count in duplicates.items():
                    f.write(f"   {url_counter}. URL appears {count} times:\n")
                    f.write(f"      {url}\n")
                    url_counter += 1
                
                f.write("\n")
                file_counter += 1
        
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()