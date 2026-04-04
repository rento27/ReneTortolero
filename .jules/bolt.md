## 2026-02-03 - Regex XML Parsing Trap
**Learning:** Regex `d="(.*?)"` in XML parsing can be dangerous if other attributes like `id` end in `d` (e.g. `id="foo"`).
**Action:** Always use word boundaries or whitespace checks (e.g., `\s+d=`) when extracting attributes via regex.
