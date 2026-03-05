"""
Subscene Scraper - Download Manager
"""

import os
import re
import time
import zipfile
import requests
from config import DOWNLOAD_DIR, MAX_FILES_BEFORE_ZIP, ZIP_OUTPUT, HEADERS, TIMEOUT, DELAY


class DownloadManager:

    def __init__(self):
        self.download_dir = DOWNLOAD_DIR
        self.files = []
        os.makedirs(self.download_dir, exist_ok=True)
        print(f"📁 Download dir: {self.download_dir}")

    def _size(self, b):
        if b < 1024: return f"{b} B"
        if b < 1024**2: return f"{b/1024:.1f} KB"
        return f"{b/1024**2:.1f} MB"

    def _clean_name(self, name):
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
        name = re.sub(r'_+', '_', name)
        return name.strip('_. ')[:200]

    def download(self, url, name=None):
        """Download single file"""
        try:
            session = requests.Session()
            session.headers.update(HEADERS)
            resp = session.get(url, timeout=TIMEOUT, stream=True, allow_redirects=True)
            resp.raise_for_status()

            # Determine filename
            filename = None

            # From Content-Disposition
            cd = resp.headers.get("Content-Disposition", "")
            if "filename" in cd:
                match = re.findall(r'filename[*]?=(?:UTF-8\'\')?["\']?([^"\';\n]+)', cd, re.I)
                if match:
                    filename = match[0]

            # From custom name
            if not filename and name:
                filename = self._clean_name(name) + ".zip"

            # Fallback
            if not filename:
                filename = url.split("/")[-1].split("?")[0] or "subtitle.zip"

            filename = self._clean_name(filename)
            if not filename:
                filename = "subtitle.zip"

            # Ensure extension
            if "." not in filename:
                filename += ".zip"

            filepath = os.path.join(self.download_dir, filename)

            # Handle duplicates
            if os.path.exists(filepath):
                base, ext = os.path.splitext(filename)
                i = 1
                while os.path.exists(filepath):
                    filepath = os.path.join(self.download_dir, f"{base}_{i}{ext}")
                    i += 1

            # Write file
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

            actual_size = os.path.getsize(filepath)

            # Verify file is not empty
            if actual_size == 0:
                os.remove(filepath)
                print(f"❌ Empty file removed")
                return None

            print(f"✅ {os.path.basename(filepath)} ({self._size(actual_size)})")
            self.files.append(filepath)
            session.close()
            return filepath

        except Exception as e:
            print(f"❌ Failed: {e}")
            return None

    def download_batch(self, links):
        """Download multiple files"""
        total = len(links)
        success = []
        print(f"\n📦 Downloading {total} files...")
        print("─" * 50)

        for i, (url, name) in enumerate(links, 1):
            print(f"  [{i}/{total}] ", end="")
            result = self.download(url, name)
            if result:
                success.append(result)
            if i < total:
                time.sleep(DELAY)

        print("─" * 50)
        print(f"📊 Result: {len(success)}/{total} successful")
        return success

    def make_zip(self, output=None):
        """Compress all files into ZIP"""
        output = output or ZIP_OUTPUT
        if not self.files:
            print("  ⚠️ No files to zip!")
            return None

        zip_path = os.path.join(self.download_dir, output)
        print(f"\n🗜️ Creating ZIP: {output}")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in self.files:
                if os.path.exists(f):
                    zf.write(f, os.path.basename(f))
                    print(f"  📄 + {os.path.basename(f)}")

        size = os.path.getsize(zip_path)
        print(f"  ✅ ZIP ready! ({self._size(size)})")
        return zip_path

    def auto_zip(self):
        """Auto-zip if file count exceeds limit"""
        if len(self.files) > MAX_FILES_BEFORE_ZIP:
            print(f"\n📢 {len(self.files)} files > limit ({MAX_FILES_BEFORE_ZIP})")
            return self.make_zip()
        return None

    def show_files(self):
        """Display downloaded files"""
        if not os.path.exists(self.download_dir):
            return
        files = os.listdir(self.download_dir)
        if not files:
            return
        print(f"\n📂 Downloaded Files ({len(files)}):")
        print("─" * 40)
        for f in sorted(files):
            fp = os.path.join(self.download_dir, f)
            size = os.path.getsize(fp)
            print(f"  📄 {f} ({self._size(size)})")
        print("─" * 40)

    def cleanup(self, keep_zip=True):
        """Remove individual files, optionally keep ZIP"""
        removed = 0
        for f in self.files:
            if os.path.exists(f):
                if keep_zip and f.endswith('.zip') and ZIP_OUTPUT in f:
                    continue
                os.remove(f)
                removed += 1
        self.files.clear()
        print(f"  🧹 Removed {removed} files")
