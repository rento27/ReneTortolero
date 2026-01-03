## 2024-05-23 - Broken Media Attributes & Preloading
**Learning:** HTML media attributes like `poster` that point to non-existent files cause unnecessary 404 network requests, degrading performance. Missing `preload="none"` on large video/audio assets causes browser pre-buffering, wasting bandwidth even if the user never plays the media.
**Action:** Always verify existence of static assets referenced in HTML. Default to `preload="none"` for large media files unless they are critical to the immediate user experience (e.g., above the fold hero videos).
