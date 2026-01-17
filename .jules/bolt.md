## 2024-05-23 - Memory vs Reality Mismatch
**Learning:** Memory stated optimizations (video preload, poster removal) were already present, but file inspection proved they were missing. Memory can be stale or refer to lost state.
**Action:** Always verify "known" optimizations against the actual codebase before assuming they exist. Trust `read_file` over memory.
