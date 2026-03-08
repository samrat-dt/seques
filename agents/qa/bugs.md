# Bug Log

| ID | Severity | Title | Status | Fixed in |
|---|---|---|---|---|
| BUG-001 | HIGH | `ValueError: document closed` in ingest.py | Fixed | Phase 1 |
| BUG-002 | HIGH | CORS headers missing on error responses | Workaround | Phase 1 |
| BUG-003 | HIGH | `ModuleNotFoundError: openai / google-generativeai` | Fixed | Phase 1 |
| BUG-004 | MEDIUM | `allow_credentials=True` incompatible with wildcard CORS | Fixed | Phase 1 |
| BUG-005 | MEDIUM | `MutableHeaders.pop()` not available in Starlette | Fixed | Phase 1 |
| BUG-006 | MEDIUM | `str | None` union syntax fails on Python 3.9 | Fixed | Phase 1 |
| BUG-007 | LOW | Port 8000 not freed on restart (requires manual kill) | Open | — |

### BUG-001 Detail
- `ingest.py`: `len(doc)` called after `doc.close()` → `ValueError: document closed`
- Fix: store page count before closing — `return "\n\n".join(pages), len(pages)`

### BUG-002 Detail
- SecurityHeadersMiddleware and RateLimitMiddleware propagated exceptions past CORSMiddleware, so CORS headers were absent on error responses
- Workaround: disabled both middleware. Proper fix tracked in SEC-001/SEC-003.

### BUG-005 Detail
- `response.headers.pop("Server", None)` raises `AttributeError`
- Fix: `try: del response.headers["server"] \nexcept KeyError: pass`

### BUG-006 Detail
- Python 3.9 does not evaluate `str | None` union syntax at runtime
- Fix: `from __future__ import annotations` added to all affected files
