# Video Processing Scripts

This repository contains two Python scripts for managing video content across different categories and subcategories.

## Scripts Overview

### 1. remove_duplicates.py
**Purpose**: Remove duplicate video URLs from videos.json files across all categories and subcategories.

**Key Features**:
- Scans all directories recursively for videos.json files
- Identifies and removes duplicate video URLs within each file
- Preserves the first occurrence of each unique URL
- Creates backups before making changes
- Provides detailed logging and statistics
- Safe operation with rollback capability

**Usage**:
```bash
python3 remove_duplicates.py [--root-dir PATH] [--dry-run] [--backup]
```

**Options**:
- `--root-dir PATH`: Specify root directory (default: current directory)
- `--dry-run`: Show what would be changed without making actual changes
- `--backup`: Create backup files before making changes

**Example Output**:
```
Found 360 videos.json files
Processing: ./UGC/Angry Mode/videos.json
  - Found 5 duplicates, kept 15 unique videos
  - Backup created: ./UGC/Angry Mode/videos.json.backup
Total duplicates removed: 127 across 45 files
```

### 2. download_empty_categories.py
**Purpose**: Identify missing or empty subcategories and scrape content for them using the existing scraper.

**Key Features**:
- Compares existing folder structure with metadata.json files
- Identifies missing subcategory folders
- Finds subcategories without videos.json files
- Detects empty or corrupted videos.json files
- Uses the SimpleVideoScraper to scrape missing content
- Interactive selection of subcategories to process
- Automatic mode for batch processing
- Dry-run mode for preview

**Usage**:
```bash
python3 download_empty_categories.py [--root-dir PATH] [--auto] [--dry-run]
```

**Options**:
- `--root-dir PATH`: Specify root directory (default: current directory)
- `--auto`: Automatically scrape all missing subcategories without prompting
- `--dry-run`: Show what would be scraped without actually scraping

**Example Output**:
```
📊 Summary:
  Total missing/empty subcategories: 233
  - Missing folders: 180
  - Missing videos.json: 35
  - Empty videos.json: 15
  - Corrupted videos.json: 3

🔍 Dry run - subcategories that would be scraped:
  - Kling 2.1 Master/Saint Glow (folder_missing)
  - Camera Controls/Eating Zoom (folder_missing)
  - UGC/Beach Vibes (no_videos_json)
```

**Interactive Mode**:
```
Select subcategories to scrape:
- Enter numbers (e.g., 1,3,5-8): 1-5,10
- Enter 'all' to select all subcategories
- Enter 'q' to quit

🚀 Starting to scrape 6 subcategories...
[1/6] Scraping Kling 2.1 Master/Saint Glow...
  ✅ Success
```

## Requirements

Both scripts require:
- Python 3.6+
- Access to the existing `simple_scraper.py` (for download_empty_categories.py)
- Read/write permissions in the project directory

## Safety Features

### remove_duplicates.py:
- Creates backup logs before making changes
- Only modifies files with actual duplicates
- Preserves placeholder and empty URLs
- Detailed error handling and reporting

### download_empty_categories.py:
- Interactive confirmation before downloading
- 30-minute timeout per category to prevent hanging
- Detailed logging of success/failure for each category
- Uses the existing scraper infrastructure

## Logs

Both scripts create detailed log files:
- `remove_duplicates.log` - Duplicate removal operations
- `download_empty_categories.log` - Download operations

These logs include timestamps, operation details, and any errors encountered.

## Tips

1. **Before running remove_duplicates.py**: Consider backing up your `videos.json` files
2. **For download_empty_categories.py**: Make sure your scraper is working properly first
3. **Check logs**: Both scripts provide detailed logs for troubleshooting
4. **Run periodically**: Use `remove_duplicates.py` after scraping sessions to keep data clean