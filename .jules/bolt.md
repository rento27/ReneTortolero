# Bolt's Journal

## 2024-05-22 - [Manual SVG Optimization]
**Learning:** In environments without specialized tools like `svgo` or `imagemagick`, SVG optimization can be achieved by safely stripping metadata and editor-specific namespaced tags/attributes using regex, provided the core XML structure and path data are preserved.
**Action:** When standard tools are missing, create small, verifiable python scripts to perform asset optimization rather than giving up. Always verify the resulting XML is valid.
