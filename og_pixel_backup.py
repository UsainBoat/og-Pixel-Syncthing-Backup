import os
import json
import shutil
import logging
from datetime import datetime
import glob

# Local imports
from db_manager import DBManager
from image_utils import get_date_taken

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backup.log"),
        logging.StreamHandler()
    ]
)

def load_config():
    config_path = 'config.json'
    if not os.path.exists(config_path):
        logging.error(f"Config file {config_path} not found. Please create one from config.json.example")
        return None
    
    with open(config_path, 'r') as f:
        return json.load(f)

def clean_destination(destination_dir):
    """Deletes all files in the destination directory."""
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
        return

    logging.info(f"Cleaning destination directory: {destination_dir}")
    for filename in os.listdir(destination_dir):
        file_path = os.path.join(destination_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logging.error(f"Failed to delete {file_path}. Reason: {e}")

def main():
    config = load_config()
    if not config:
        return

    source_dir = config['source_directory']
    dest_dir = config['destination_directory']
    db_file = config['database_file']
    max_size_mb = config.get('max_storage_size_mb', 1024)
    oldest_date_str = config.get('oldest_date', '1970-01-01')

    try:
        oldest_date = datetime.strptime(oldest_date_str, "%Y-%m-%d")
    except ValueError:
        logging.error(f"Invalid date format for oldest_date: {oldest_date_str}. Use YYYY-MM-DD.")
        return

    # Initialize Database
    db = DBManager(db_file)

    # 1. Clean Destination (Fresh Start)
    clean_destination(dest_dir)

    # 2. Scan & Filter Files
    logging.info(f"Scanning source directory: {source_dir}")
    candidates = []
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.heic', '.dng', '.raw', '.webp'}

    for root, _, files in os.walk(source_dir):
        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            
            if ext not in image_extensions:
                continue
            
            # Check if already copied
            if db.is_copied(file_path):
                continue
            
            # Check date
            date_taken = get_date_taken(file_path)
            if date_taken < oldest_date:
                continue
            
            candidates.append({
                'path': file_path,
                'date': date_taken,
                'size': os.path.getsize(file_path)
            })

    # 3. Sort by Date (Oldest First)
    candidates.sort(key=lambda x: x['date'])
    logging.info(f"Found {len(candidates)} eligible files.")

    # 4. Copy Batch
    current_size = 0
    max_size_bytes = max_size_mb * 1024 * 1024
    copied_count = 0

    for candidate in candidates:
        if current_size + candidate['size'] > max_size_bytes:
            logging.info("Max storage size reached. Stopping batch.")
            break
        
        src_path = candidate['path']
        filename = os.path.basename(src_path)
        dest_path = os.path.join(dest_dir, filename)
        
        # Handle filename collisions in destination (e.g., IMG_001.JPG from two different subfolders)
        base, extension = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(dest_dir, f"{base}_{counter}{extension}")
            counter += 1

        try:
            shutil.copy2(src_path, dest_path)
            db.log_copy(src_path)
            current_size += candidate['size']
            copied_count += 1
            logging.info(f"Copied: {filename} ({candidate['size'] / 1024 / 1024:.2f} MB)")
        except Exception as e:
            logging.error(f"Error copying {src_path}: {e}")

    logging.info(f"Batch complete. Copied {copied_count} files totaling {current_size / 1024 / 1024:.2f} MB.")
    db.close()

if __name__ == "__main__":
    main()
