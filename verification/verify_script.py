from playwright.sync_api import sync_playwright

def verify_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # Navigate to the Vite preview server
            page.goto("http://localhost:5174")

            # Wait for content to load
            page.wait_for_selector("div#root")

            # Take a screenshot
            page.screenshot(path="verification/orion_ui.png")
            print("Screenshot taken successfully.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_frontend()
