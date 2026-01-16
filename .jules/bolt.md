# Bolt's Journal
This journal records critical performance learnings and architectural insights.

## 2024-01-26 - Media Preloading Strategy
**Learning:** Large media assets (video/audio) included via HTML tags default to `preload="metadata"` or "auto" in many browsers, causing significant bandwidth consumption (~2.7MB for `vio.mp4`) on page load even if the user never plays them.
**Action:** Always explicitly set `preload="none"` for non-critical media elements to save bandwidth and improve initial load performance.

## 2024-01-26 - Video Preloading & UX
**Learning:** Using `preload="none"` on `<video>` tags without a `poster` image results in a blank/black element, which degrades UX.
**Action:** Use `preload="metadata"` if no poster image is available to ensure the video preview (first frame) is displayed, while still avoiding full content buffering.
