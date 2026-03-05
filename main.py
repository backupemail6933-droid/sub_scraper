"""
Subscene Scraper - Main Entry Point
"""

from scraper import SubsceneScraper
from downloader import DownloadManager
from config import LANGUAGES


def banner():
    print("""
╔══════════════════════════════════════════════════════╗
║           🎬 Subscene Subtitle Scraper 🎬            ║
║        sub-scene.com | v1.1 Fixed Edition            ║
║                                                      ║
║  Search by: Movie Name  OR  IMDb ID (tt1234567)      ║
╚══════════════════════════════════════════════════════════╝
    """)


def pick_one(items, key):
    """Select single item"""
    if not items:
        print("  ⚠️ No results!")
        return None

    print()
    for i, item in enumerate(items, 1):
        print(f"  [{i}] {item[key]}")
    print(f"  [0] ❌ Cancel")

    while True:
        try:
            c = input(f"\n  👉 Choose number: ").strip()
            if c == "0":
                return None
            idx = int(c) - 1
            if 0 <= idx < len(items):
                return items[idx]
            print("  ⚠️ Invalid number!")
        except ValueError:
            print("  ⚠️ Enter a number!")


def pick_many(items):
    """Select multiple items"""
    if not items:
        return []

    print(f"\n📋 Available Subtitles ({len(items)}):")
    print("─" * 60)
    for i, item in enumerate(items, 1):
        lang = item.get("language", "?")
        title = item.get("title", "?")[:55]
        print(f"  [{i:3d}] [{lang:>10s}] {title}")
    print("─" * 60)
    print(f"  [a] ✅ Select ALL ({len(items)} files)")
    print(f"  [0] ❌ Cancel")

    c = input(f"\n  👉 Choose (e.g. 1,3,5 or 'a' for all): ").strip()

    if c == "0":
        return []
    if c.lower() == "a":
        return items

    selected = []
    try:
        for x in c.split(","):
            x = x.strip()
            # Support ranges like 1-5
            if "-" in x:
                parts = x.split("-")
                start, end = int(parts[0]), int(parts[1])
                for idx in range(start - 1, end):
                    if 0 <= idx < len(items):
                        selected.append(items[idx])
            else:
                idx = int(x) - 1
                if 0 <= idx < len(items):
                    selected.append(items[idx])
    except ValueError:
        print("  ⚠️ Invalid input!")

    return selected


def pick_lang():
    """Select language filter"""
    print("\n🌍 Filter by Language:")
    for k, v in LANGUAGES.items():
        print(f"  [{k}] {v}")
    print(f"  [0] 🌐 All Languages")

    c = input("\n  👉 Choose: ").strip()
    lang = LANGUAGES.get(c, None)
    print(f"  🌍 Selected: {lang or 'All Languages'}")
    return lang


def main():
    banner()
    scraper = SubsceneScraper()
    dl = DownloadManager()

    try:
        while True:
            print("\n" + "=" * 50)
            query = input("🎬 Enter movie name or IMDb ID (q to quit): ").strip()

            if query.lower() in ("q", "quit", "exit"):
                print("\n👋 Goodbye!")
                break

            if not query:
                print("  ⚠️ Please enter something!")
                continue

            # ============================================
            # Step 1: Search
            # ============================================
            results = scraper.search(query)

            if not results:
                print("  ❌ No results! Try different keywords.")
                continue

            # ============================================
            # Step 2: Pick title
            # ============================================
            title = pick_one(results, "title")
            if not title:
                continue

            print(f"\n  ✅ Selected: {title['title']}")
            print(f"  🔗 URL: {title['url']}")

            # ============================================
            # Step 3: Pick language
            # ============================================
            lang = pick_lang()

            # ============================================
            # Step 4: Get subtitles
            # ============================================
            subs = scraper.get_subtitles(title["url"], lang)

            if not subs:
                print("  ❌ No subtitles found!")
                continue

            # ============================================
            # Step 5: Pick subtitles
            # ============================================
            chosen = pick_many(subs)

            if not chosen:
                continue

            print(f"\n  ✅ Selected {len(chosen)} subtitles")

            # ============================================
            # Step 6: Extract download links
            # ============================================
            print(f"\n🔗 Extracting download links...")
            print("─" * 50)

            dl_links = []
            for i, sub in enumerate(chosen, 1):
                short_title = sub["title"][:45]
                print(f"  [{i}/{len(chosen)}] {short_title}...", end=" ")
                link = scraper.get_download_link(sub["url"])
                if link:
                    dl_links.append((link, sub["title"]))
                    print("✅")
                else:
                    print("❌ (no link found)")

            print("─" * 50)

            if not dl_links:
                print("  ❌ Could not extract any download links!")
                continue

            print(f"  📊 Got {len(dl_links)}/{len(chosen)} links")

            # ============================================
            # Step 7: Download
            # ============================================
            downloaded = dl.download_batch(dl_links)

            # ============================================
            # Step 8: Auto-zip if needed
            # ============================================
            if downloaded:
                zip_result = dl.auto_zip()
                if zip_result:
                    cleanup = input("\n  🧹 Delete individual files? (y/n): ").strip().lower()
                    if cleanup == "y":
                        dl.cleanup()

            # Show results
            dl.show_files()

            print("\n✅ Operation completed!")
            print("=" * 50)

    except KeyboardInterrupt:
        print("\n\n👋 Interrupted! Goodbye!")

    finally:
        scraper.close()


if __name__ == "__main__":
    main()
