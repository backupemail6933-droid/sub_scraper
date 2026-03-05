"""
Subscene Scraper - Configuration File
All settings and constants go here
"""

# Base URL
BASE_URL = "https://sub-scene.com"

# Search URL
SEARCH_URL = f"{BASE_URL}/search?query=a"

# Headers to mimic browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://subscene.com",
    "Connection": "keep-alive",
}

# Download settings
DOWNLOAD_DIR = "downloads"
MAX_FILES_BEFORE_ZIP = 5  # لو أكتر من 5 ملفات هيضغطهم
ZIP_OUTPUT = "subtitles.zip"

# Supported languages
LANGUAGES = {
    "1": "Arabic",
    "2": "English",
    "3": "French",
    "4": "Spanish",
    "5": "German",
    "6": "Turkish",
    "7": "Italian",
    "8": "Portuguese",
}

# Request settings
TIMEOUT = 30
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 1  # seconds - عشان ما نتبلوكش
