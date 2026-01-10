from playwright.sync_api import sync_playwright, expect

def verify_video_attributes():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Load the local HTML file
        page.goto("file:///app/experiencia.html")

        # Locate the video element
        video = page.locator("video")

        # Verify attributes
        # 1. preload should be "none"
        expect(video).to_have_attribute("preload", "none")

        # 2. poster attribute should NOT exist (or be null/empty depending on how browser reports it)
        # Playwright to_have_attribute checks existence and value.
        # To check non-existence is trickier with standard matchers, but we can get the attribute.
        poster = video.get_attribute("poster")
        if poster is not None:
             print(f"FAILURE: Poster attribute exists and is: {poster}")
             exit(1)

        print("SUCCESS: Video has preload='none' and no poster attribute.")

        # Take a screenshot just to see the black box
        page.screenshot(path="verification/video_optimized.png")

        browser.close()

if __name__ == "__main__":
    verify_video_attributes()
