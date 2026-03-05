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
            if len(parts) > 1:
                filename = parts[1].strip('"').strip("'").strip()
                # Handle UTF-8 encoded filenames
                if "filename*=" in cd:
                    parts2 = cd.split("filename*=")
                    if len(parts2) > 1:
                        filename = parts2[1].split("''")[-1].strip('"').strip()
                return filename

        # Try to get from URL
        url_path = response.url.split("/")[-1].split("?")[0]
        if "." in url_path:
            return url_path

        return f"{fallback_name}.zip"

    def _sanitize_filename(self, filename):
        """Remove invalid characters from filename"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        return filename.strip()

    def download_file(self, url, custom_name=None):
        """
        Download a single file
        Args:
            url: Direct download URL
            custom_name: Optional custom filename
        Returns:
            Path to downloaded file or None
        """
        try:
            session = requests.Session()
            session.headers.update(HEADERS)

            response = session.get(url, timeout=TIMEOUT, stream=True)
            response.raise_for_status()

            # Get filename
            if custom_name:
                filename = self._sanitize_filename(custom_name)
            else:
                filename = self._get_filename_from_response(response)
                filename = self._sanitize_filename(filename)

            # Handle duplicate filenames
            filepath = os.path.join(self.download_dir, filename)
            if os.path.exists(filepath):
                name, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(filepath):
                    filename = f"{name}_{counter}{ext}"
                    filepath = os.path.join(self.download_dir, filename)
                    counter += 1

            # Download with progress
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Simple progress
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r  ⬇️  Downloading: {filename} [{percent:.1f}%]", end="", flush=True)

            print(f"\r  ✅ Downloaded: {filename} ({self._format_size(downloaded)})")

            self.downloaded_files.append(filepath)
            session.close()
            return filepath

        except Exception as e:
            print(f"\n  ❌ Download failed: {e}")
            return None

    def download_multiple(self, download_links, delay=1):
        """
        Download multiple files
        Args:
            download_links: List of (url, name) tuples
            delay: Delay between downloads in seconds
        Returns:
            List of successfully downloaded file paths
        """
        total = len(download_links)
        successful = []

        print(f"\n📦 Starting download of {total} files...")
        print("=" * 50)

        for i, (url, name) in enumerate(download_links, 1):
            print(f"\n[{i}/{total}]", end="")
            filepath = self.download_file(url, name)

            if filepath:
                successful.append(filepath)

            if i < total:
                time.sleep(delay)

        print(f"\n{'=' * 50}")
        print(f"✅ Successfully downloaded: {len(successful)}/{total}")

        return successful

    def zip_files(self, files=None, output_name=None):
        """
        Compress downloaded files into a ZIP archive
        Args:
            files: List of file paths (uses downloaded_files if None)
            output_name: Output ZIP filename
        Returns:
            Path to ZIP file or None
        """
        files = files or self.downloaded_files
        output_name = output_name or ZIP_OUTPUT

        if not files:
            print("  ⚠️ No files to compress!")
            return None

        zip_path = os.path.join(self.download_dir, output_name)

        try:
            print(f"\n🗜️  Compressing {len(files)} files...")

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for filepath in files:
                    if os.path.exists(filepath):
                        arcname = os.path.basename(filepath)
                        zf.write(filepath, arcname)
                        print(f"  📄 Added: {arcname}")

            zip_size = os.path.getsize(zip_path)
            print(f"\n  ✅ ZIP created: {output_name} ({self._format_size(zip_size)})")

            return zip_path

        except Exception as e:
            print(f"  ❌ Compression failed: {e}")
            return None

    def auto_zip_if_needed(self):
        """Automatically zip files if count exceeds threshold"""
        if len(self.downloaded_files) > MAX_FILES_BEFORE_ZIP:
            print(f"\n📢 More than {MAX_FILES_BEFORE_ZIP} files downloaded, auto-compressing...")
            return self.zip_files()
        return None

    def cleanup(self, keep_zip=True):
        """
        Remove individual files after zipping
        Args:
            keep_zip: Whether to keep the ZIP file
        """
        for filepath in self.downloaded_files:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception:
                pass
        self.downloaded_files.clear()
        print("  🧹 Cleanup complete!")

    @staticmethod
    def _format_size(size_bytes):
        """Format bytes to human readable size"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.1f} MB"
        else:
            return f"{size_bytes / (1024 ** 3):.1f} GB"
