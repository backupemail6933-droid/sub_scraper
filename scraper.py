"""
Subscene Scraper - Core Scraping Engine
Handles all HTTP requests and HTML parsing
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from config import BASE_URL, SEARCH_URL, HEADERS, TIMEOUT, MAX_RETRIES, DELAY_BETWEEN_REQUESTS


class SubsceneScraper:
    """Main scraper class for Subscene website"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _make_request(self, url, method="GET", data=None):
        """
        Make HTTP request with retry logic
        Args:
            url: Target URL
            method: GET or POST
            data: POST data if needed
        Returns:
            BeautifulSoup object or None
        """
        for attempt in range(MAX_RETRIES):
            try:
                if method == "POST":
                    response = self.session.post(url, data=data, timeout=TIMEOUT)
                else:
                    response = self.session.get(url, timeout=TIMEOUT)

                response.raise_for_status()
                return BeautifulSoup(response.content, "html.parser")

            except requests.exceptions.RequestException as e:
                print(f"  ⚠️ Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(DELAY_BETWEEN_REQUESTS * (attempt + 1))

        print("  ❌ All attempts failed!")
        return None

    def search(self, query):
        """
        Search for a movie/series on Subscene
        Args:
            query: Search term (movie/series name)
        Returns:
            List of dicts: [{"title": ..., "url": ...}, ...]
        """
        print(f"\n🔍 Searching for: '{query}'...")

        # Subscene search is POST-based
        data = {"query": query}
        soup = self._make_request(SEARCH_URL, method="POST", data=data)

        if not soup:
            return []

        results = []

        # Parse search results
        # Subscene organizes results in categories: Popular, Exact, Close, TV-Series
        search_sections = soup.find_all("div", class_="search-result")

        for section in search_sections:
            # Get all result items
            items = section.find_all("div", class_="title")
            for item in items:
                link = item.find("a")
                if link and link.get("href"):
                    title = link.get_text(strip=True)
                    url = BASE_URL + link["href"]
                    results.append({
                        "title": title,
                        "url": url
                    })

        # Alternative parsing if structure is different
        if not results:
            all_links = soup.select("div.title a, ul li div.title a")
            for link in all_links:
                if link.get("href") and "/subtitles/" in link["href"]:
                    title = link.get_text(strip=True)
                    href = link["href"]
                    if not href.startswith("http"):
                        href = BASE_URL + href
                    results.append({
                        "title": title,
                        "url": href
                    })

        print(f"  ✅ Found {len(results)} results")
        return results

    def get_subtitles(self, page_url, language_filter=None):
        """
        Get all subtitle links from a movie/series page
        Args:
            page_url: URL of the movie/series subtitle page
            language_filter: Filter by language name (e.g., "Arabic")
        Returns:
            List of dicts: [{"language": ..., "title": ..., "url": ..., "author": ...}, ...]
        """
        print(f"\n📄 Fetching subtitles from page...")
        time.sleep(DELAY_BETWEEN_REQUESTS)

        soup = self._make_request(page_url)
        if not soup:
            return []

        subtitles = []

        # Find subtitle table
        table = soup.find("table") or soup.find("tbody")

        if table:
            rows = table.find_all("tr")
            for row in rows:
                try:
                    # Get the main link cell
                    cells = row.find_all("td")
                    if len(cells) < 1:
                        continue

                    link_cell = cells[0]
                    link = link_cell.find("a")

                    if not link or not link.get("href"):
                        continue

                    # Extract language and title
                    spans = link.find_all("span")
                    if len(spans) >= 2:
                        language = spans[0].get_text(strip=True)
                        title = spans[1].get_text(strip=True)
                    elif len(spans) == 1:
                        language = spans[0].get_text(strip=True)
                        title = link.get_text(strip=True)
                    else:
                        language = "Unknown"
                        title = link.get_text(strip=True)

                    # Filter by language if specified
                    if language_filter and language_filter.lower() not in language.lower():
                        continue

                    # Get author if available
                    author = ""
                    if len(cells) > 1:
                        author_cell = cells[1] if len(cells) > 1 else None
                        if author_cell:
                            author = author_cell.get_text(strip=True)

                    # Build URL
                    sub_url = link["href"]
                    if not sub_url.startswith("http"):
                        sub_url = BASE_URL + sub_url

                    subtitles.append({
                        "language": language,
                        "title": title,
                        "url": sub_url,
                        "author": author
                    })

                except Exception as e:
                    continue

        print(f"  ✅ Found {len(subtitles)} subtitles")
        return subtitles

    def get_download_link(self, subtitle_page_url):
        """
        Extract the actual download link from a subtitle's page
        Args:
            subtitle_page_url: URL of the individual subtitle page
        Returns:
            Direct download URL string or None
        """
        time.sleep(DELAY_BETWEEN_REQUESTS)

        soup = self._make_request(subtitle_page_url)
        if not soup:
            return None

        # Find download button/link
        download_btn = soup.find("a", id="downloadButton")
        if not download_btn:
            download_btn = soup.find("a", {"id": "downloadButton"})
        if not download_btn:
            download_btn = soup.select_one("a.download, #downloadButton, a[href*='subtitle/download']")
        if not download_btn:
            # Try to find any download link
            all_links = soup.find_all("a")
            for link in all_links:
                href = link.get("href", "")
                if "download" in href.lower():
                    download_btn = link
                    break

        if download_btn and download_btn.get("href"):
            download_url = download_btn["href"]
            if not download_url.startswith("http"):
                download_url = BASE_URL + download_url
            return download_url

        return None

    def close(self):
        """Close the session"""
        self.session.close()
