# Shipping the Product Layer: Landing Page, Session Persistence, and Auth Scaffolding

**Published:** 2026-03-09
**Author:** Seques Team

---

Phase 1 gave us a working engine. Today we shipped the product layer on top of it.

Six things landed: a landing page, session URL persistence, a reversible approve flow, clearer tab labels, backend auth scaffolding with JWT validation and RLS policies, and per-session guardrails. Some of these are live and working. One — auth — is scaffolded but not activated yet. Here's what we did and why.

---

## Landing Page as the First Screen

Before today, the first thing you saw at the app URL was the upload form. No context, no explanation — just file pickers and a "Run it" button.

We added a landing page as the first screen in the React SPA. Not a separate static site, not a different subdomain — just a new `Landing.jsx` screen that renders before the upload flow. Same dark theme, same Vite bundle, no extra deploy surface.

The page covers three things: what the product does (one sentence), what's actually shipped (v0.3.0 highlights with honest notes about trade-offs), and what's coming next (Phase 2 backlog). The CTA drops you straight into the upload flow.

The "where we are today" section is intentionally candid. We list the real constraints — sequential processing by default, 32KB doc budget, no auth yet, in-memory sessions. A landing page that hides these does more harm than good for a beta product.

---

## Session URL Persistence

Hard-refreshing mid-session killed your work. All session state lived in React `useState` — no URL, no recovery.

The fix is simple: when processing starts, we push `?s=<sessionId>` to the browser URL via `window.history.pushState`. On mount, `App.jsx` reads that param, calls `GET /api/sessions/{id}/status` to check if processing is complete, and if so calls `GET /api/sessions/{id}/answers` to restore questions and answers directly to the Review screen.

If the session doesn't exist (expired, wrong ID, server restarted), we silently strip the param and land on the upload screen. No error page.

`handleReset` (triggered by "seques" wordmark or "+ New") calls `window.history.replaceState` to clear the param. Clean URL, clean state.

This works today because `_restore_session()` in `main.py` already tries Supabase as a fallback on cache miss. When Supabase persistence is wired in Phase 2, hard-refresh restores sessions even after a server restart.

---

## Un-approve Button

Approve was a one-way operation. Once you hit it, the only way to un-approve was to edit the answer text, which set the status to "edited" — but left the APPROVED badge gone with no obvious path back if you changed your mind.

We added an "Un-approve" button that appears on the card actions row whenever `status === 'approved'` and the card isn't in edit mode. It calls `onUpdate({ status: 'edited' })` — the same PATCH endpoint, just setting status back to edited.

Approve and Un-approve are mutually exclusive in the UI. Only one shows at a time.

---

## Tab Labels: Answered and Flagged

The Review screen had four filter tabs: All, Ready, Review, Gaps.

"Ready" and "Review" were both used as tab labels and as general English words in the UI ("ready answers", "review them"), which made the distinction confusing. "Ready" didn't clearly mean "answered with high confidence." "Review" as a tab label inside the Review screen was redundant noise.

We renamed them:
- **Ready → Answered**: questions where `!needs_review && evidence_coverage !== 'none'`
- **Review → Flagged**: questions where `needs_review === true`

"Answered" is descriptive. "Flagged" is actionable. The distinction is immediate.

---

## Auth Scaffolding: Everything Except the Gate

We built the full auth infrastructure but deliberately did not activate the auth gate. Here's what's in place:

**Frontend:**
- `Auth.jsx` — email input, Supabase `signInWithOtp()`, "Check your email" confirmation state
- `supabase.js` — exports a real Supabase client if `VITE_SUPABASE_URL` + `VITE_SUPABASE_ANON_KEY` are set; exports `null` otherwise (no crash)
- `api.js` — `setAuthToken()` and `Authorization: Bearer` header injection are implemented and exported; nothing currently calls `setAuthToken()`

**Backend:**
- `verify_token` FastAPI dependency — decodes a Supabase HS256 JWT using `SUPABASE_JWT_SECRET`; returns `None` (passthrough) when the secret is not configured
- `POST /api/sessions` is wired to `Depends(verify_token)` — auth-aware but backwards-compatible
- `POST /api/auth/verify` endpoint — accepts a raw JWT, returns `user_id` + `email`
- Per-user session cap: `MAX_SESSIONS_PER_USER=3` (env-configurable); enforced only when auth is enabled
- Per-session question cap: `MAX_QUESTIONS_PER_SESSION=100`; enforced on every questionnaire upload regardless of auth state

**Database:**
- `migrations/002_rls_policies.sql` — adds `user_id` to sessions, enables RLS on all tables, creates per-user ownership policies for sessions/questions/answers, INSERT-only audit policy for service role

**What's not wired:** The auth gate in `App.jsx`. Right now, `App.jsx` doesn't import `supabase.js` at all. The app works without any Supabase credentials. When we're ready to activate auth, the change is two lines in `App.jsx` (check session on mount, render `<Auth />` if no user) and adding `Depends(verify_token)` to the remaining session routes.

Why not activate it now? The app needs to work for demos and testing without a Supabase project configured. Activating the gate would block everyone who doesn't have credentials set up. The scaffolding is there; flipping the switch is a one-PR change.

---

## What Didn't Ship

**Full Supabase persistence**: The CRUD layer (`database.py`) is scaffolded and `_restore_session()` works. What's missing is wiring `main.py` to write sessions/questions/answers to Supabase on creation instead of just on demand. That's Phase 2.

**Security middleware**: `SecurityHeadersMiddleware` and `RateLimitMiddleware` remain disabled. They were intercepting exceptions before CORS headers could be applied, breaking all API calls from the frontend. The fix is non-trivial — middleware exception handling in Starlette requires care. Tracked as an open issue.

**Auth gate**: As described above — scaffolded, not activated.

---

## What's Next

Phase 2 starts with:
1. Run the two SQL migrations in Supabase dashboard
2. Activate the auth gate — two lines in `App.jsx`, `Depends(verify_token)` on remaining routes
3. Wire Supabase persistence — `database.py` writes instead of in-memory-only
4. Fix and re-enable the security middleware
5. RAG for large compliance documents

The engine is solid. The product surface is taking shape. Auth is the unlock for everything multi-tenant.

---

*Seques is an AI-powered security questionnaire co-pilot. Vendors upload their compliance docs and a prospect's questionnaire. The AI drafts every answer. Teams review, edit, and export. We're in early access — [reach out](mailto:access@seques.ai) if you're spending hours filling out security questionnaires manually.*
