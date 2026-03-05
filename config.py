"""
Subscene Scraper - Configuration File
"""

# ✅ Fixed: correct domain
BASE_URL = "https://sub-scene.com"

# ✅ Fixed: correct search endpoint (GET not POST)
SEARCH_URL = f"{BASE_URL}/search"

# Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://sub-scene.com",
    "Connection": "keep-alive",
}

# Download settings
DOWNLOAD_DIR = "/content/subtitles"  # Colab path
MAX_FILES_BEFORE_ZIP = 5
ZIP_OUTPUT = "subtitles.zip"

# Languages
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
DELAY = 1.5
