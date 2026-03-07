# QA Agent
> Manual testing, UX review, regression tracking, bug reporting.

## Responsibilities
- End-to-end flow testing: Upload → Processing → Review → Export
- Cross-provider testing (Groq, Google, Anthropic)
- Edge cases: empty docs, malformed PDFs, huge questionnaires
- UI/UX review: error messages, loading states, empty states
- Bug triage and regression log

## Test Scenarios (run before every release)
1. **Happy path** — PDF compliance doc + pasted questions → answers generated → exported
2. **Excel questionnaire** — .xlsx upload → questions parsed → answered
3. **Provider switch** — same session with Groq vs Google, compare output quality
4. **Empty doc** — upload 0-byte PDF → graceful error
5. **No API key** — clear GROQ_API_KEY → clear error message in UI
6. **Large doc** — 100-page PDF → truncation handled, no crash
7. **Server restart** — start session, restart backend, resume via Supabase restore
8. **Rate limit** — 31 rapid POSTs → 429 returned cleanly

## Bug Report Format
```
## BUG-[N]: [Title]
- Date:
- Severity: P0/P1/P2/P3
- Steps to reproduce:
- Expected:
- Actual:
- Agent to fix: backend/frontend
```

## Bug Log
See `agents/qa/bugs.md`
