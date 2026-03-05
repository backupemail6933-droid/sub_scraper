"""
Subscene Scraper - Download Manager
Handles downloading files, progress tracking, and zipping
"""

import os
import zipfile
import requests
import time
from config import DOWNLOAD_DIR, MAX_FILES_BEFORE_ZIP, ZIP_OUTPUT, HEADERS, TIMEOUT


class DownloadManager:
    """Manages downloading and organizing subtitle files"""

    def __init__(self, download_dir=None):
        self.download_dir = download_dir or DOWNLOAD_DIR
        self.downloaded_files = []
        self._ensure_download_dir()

    def _ensure_download_dir(self):
        """Create download directory if it doesn't exist"""
        os.makedirs(self.download_dir, exist_ok=True)

    def _get_filename_from_response(self, response, fallback_name="subtitle"):
        """
        Extract filename from response headers
        Args:
            response: requests Response object
            fallback_name: Fallback filename if none found
        Returns:
            Filename string
        """
        # Try Content-Disposition header
        cd = response.headers.get("Content-Disposition", "")
        if "filename=" in cd:
            # Extract filename from header
            parts = cd.split("filename=")
            if len(parts) > 
