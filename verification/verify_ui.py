from playwright.sync_api import sync_playwright

def verify_new_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # Navigate to the app (served from la-sal-pwa/dist directory)
            page.goto("http://localhost:8000")

            # Wait for text distinctive to the new UI
            # "Menú Degustación" or "BIENVENIDO 2026"
            page.wait_for_selector("text=BIENVENIDO 2026")

            # Take a screenshot of the main view
            page.screenshot(path="verification/new_ui_view.png", full_page=True)
            print("Screenshot taken: new_ui_view.png")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_new_ui()
