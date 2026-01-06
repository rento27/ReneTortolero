from playwright.sync_api import sync_playwright

def verify_landing_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # Vite default port is usually 5173
            page.goto("http://localhost:5173")
            # Wait for content
            page.wait_for_selector("text=Notaría 4 Digital Core")
            page.screenshot(path="/home/jules/verification/landing_page.png")
            print("Screenshot taken successfully")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_landing_page()
