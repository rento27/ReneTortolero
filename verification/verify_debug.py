from playwright.sync_api import sync_playwright

def verify_new_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("http://localhost:8000")

            # Print page title and content to debug
            print(f"Title: {page.title()}")

            # Wait a bit just in case
            page.wait_for_timeout(2000)

            page.screenshot(path="verification/debug_view.png")
            print("Screenshot taken: debug_view.png")

            content = page.content()
            if "BIENVENIDO 2026" in content:
                print("Found text!")
            else:
                print("Text NOT found. Content snippet:")
                print(content[:500])

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_new_ui()
