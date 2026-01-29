# Bolt's Journal

## 2024-05-22 - Avoid Invalid Poster Attributes
**Learning:** `poster` attributes on `<video>` tags must point to image files. Pointing to video files or non-existent paths causes 404 errors and delays page load.
**Action:** Always verify `poster` paths exist and are images. Use `preload="none"` for heavy media below the fold.
