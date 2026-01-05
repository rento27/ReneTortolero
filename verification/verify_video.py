import os
from playwright.sync_api import sync_playwright

def verify_video():
    # Construct absolute file path
    file_path = os.path.abspath("experiencia.html")
    url = f"file://{file_path}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the local file
        print(f"Navigating to {url}")
        page.goto(url)

        # Wait for the video element to be attached
        video = page.locator("video")
        video.wait_for()

        # Get attributes
        preload = video.get_attribute("preload")
        poster = video.get_attribute("poster")

        print(f"Preload attribute: {preload}")
        print(f"Poster attribute: {poster}")

        # Verify
        if preload != "none":
            print("ERROR: preload attribute is not 'none'")
            exit(1)

        if poster is not None:
             print("ERROR: poster attribute should be removed")
             exit(1)

        # Take screenshot of the video element area
        page.screenshot(path="verification/verification.png")
        print("Verification screenshot saved.")

        browser.close()

if __name__ == "__main__":
    verify_video()
