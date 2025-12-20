# Bolt's Journal

## 2024-05-22 - Missing Media Assets
**Learning:** The project references a `poster` image for a video that does not exist (`video/war.mp4`). This causes a 404 error and unnecessary network request.
**Action:** Always verify asset existence before referencing them. Remove broken references or replace them with valid ones. Use `preload="none"` for videos when no poster is available or to save bandwidth.
