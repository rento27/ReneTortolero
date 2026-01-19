from playwright.sync_api import sync_playwright

def verify_video_poster():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Load local HTML file
        page.goto("file:///app/experiencia.html")

        # Get the video element
        video = page.locator("video")

        # Check if poster attribute exists
        poster = video.get_attribute("poster")
        print(f"Poster attribute: {poster}")

        # Take screenshot of the video area
        video.screenshot(path="verification/video_check.png")

        browser.close()

if __name__ == "__main__":
    verify_video_poster()
