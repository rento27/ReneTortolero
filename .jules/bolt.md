# Bolt's Journal

This journal records critical performance learnings.

## 2024-05-23 - Static Site Media
**Learning:** The project is a static HTML site with large media assets and no build process. Media assets like videos are loaded without `preload="none"`, causing unnecessary bandwidth usage. Broken poster links cause 404s.
**Action:** Always check for `preload="none"` on large video/audio tags in static HTML sites. Verify asset existence to prevent 404s.
