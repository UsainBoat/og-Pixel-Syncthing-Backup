# og-Pixel-Syncthing-Backup

A Python script designed to act as a staging mechanism between an Immich photo library and a Syncthing folder. It selects a batch of images from the source, copies them to the destination for synchronization, and logs the process to ensure files are not re-copied in subsequent runs.

## Features

*   **Staging Workflow**: Wipes the destination folder at the start of each run to prepare for a new batch.
*   **Smart Selection**: Prioritizes the **oldest eligible files** first to catch up on backlog.
*   **History Tracking**: Uses an SQLite database (`backup_log.db`) to remember copied files and prevent duplicates.
*   **Configurable Limits**: Set a maximum storage size per run (e.g., 1GB) to manage bandwidth/storage on the receiving end.
*   **Date Filtering**: Only processes images newer than a specified date.
*   **EXIF Support**: Uses the actual "Date Taken" from image metadata (EXIF) to sort files, falling back to modification time if unavailable.

## Requirements

*   Python 3.x
*   Pillow (for EXIF data extraction)

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Configure**: Copy `config.json.example` to `config.json` and edit the paths.
    ```bash
    cp config.json.example config.json
    nano config.json
    ```
    
    *   `source_directory`: Path to your Immich library (read-only).
    *   `destination_directory`: Path to your Syncthing folder (will be wiped!).
    *   `max_storage_size_mb`: Max size to copy in one run (MB).
    *   `oldest_date`: Date in `YYYY-MM-DD` format. Files older than this are ignored.

2.  **Run**: Execute the script.
    ```bash
    python3 og_pixel_backup.py
    ```

## Logic

1.  Reads configuration.
2.  **Deletes ALL files** in the `destination_directory` (Fresh Start).
3.  Scans `source_directory` for images.
4.  Filters files:
    *   Must be newer than `oldest_date`.
    *   Must **NOT** have been copied before (checked against `backup_log.db`).
5.  Sorts candidates by **EXIF Date (Oldest First)**.
6.  Copies files until `max_storage_size_mb` is reached.
7.  Updates the database with the copied files.
