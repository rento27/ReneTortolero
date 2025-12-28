from playwright.sync_api import sync_playwright

def verify_functionality():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("http://localhost:8000")
            page.wait_for_selector("text=Listado de Asistentes", timeout=10000)

            # 1. Verify Search Bar exists
            search_input = page.locator("input[placeholder='Buscar por nombre o mesa...']")
            if search_input.count() > 0:
                print("Search bar found.")
            else:
                print("Search bar NOT found.")

            # 2. Verify Filters exist
            filters = page.locator("button:has-text('Todos')")
            if filters.count() > 0:
                print("Filters found.")
            else:
                print("Filters NOT found.")

            # 3. Take screenshot of the new UI with controls
            page.screenshot(path="verification/functional_ui.png", full_page=True)
            print("Screenshot taken: functional_ui.png")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_functionality()
