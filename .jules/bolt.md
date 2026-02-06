## 2025-02-05 - satcfdi v4 API Mismatch
**Learning:** `satcfdi` v4 enforces snake_case arguments in `Comprobante` constructor and rejects explicit `SubTotal`/`Total` arguments to enforce auto-calculation. Passing PascalCase arguments (like `Emisor`) causes `TypeError`.
**Action:** Always verify `satcfdi` version and use `help()` or `inspect` to check constructor signatures before assuming PascalCase mapping.
