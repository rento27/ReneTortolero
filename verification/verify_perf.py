
from playwright.sync_api import sync_playwright

def verify_video_optimization():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Loading the local file
        page.goto("file:///app/experiencia.html")

        # Select the video element
        video = page.locator("video")

        # Verify preload attribute
        preload_attr = video.get_attribute("preload")
        print(f"Preload attribute: {preload_attr}")

        # Verify poster attribute
        poster_attr = video.get_attribute("poster")
        print(f"Poster attribute: {poster_attr}")

        # Take a screenshot
        page.screenshot(path="verification/experiencia_optimized.png")

        browser.close()

if __name__ == "__main__":
    verify_video_optimization()
