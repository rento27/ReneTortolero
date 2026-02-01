# Bolt's Journal

## 2025-02-01 - [Initial Setup]
**Learning:** Legacy HTML portfolio lacks build tools and test suite. Verification must be manual or via simple script checks.
**Action:** Rely on `read_file` and manual visual inspection logic.

## 2025-02-01 - [Invalid Video Poster]
**Learning:** Found `<video poster>` pointing to a `.mp4` file. This is invalid HTML and causes wasted network requests or 404s.
**Action:** Check `poster` attributes to ensure they reference image files (jpg, png, webp) only.
