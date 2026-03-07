# Frontend Agent
> Owns everything in `frontend/src/`. React 18, Vite, Tailwind CSS.

## Responsibilities
- All screens: Upload, Processing, Review, Export
- `api.js` — all fetch calls to backend
- Component styling (Tailwind only, no custom CSS)
- Provider selector UI
- Error handling and loading states

## Key Files
| File | Purpose |
|---|---|
| `src/api.js` | All fetch calls — add new endpoints here first |
| `src/App.jsx` | Screen routing state machine |
| `src/screens/Upload.jsx` | Step 1 — uploads + provider selection |
| `src/screens/Processing.jsx` | Step 2 — polls /status |
| `src/screens/Review.jsx` | Step 3 — edit/approve answers |
| `src/screens/Export.jsx` | Step 4 — download |

## Constraints
- Backend CORS allows: localhost:5173, 5174, 3000
- No external UI libraries — Tailwind only
- No emojis in UI unless user-requested
- All API calls go through `api.js` — never fetch() directly in components

## Run
```bash
cd frontend && npm run dev
```
Vite picks the next available port if 5173 is taken.

## After Every Change
- Update `agents/frontend/memory.md`
