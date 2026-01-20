from playwright.sync_api import sync_playwright

def verify(page):
    print("Navigating to app...")
    page.goto("http://localhost:4173")

    print("Checking title...")
    # Verify header text
    page.wait_for_selector("text=Notaría Pública No. 4")

    print("Taking screenshot...")
    page.screenshot(path="/home/jules/verification/frontend.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify(page)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()
