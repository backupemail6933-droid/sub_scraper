"""
Subscene Scraper - Google Colab Runner
Run this file directly in Google Colab
"""

# Install dependencies
import subprocess
subprocess.check_call(["pip", "install", "-q", "requests", "beautifulsoup4"])

print("✅ Dependencies installed!")
print("=" * 50)

# Now import and run
from main import main
main()
