## 2024-05-23 - Broken Assets & Default Preloading
**Learning:** Broken `poster` links on video elements can cause unnecessary 404 requests, and missing `preload="none"` on large video files (2.7MB) triggers wasted bandwidth.
**Action:** Always verify asset existence and default to `preload="none"` for non-hero media.
