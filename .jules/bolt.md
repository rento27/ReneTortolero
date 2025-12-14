## 2024-05-23 - Static Site Optimization
**Learning:** In simple static sites without a build system, checking for broken asset links (like `poster` attributes) manually is critical as there are no build-time checks.
**Action:** Always verify asset existence (`list_files`) before assuming attributes like `poster` are valid.
