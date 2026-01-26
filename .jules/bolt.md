## 2024-05-22 - Asset Loading Anti-patterns
**Learning:** Found a `<video>` tag using an `.mp4` file as a `poster` image. This causes invalid requests (404) and wastes bandwidth. Also, large media files (2.7MB video) were missing `preload="none"`, risking unintentional buffering.
**Action:** Always verify `poster` attributes point to images and ensure `preload="none"` is used for large media assets below the fold or not immediately needed.
