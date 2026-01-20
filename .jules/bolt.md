# Bolt's Journal

## 2025-01-20 - [Fixing Media Attributes]
**Learning:** Found a video element with a `poster` attribute pointing to a non-existent `.mp4` file. This causes a double penalty: a 404 network error and potential browser confusion or wasted bandwidth trying to decode a video as an image.
**Action:** Always check validity of resource paths in static HTML and prefer `preload="none"` for large media files to save initial bandwidth.
