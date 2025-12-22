## 2024-05-23 - Static Asset Constraints
**Learning:** The project lacks an image processing pipeline (e.g., ffmpeg, imagemagick) and relies on manually placed static assets. This results in large files (e.g., 700KB thumbnails) being served.
**Action:** Future optimizations must rely on client-side attributes (`preload="none"`, `loading="lazy"`) rather than resizing or compressing assets on the server/build side. Always verify file existence (like `poster` attributes) manually as there are no build checks.
