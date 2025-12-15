## 2024-12-15 - Lazy Loading LCP Anti-pattern
**Learning:** Applying `loading="lazy"` to images that are likely the Largest Contentful Paint (LCP) element (above the fold) is a performance anti-pattern. It delays the browser's ability to prioritize and load the most important visual content.
**Action:** Always check if an image is in the initial viewport before adding lazy loading. If in doubt, default to eager loading for the first image on the page.

## 2024-12-15 - Video Preload Optimization
**Learning:** Adding `preload="none"` to video elements can significantly reduce initial data usage, especially for large video files that users might not play immediately.
**Action:** Audit all `<video>` and `<audio>` tags for `preload` attributes.
