## 2024-05-23 - Static Site Media Optimization
**Learning:** Even small static sites can suffer from significant bandwidth waste. The absence of `preload="none"` on `<video>`/`<audio>` tags defaults to browser-dependent behavior (often downloading metadata or buffers), which can be costly on mobile.
**Action:** Always audit media tags in static HTML. Ensure `preload="none"` is used unless autoplay is required. Verify referenced assets (like `poster` images) actually exist to avoid 404 latency.
