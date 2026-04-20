from playwright.sync_api import sync_playwright

def verify_app():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # Navigate to the app (served from la-sal-pwa directory)
            page.goto("http://localhost:8000/index.html")

            # Wait for the Stats panel to appear (indicates React loaded)
            page.wait_for_selector("text=LASAL PLAYA")

            # Take a screenshot of the main view
            page.screenshot(path="verification/app_view.png", full_page=True)
            print("Screenshot taken: app_view.png")

            # Test filter interaction
            # Click 'Falta Pago'
            page.get_by_text("Falta Pago").click()
            page.wait_for_timeout(500) # Wait for filter to apply visually
            page.screenshot(path="verification/filter_view.png", full_page=True)
            print("Screenshot taken: filter_view.png")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_app()
