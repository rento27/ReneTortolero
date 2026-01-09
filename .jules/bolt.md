## 2024-05-23 - Static Media Optimization
**Learning:** Browsers handle `video` tags without `preload` attributes inconsistently (often defaulting to `metadata` or `auto`), which can trigger significant data usage (e.g., 2.7MB) even if the user never plays the content. Additionally, pointing `poster` attributes to non-existent files or non-image types causes unnecessary 404 requests.
**Action:** Always explicitly set `preload="none"` for below-the-fold or non-critical media and verify existence of `poster` images to save bandwidth and avoid console errors.
