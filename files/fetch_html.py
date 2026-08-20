import sys
from patchright.sync_api import sync_playwright

def main():
    if len(sys.argv) < 2:
        return
    url = sys.argv[1]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True
        )
        page = context.new_page()
        mpn_arg = sys.argv[2] if len(sys.argv) > 2 else ""
        page.goto(url, wait_until='domcontentloaded', timeout=15000)
        
        # Auto-click product link if on a search results page
        if mpn_arg:
            try:
                # Try to find a link containing the MPN text or href
                page.wait_for_selector(f"a:has-text(\"{mpn_arg}\"), a[href*=\"{mpn_arg.lower()}\"]", timeout=3000)
                loc = page.locator(f"a:has-text(\"{mpn_arg}\"), a[href*=\"{mpn_arg.lower()}\"]").first
                if loc.is_visible():
                    loc.click(timeout=5000)
                    page.wait_for_load_state('domcontentloaded', timeout=5000)
            except Exception:
                pass

        # ensure stdout uses utf-8
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        
        print(page.content())
        browser.close()

if __name__ == "__main__":
    main()
