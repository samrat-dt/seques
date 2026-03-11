# Seques v1.0.0-stable: Three Bugs Fixed, One Clean Handoff

**2026-03-11**

---

The v1.0.0-stable post covered what we shipped and why certain decisions got made. This one is shorter: a status check now that the dust has settled, what those three production fixes actually were, and where Phase 3 is headed.

## What's Live Right Now

The full flow works end-to-end in production. Frontend on Vercel, backend on Railway via Docker. You upload compliance docs (PDF, DOCX, up to 50MB), upload a questionnaire (PDF, Excel, or pasted text), and the AI drafts every answer using Groq by default with Anthropic as an available fallback. Sessions persist to Supabase. Export comes out as Excel or PDF.

The access-code gate is the only auth layer right now — `seques2026` by default, overridable via `VITE_ACCESS_CODE`. It's intentionally simple. Every API call carries it as a Bearer token. The backend accepts it without JWT validation (`_AUTH_ENABLED=False`). That's the trade-off we made to ship a working product instead of a broken auth integration.

## The Three Production Bugs

All three had the same root cause: certain browser APIs don't support custom request headers, and our backend requires `Authorization: Bearer <token>` on every request.

**SSE → polling.** The processing screen originally used `EventSource` to stream progress from the backend. `EventSource` is a browser API that cannot send custom headers — it just opens a GET connection with no way to attach an `Authorization` header. Every connection returned 401 immediately. The fix was replacing the stream with a 1-second poll against `/api/sessions/{id}/status`. Less elegant, works completely.

**`<a href>` → fetch+blob.** Export downloads started as direct anchor links. A plain `<a href>` causes the browser to make the GET request on its own, bypassing any JavaScript — meaning no auth header, meaning 401. Fixed by replacing it with a `fetch()` call that includes the auth token, receiving the response as a blob, creating an object URL, and triggering a programmatic click. The object URL is revoked after use.

**Magic Link → access-code.** We built Supabase Magic Link auth. It worked locally. In production, it returned "invalid api key" errors we couldn't trace to a root cause quickly. Rather than block the whole release debugging a third-party SDK, we replaced it with the access-code gate. The Supabase client in `supabase.js` now intentionally exports `null`. The env vars are still set in Vercel but the client is not initialised.

None of these were subtle bugs. They were cases where an assumption that held in local development (custom headers always work) broke against browser security constraints in production.

## Clean Handoff State

The codebase is in a clean state for any developer or agent picking it up. `docs/handover.md` is the single entry point — it covers the full capability table, every known gap (with "don't re-investigate" notes), production environment variables, auth architecture, and the exact runtime configuration as shipped. Read that first, then `docs/architecture.md`. There are no undocumented workarounds or environment-specific magic.

Running locally takes about five minutes: copy `.env.example`, add a Groq or Anthropic key, start the FastAPI server and Vite dev server. The access code is `seques2026`.

## What's Coming in Phase 3

Priority order is fixed and documented:

1. **RAG for large docs** — the 32KB document budget is the biggest quality ceiling. Most SOC 2 reports are 50-120KB; we're currently ingesting the first seven or so pages and relying on model domain knowledge for the rest. pgvector + chunk-and-embed removes that limit and improves answer accuracy for large compliance programmes.

2. **Parallel processing** — `ANSWER_CONCURRENCY=1` is stable but slow. With async LLM clients and Redis rate-budget tracking, 10× concurrency should be achievable as a reliable default. That takes a 30-question session from ~90 seconds to under 15.

3. **Redis rate limiter** — the current in-memory dict resets on restart and doesn't share state across workers. Required before any multi-worker deploy.

4. **Multi-user accounts** — invite-based auth, per-user isolation, proper JWT. The infrastructure (Supabase, RLS policies) is already in place; it's waiting on Phase 3 to get turned on.

The product is working and the foundation is honest. Phase 3 is a quality and scale problem, not a stability problem.
