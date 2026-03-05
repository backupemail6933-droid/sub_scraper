"""
Subscene Scraper - Main Entry Point
Interactive CLI for searching and downloading subtitles
"""

from scraper import SubsceneScraper
from downloader import DownloadManager
from config import LANGUAGES
import sys


def display_banner():
    """Show application banner"""
    print("""
╔══════════════════════════════════════════════════╗
║          🎬 Subscene Subtitle Scraper 🎬         ║
║              v1.0 - Made with Python             ║
╚══════════════════════════════════════════════════╝
    """)


def select_from_list(items, display_key, prompt="Select"):
    """
    Display numbered list and get user selection
    Args:
        items: List of items
        display_key: Key to display (for dicts) or None (for strings)
        prompt: Selection prompt text
    Returns:
        Selected item or None
    """
    if not items:
        print("  ⚠️ No items to display!")
        return None

    print()
    for i, item in enumerate(items, 1):
        if isinstance(item, dict):
            print(f"  [{i}] {item.get(display_key, 'Unknown')}")
        else:
            print(f"  [{i}] {item}")

    print(f"  [0] Cancel")

    while True:
        try:
            choice = input(f"\n  {prompt} (number): ").strip()
            if choice == "0":
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                return items[idx]
            print("  ⚠️ Invalid number, try again!")
        except ValueError:
            print("  ⚠️ Please enter a number!")


def select_language():
    """Let user select subtitle language"""
    print("\n🌍 Available Languages:")
    for key, lang in LANGUAGES.items():
        print(f"  [{key}] {lang}")
    print("  [0] All Languages")

    choice = input("\n  Select language: ").strip()
    return LANGUAGES.get(choice, None)


def multi_select_from_list(items, display_key):
    """
    Let user select multiple items
    Args:
        items: List of items
        display_key: Key to display
    Returns:
        List of selected items
    """
    if not items:
        print("  ⚠️ No items to display!")
        return []

    print()
    for i, item in enumerate(items, 1):
        if isinstance(item, dict):
            lang = item.get("language", "")
            title = item.get("title", "")
            print(f"  [{i}] [{lang}] {title}")
        else:
            print(f"  [{i}] {item}")

    print(f"\n  [a] Select ALL")
    print(f"  [0] Cancel")

    choice = input(f"\n  Select (comma-separated, e.g., 1,3,5): ").strip()

    if choice == "0":
        return []
    if choice.lower() == "a":
        return items

    selected = []
    try:
        indices = [int(x.strip()) - 1 for x in choice.split(",")]
        for idx in indices:
            if 0 <= idx < len(items):
                selected.append(items[idx])
    except ValueError:
        print("  ⚠️ Invalid input!")

    return selected


def main():
    """Main application flow"""
    display_banner()

    scraper = SubsceneScraper()
    downloader = DownloadManager()

    try:
        while True:
            # Step 1: Search
            query = input("\n🎬 Enter movie/series name (or 'quit' to exit): ").strip()

            if query.lower() in ("quit", "exit", "q"):
                print("\n👋 Goodbye!")
                break

            if not query:
                print("  ⚠️ Please enter a search term!")
                continue

            # Step 2: Get search results
            results = scraper.search(query)

            if not results:
                print("  ❌ No results found! Try different keywords.")
                continue

            # Step 3: Select a title
            selected_title = select_from_list(results, "title", "Select title")

            if not selected_title:
                continue

            print(f"\n  ✅ Selected: {selected_title['title']}")

            # Step 4: Select language
            language = select_language()
            lang_display = language if language else "All"
            print(f"  🌍 Language: {lang_display}")

            # Step 5: Get subtitles
            subtitles = scraper.get_subtitles(selected_title["url"], language)

            if not subtitles:
                print("  ❌ No subtitles found for this selection!")
                continue

            # Step 6: Select subtitles to download
            print(f"\n📋 Found {len(subtitles)} subtitles:")
            selected_subs = multi_select_from_list(subtitles, "title")

            if not selected_subs:
                continue

            print(f"\n  ✅ Selected {len(selected_subs)} subtitles for download")

            # Step 7: Get download links and download
            download_links = []

            print("\n🔗 Extracting download links...")
            for i, sub in enumerate(selected_subs, 1):
                print(f"  [{i}/{len(selected_subs)}] Processing: {sub['title'][:50]}...")
                dl_link = scraper.get_download_link(sub["url"])

                if dl_link:
                    download_links.append((dl_link, sub["title"]))
                    print(f"    ✅ Link found!")
                else:
                    print(f"    ❌ Could not extract download link")

            if not download_links:
                print("\n  ❌ No download links could be extracted!")
                continue

            # Step 8: Download files
            downloaded = downloader.download_multiple(download_links)

            # Step 9: Auto-zip if needed
            if downloaded:
                zip_result = downloader.auto_zip_if_needed()
                if zip_result:
                    # Ask if user wants to cleanup individual files
                    cleanup = input("\n  🧹 Delete individual files? (y/n): ").strip().lower()
                    if cleanup == "y":
                        downloader.cleanup()

            print("\n" + "=" * 50)
            print("✅ Operation completed!")
            print("=" * 50)

    except KeyboardInterrupt:
        print("\n\n👋 Interrupted! Goodbye!")

    finally:
        scraper.close()


if __name__ == "__main__":
    main()
