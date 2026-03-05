"""
Subscene Scraper - Core Engine (Fixed for sub-scene.com)
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin, quote_plus
from config import BASE_URL, SEARCH_URL, HEADERS, TIMEOUT, MAX_RETRIES, DELAY


class SubsceneScraper:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        print("✅ Scraper initialized!")

    def _request(self, url, method="GET", data=None, params=None):
        """Make HTTP request with retries"""
        for attempt in range(MAX_RETRIES):
            try:
                if method == "POST":
                    resp = self.session.post(url, data=data, timeout=TIMEOUT)
                else:
                    resp = self.session.get(url, params=params, timeout=TIMEOUT)

                resp.raise_for_status()
                return BeautifulSoup(resp.content, "html.parser")

            except requests.exceptions.RequestException as e:
                print(f"  ⚠️ Attempt {attempt+1}/{MAX_RETRIES}: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(DELAY * (attempt + 1))
        return None

    def search(self, query):
        """
        Search for movie/series
        Supports: movie name OR IMDb ID (tt1234567)
        URL format: https://sub-scene.com/search?query=xxx
        """
        print(f"\n🔍 Searching: '{query}'...")

        # ✅ Fixed: GET request with query parameter
        params = {"query": query}
        soup = self._request(SEARCH_URL, method="GET", params=params)

        if not soup:
            print("  ❌ Search failed!")
            return []

        results = []
        seen = set()

        # ============================================
        # Method 1: Find all links containing /subtitles/
        # ============================================
        for link in soup.find_all("a", href=True):
            href = link["href"]

            # Filter subtitle-related links
            if "/subtitles/" in href or "/subtitle/" in href:
                title = link.get_text(strip=True)

                # Skip empty or very short titles
                if not title or len(title) < 2:
                    continue

                # Skip navigation/filter links
                skip_words = ["search", "login", "register", "filter", "sort", "page"]
                if any(w in href.lower() for w in skip_words):
                    continue

                full_url = urljoin(BASE_URL, href)

                if full_url not in seen:
                    seen.add(full_url)
                    results.append({
                        "title": title,
                        "url": full_url
                    })

        # ============================================
        # Method 2: Try finding in div/li structures
        # ============================================
        if not results:
            # Look for common structures
            for container in soup.find_all(["div", "li", "tr"]):
                link = container.find("a", href=True)
                if not link:
                    continue

                href = link["href"]
                if "/subtitles/" not in href and "/subtitle/" not in href:
                    continue

                title = link.get_text(strip=True)
                if not title or len(title) < 2:
                    # Try getting text from parent
                    title = container.get_text(strip=True)[:100]

                if title:
                    full_url = urljoin(BASE_URL, href)
                    if full_url not in seen:
                        seen.add(full_url)
                        results.append({
                            "title": title,
                            "url": full_url
                        })

        # ============================================
        # Method 3: Check if redirected to subtitle page directly
        # ============================================
        if not results:
            # Sometimes searching by IMDB ID redirects directly
            page_title = soup.find("title")
            if page_title:
                pt = page_title.get_text(strip=True)
                if pt and "search" not in pt.lower():
                    # We might be on the subtitle page already
                    results.append({
                        "title": pt,
                        "url": SEARCH_URL + "?query=" + quote_plus(query)
                    })

        print(f"  ✅ Found {len(results)} results")
        return results

    def get_subtitles(self, page_url, lang_filter=None):
        """Get all subtitles from a movie/series page"""
        print(f"\n📄 Loading subtitles...")
        time.sleep(DELAY)

        soup = self._request(page_url)
        if not soup:
            return []

        subtitles = []

        # ============================================
        # Method 1: Table-based layout (traditional subscene)
        # ============================================
        table = soup.find("table") or soup.find("tbody")
        if table:
            rows = table.find_all("tr") if table.name == "table" else table.find_all("tr")
            for row in rows:
                sub = self._parse_subtitle_row(row, lang_filter)
                if sub:
                    subtitles.append(sub)

        # ============================================
        # Method 2: Div-based layout
        # ============================================
        if not subtitles:
            # Try finding subtitle items in divs
            sub_containers = soup.find_all("div", class_=re.compile(r"subtitle|sub-item|result", re.I))
            if not sub_containers:
                sub_containers = soup.find_all("a", href=re.compile(r"/subtitles/.*/.*/"))

            for container in sub_containers:
                sub = self._parse_subtitle_div(container, lang_filter)
                if sub:
                    subtitles.append(sub)

        # ============================================
        # Method 3: Generic link search
        # ============================================
        if not subtitles:
            for link in soup.find_all("a", href=True):
                href = link["href"]
                # Subtitle detail pages usually have deeper paths
                if "/subtitles/" in href and href.count("/") >= 3:
                    text = link.get_text(strip=True)
                    if text and len(text) > 3:
                        # Try to extract language
                        language = "Unknown"
                        spans = link.find_all("span")
                        if spans:
                            language = spans[0].get_text(strip=True)
                            if len(spans) >= 2:
                                text = spans[1].get_text(strip=True)

                        if lang_filter and lang_filter.lower() not in language.lower():
                            continue

                        full_url = urljoin(BASE_URL, href)
                        subtitles.append({
                            "language": language,
                            "title": text,
                            "url": full_url,
                            "author": ""
                        })

        print(f"  ✅ Found {len(subtitles)} subtitles")
        return subtitles

    def _parse_subtitle_row(self, row, lang_filter=None):
        """Parse a table row to extract subtitle info"""
        try:
            link = row.find("a", href=True)
            if not link:
                return None

            href = link["href"]
            if "/subtitles/" not in href and "/subtitle/" not in href:
                return None

            # Extract language and title from spans
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

            # Clean up
            language = language.strip()
            title = title.strip()

            if not title:
                return None

            # Language filter
            if lang_filter and lang_filter.lower() not in language.lower():
                return None

            # Author
            author = ""
            cells = row.find_all("td")
            for cell in cells[1:]:
                text = cell.get_text(strip=True)
                if text and text != language and text != title:
                    author = text
                    break

            return {
                "language": language,
                "title": title,
                "url": urljoin(BASE_URL, href),
                "author": author
            }
        except Exception:
            return None

    def _parse_subtitle_div(self, container, lang_filter=None):
        """Parse a div container to extract subtitle info"""
        try:
            if container.name == "a":
                link = container
            else:
                link = container.find("a", href=True)

            if not link:
                return None

            href = link.get("href", "")
            if "/subtitles/" not in href and "/subtitle/" not in href:
                return None

            # Try to get language
            language = "Unknown"
            lang_elem = container.find(class_=re.compile(r"lang|language", re.I))
            if lang_elem:
                language = lang_elem.get_text(strip=True)
            else:
                spans = link.find_all("span")
                if spans:
                    language = spans[0].get_text(strip=True)

            title = link.get_text(strip=True)
            if not title:
                return None

            if lang_filter and lang_filter.lower() not in language.lower():
                return None

            return {
                "language": language,
                "title": title,
                "url": urljoin(BASE_URL, href),
                "author": ""
            }
        except Exception:
            return None

    def get_download_link(self, sub_page_url):
        """Extract download link from subtitle page"""
        time.sleep(DELAY)
        soup = self._request(sub_page_url)
        if not soup:
            return None

        # ✅ Try multiple methods to find download button
        # Method 1: ID-based
        for id_name in ["downloadButton", "download-button", "btn-download"]:
            btn = soup.find("a", id=id_name)
            if btn and btn.get("href"):
                return urljoin(BASE_URL, btn["href"])

        # Method 2: Class-based
        for class_name in ["download", "btn-download", "download-btn"]:
            btn = soup.find("a", class_=class_name)
            if btn and btn.get("href"):
                return urljoin(BASE_URL, btn["href"])

        # Method 3: Text-based
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True).lower()
            href = link["href"].lower()
            if "download" in text or "download" in href:
                if "javascript" not in href:
                    return urljoin(BASE_URL, link["href"])

        # Method 4: Button element
        btn = soup.find("button", onclick=True)
        if btn:
            onclick = btn.get("onclick", "")
            urls = re.findall(r"['\"]([^'\"]*download[^'\"]*)['\"]", onclick)
            if urls:
                return urljoin(BASE_URL, urls[0])

        return None

    def close(self):
        self.session.close()
        print("✅ Session closed")
