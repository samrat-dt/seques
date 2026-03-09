# Seques UI Revamp Plan

> Status: Design spec — ready for engineering implementation.
> Aesthetic direction: dark base, warm amber accent, editorial type, no emoji icons.
> Inspiration: Linear density, Vercel cleanliness, Raycast personality, Resend minimalism.

---

## 1. Design System

### 1.1 Color Palette

All colors defined as CSS custom properties and Tailwind config values. The background stack uses three surface levels so cards visually lift off the page without heavy shadows.

#### Background layers

| Token          | Hex       | Usage                                           |
|----------------|-----------|-------------------------------------------------|
| `bg-base`      | `#0d0d0f` | Root page background — near-black with warmth   |
| `bg-surface`   | `#141416` | Card / panel surface                            |
| `bg-raised`    | `#1c1c20` | Inputs, code blocks, hover states inside a card |
| `bg-overlay`   | `#242428` | Dropdowns, tooltips, active drag zones          |

#### Accent — Amber

Amber reads as "high-signal" (the color of a warning light, a terminal cursor, a sticky note on a monitor) — appropriate for a security tool that demands attention. Not the cliche blue.

| Token            | Hex       | Usage                                       |
|------------------|-----------|---------------------------------------------|
| `accent`         | `#f59e0b` | Primary CTAs, active tab underlines, links  |
| `accent-dim`     | `#92400e` | Disabled/muted CTA state                   |
| `accent-glow`    | `rgba(245,158,11,0.12)` | Box shadow glow for primary buttons |
| `accent-subtle`  | `rgba(245,158,11,0.08)` | Drag-over zone highlight fill       |

#### Text hierarchy (4 levels)

| Token        | Hex       | Usage                                            |
|--------------|-----------|--------------------------------------------------|
| `text-primary`   | `#f0ede8` | Headings, question text, active labels — warm off-white |
| `text-secondary` | `#9b9691` | Subtext, descriptions, counts                    |
| `text-muted`     | `#5a5753` | Placeholder copy, disabled states, hints         |
| `text-inverse`   | `#0d0d0f` | Text on amber accent buttons                     |

#### Borders

| Token           | Hex                     | Usage                                    |
|-----------------|-------------------------|------------------------------------------|
| `border-subtle` | `rgba(255,255,255,0.06)` | Default card borders — barely-there     |
| `border-mid`    | `rgba(255,255,255,0.12)` | Input borders, dividers                 |
| `border-strong` | `rgba(255,255,255,0.20)` | Hover borders, focus rings              |

#### Semantic states (status colors)

| State    | Background hex  | Text hex  | Border hex  | Notes                      |
|----------|-----------------|-----------|-------------|----------------------------|
| Success  | `#052e16`       | `#4ade80` | `#166534`   | Covered, Approved          |
| Warning  | `#2d1a00`       | `#fbbf24` | `#92400e`   | Partial coverage, Needs review |
| Danger   | `#2d0a0a`       | `#f87171` | `#991b1b`   | Gaps, no evidence          |
| Info     | `#0c1a2e`       | `#60a5fa` | `#1e40af`   | Edited, informational      |
| Neutral  | `#1c1c20`       | `#9b9691` | `rgba(255,255,255,0.12)` | Default draft state |

---

### 1.2 Typography

Two fonts. One for UI chrome, one for content — they contrast without fighting.

#### Font 1: Inter (UI font)
- Provider: Google Fonts
- Weights: 400, 500, 600, 700
- Used for: nav, tabs, buttons, badges, labels, metadata
- Why: The canonical dark-UI font. Reads perfectly at 11–14px. Everyone's used to it for tool UIs.

#### Font 2: DM Serif Display (Display / heading font)
- Provider: Google Fonts
- Weights: 400 (regular only — this font is a display face)
- Used for: Screen H1 headings only (Upload, Processing, Review, Export heroes)
- Why: Introduces editorial warmth and personality against a dark background. One serif word in a sans-serif UI creates instant identity without trying hard.

#### Font 3: JetBrains Mono (Code/mono)
- Provider: Google Fonts
- Weights: 400, 500
- Used for: Question IDs, certainty percentages, session IDs, file sizes — anything that should feel precise
- Why: The tool is for technical buyers. A little monospace signals that you mean business.

#### Type scale (Tailwind class → pixel equivalent)

| Role               | Tailwind class       | px size | Weight | Font         |
|--------------------|----------------------|---------|--------|--------------|
| Screen H1          | `text-3xl` / `text-4xl` | 30–36px | 400  | DM Serif Display |
| Section heading    | `text-xl`            | 20px    | 600    | Inter        |
| Card title / Q text| `text-sm` leading-relaxed | 14px | 500  | Inter        |
| Body / answer text | `text-sm`            | 14px    | 400    | Inter        |
| Label / badge      | `text-xs`            | 12px    | 500    | Inter        |
| Mono (IDs, scores) | `font-mono text-xs`  | 11px    | 500    | JetBrains Mono |

---

### 1.3 Border Radius System

| Token    | Value      | Tailwind      | Usage                                    |
|----------|------------|---------------|------------------------------------------|
| Subtle   | `4px`      | `rounded`     | Badges, pills, monospace chips           |
| Card     | `10px`     | `rounded-xl`  | Cards, panels, drop zones                |
| Button   | `8px`      | `rounded-lg`  | All buttons                              |
| Pill     | `9999px`   | `rounded-full`| Status dot indicators only               |
| Input    | `6px`      | `rounded-md`  | Text areas, text inputs                  |

No `rounded-2xl` or `rounded-3xl` anywhere — the tool should feel precise, not bubbly.

---

### 1.4 Shadow / Glow System

Shadows are sparse. Most depth comes from layered background colors, not box-shadows. Glows are used exclusively on primary interactive elements to signal affordance.

| Name          | CSS value                                                              | Used on               |
|---------------|------------------------------------------------------------------------|-----------------------|
| `card`        | `0 1px 2px rgba(0,0,0,0.5)`                                            | Cards on base bg      |
| `card-hover`  | `0 4px 16px rgba(0,0,0,0.4)`                                           | Cards on hover        |
| `btn-primary` | `0 0 0 1px rgba(245,158,11,0.3), 0 4px 12px rgba(245,158,11,0.15)`     | Primary CTA buttons   |
| `input-focus` | `0 0 0 2px rgba(245,158,11,0.25)`                                      | Focused textareas     |
| `glow-success`| `0 0 0 1px rgba(74,222,128,0.2)`                                       | Approved card border  |

No outer glow on every card by default — glows devalue themselves if overused.

---

### 1.5 Spacing Philosophy

Consistent 8px grid. Tailwind's default spacing scale is already on this grid. Key rules:

- Minimum touch target: 32px tall (`h-8`) for small interactive elements
- Card internal padding: `p-5` (20px) — not `p-6` (24px), which feels spacious on dark bg
- Section vertical rhythm: `gap-4` between cards, `gap-6` between major sections
- Page horizontal max-width: `max-w-4xl` for Review (content-dense), `max-w-3xl` for Upload/Processing/Export (focused)
- Page top padding: `py-10` — generous breathing room below the nav
- Nav height: 52px (`h-13` or just set explicit height in CSS)

---

## 2. Component Inventory

### 2.1 Nav Bar

**Height**: 52px fixed. `position: sticky; top: 0; z-index: 50`.

**Background**: `bg-base` (`#0d0d0f`) with a 1px bottom border at `border-subtle`. Slight backdrop blur: `backdrop-filter: blur(12px)`. The bg is slightly transparent (`bg-[#0d0d0f]/95`) so page content bleeds through when scrolling, signaling depth.

**Wordmark treatment**: `seques` in Inter 600, 16px, color `text-primary`. No subtitle copy in the nav — it's redundant. A thin amber underline `2px solid accent` sits below the wordmark as a logo device (done via a `::after` pseudo-element or a `<span>` with `border-b-2 border-amber-400`). This is the only place the accent appears in the nav.

**Step indicator**: Sits in the center of the nav (see section 2.2). Replaces the subtitle.

**Right side**: When screen !== 'upload', show a ghost button: `+ New` — not the verbose "New Questionnaire". On hover: text shifts to `text-primary`, underline appears. No border, no bg — ghost style only.

**Code structure**:
```
<nav class="sticky top-0 z-50 h-[52px] bg-[#0d0d0f]/95 backdrop-blur-sm border-b border-white/[0.06] flex items-center px-6">
  <div class="max-w-4xl mx-auto w-full flex items-center justify-between">
    [wordmark]   [step indicator]   [new button]
  </div>
</nav>
```

---

### 2.2 Step Indicator

Replaces the old subtitle. Sits centered in the nav. Shows workflow position at a glance.

**Design**: Four items connected by thin lines. Active step = amber text + filled dot. Done steps = dimmed text + check mark (SVG, not emoji). Future steps = muted text + empty dot.

**Structure** (horizontal, always visible):
```
● Upload  —  ○ Processing  —  ○ Review  —  ○ Export
```

- Dot diameter: 6px (`w-1.5 h-1.5`)
- Connector line: 24px wide, 1px tall, `bg-border-subtle`
- Step label: `text-xs font-medium` Inter
- Active label: `text-amber-400`
- Done label: `text-secondary` with a 10px SVG check replacing the dot
- Future label: `text-muted`
- Entire indicator: `hidden sm:flex items-center gap-2`

This is always visible, always reflects where the user is. It is not clickable (no back-navigation from nav — use the "Back to Review" button on Export).

---

### 2.3 Upload Screen

**Layout**: Single column, max-w-3xl, centered. The two drop zones stack vertically on mobile, side-by-side at md breakpoint. Vertical stack order: Hero → Model selector → Drop zones (2-col grid) → CTA row.

**Hero section**:
- H1: DM Serif Display, `text-3xl`, `text-primary`. See copy section for text.
- Subtext: Inter 400, `text-sm`, `text-secondary`. One line max.
- Vertical margin below: `mb-8`

**Drop zone design** (both zones share this treatment):

The drop zone is a bordered rectangle with a subtle inner texture — achieved via a CSS `background-image` with a very faint dot-grid pattern (SVG data URI) on `bg-surface`. This avoids the generic flat-white feel.

```css
background-color: #141416;
background-image: radial-gradient(circle, rgba(255,255,255,0.04) 1px, transparent 1px);
background-size: 20px 20px;
border: 1px solid rgba(255,255,255,0.08);
border-radius: 10px;
```

**Default state** (no files):
- Centered icon zone: a small SVG icon (file stack for docs, file-spreadsheet for questionnaire) — `w-8 h-8`, stroke color `text-muted`
- Below icon: primary label `text-sm text-secondary font-medium`
- Below label: secondary hint `text-xs text-muted`
- Browse link: `text-amber-400 text-xs font-medium hover:text-amber-300 underline-offset-2 hover:underline`

**Drag-over state**:
- Border upgrades to `border-amber-400/50` (1px, not dashed)
- Background gets `accent-subtle` overlay: `rgba(245,158,11,0.05)` layered on top
- Icon color shifts to `text-amber-400`
- No dashed border anywhere — dashed feels dated

**File added state (Compliance docs)** — files list inside the zone:
- Each file row: `bg-raised` pill with filename truncated, file size in mono, and an `×` remove button (SVG X icon, not ✕ character) on the right
- Left of filename: a small SVG document icon, `text-secondary`
- No green background per row — just `bg-raised` with `border-subtle`

**File added state (Questionnaire)** — single file selected:
- Large filename centered in the zone, `text-sm text-primary font-medium`
- Below: file size in mono `text-xs text-muted`
- "Remove" as a subtle link below: `text-xs text-muted hover:text-danger`
- Drop zone shrinks to just enough height to show this cleanly

**Paste textarea (Questionnaire zone)**:
- The "or paste questions" divider: `text-xs text-muted` with 1px lines on either side (`bg-border-mid`)
- Textarea: `bg-raised border border-mid rounded-md p-3 text-sm text-primary placeholder:text-muted font-mono` — monospace because these are structured questions
- Focus: `border-border-strong outline-none ring-2 ring-amber-400/20`
- No resize handle: `resize-none`

**AI Model selector**:
- Sits above the drop zones, left-aligned
- Label: `text-xs text-muted uppercase tracking-widest font-medium` — "via"
- Provider buttons: `text-xs font-medium px-3 py-1 rounded-lg border`
  - Default: `bg-surface border-mid text-secondary hover:border-strong hover:text-primary`
  - Selected: `bg-raised border-amber-400/50 text-amber-400` — no filled bg, just an amber border and text
  - Unconfigured: `opacity-30 cursor-not-allowed`
- Active model name: `text-xs text-muted font-mono ml-2` — shown inline after the buttons

**CTA row** (bottom of screen):
- Left: status text `text-xs text-secondary` — "3 docs loaded" or "Add compliance docs to continue"
- Right: Primary button (see Buttons section, 2.9)
- Button disabled state: `opacity-40 cursor-not-allowed` — no bg color change, just opacity drop

---

### 2.4 Processing Screen

Replace progress bars with a **log-stream terminal widget**. This is far more alive and appropriate for a developer-friendly tool.

**Concept**: A dark terminal panel, fixed width `max-w-2xl`, padded. Lines appear one by one as processing progresses, each line prefixed with a timestamp and a status glyph. The illusion of watching the AI work in real time.

**Panel design**:
- Background: `bg-surface`, rounded-xl, border `border-subtle`
- Top bar (terminal chrome): a thin strip `h-8 bg-raised rounded-t-xl border-b border-subtle` with three colored dots (SVG circles — `#ff5f57 #ffbd2e #27c93f`, the macOS traffic lights) at `ml-4`. Right of the dots: `text-xs text-muted font-mono` showing "seques — processing"
- Content area: `p-5` below the chrome bar
- Font: JetBrains Mono throughout

**Line format**:
```
HH:MM:SS  ▶  Parsed compliance documents         [3 files]
HH:MM:SS  ✓  Extracted questions                  [12]
HH:MM:SS  ▶  Answering question 4 of 12...
```

- Timestamp: `text-muted text-xs` (actual current time, derived from `new Date().toLocaleTimeString()`)
- Status glyph: `▶` for in-progress (amber, pulsing), `✓` for done (success green), `✗` for error (danger red) — these are Unicode characters, not emoji, rendered in monospace
- Label: `text-primary text-xs`
- Count: `text-secondary text-xs` right-aligned or just appended with `[N]` bracket notation

**Animation**: Each new log line fades in with a 150ms opacity transition. A blinking cursor `▋` (Unicode block element) follows the active line. No CSS spinner, no circular loader.

**In-progress pulsing**: The `▶` glyph on the active line has `animate-pulse` in amber.

**Below the terminal**: A single line of copy `text-xs text-muted text-center mt-6`: "Typically 1–3 min. Grab a coffee." — not in the terminal, below it.

**Error state**: An `✗` line appended to the log in danger red. Below the terminal, a `bg-[#2d0a0a] border border-[#991b1b] rounded-lg p-4 text-xs text-[#f87171]` panel with the error message and a "Try again →" link.

---

### 2.5 QuestionCard

The card is the core work surface. The redesign prioritizes left-to-right information hierarchy: status → question → answer → metadata.

**Card structure**:
```
┌─ [left accent bar 3px] ──────────────────────────────────────┐
│  ROW 1: [ID chip] [STATUS badge]          [Edit] [Approve]   │
│  ROW 2: Question text                                        │
│  ROW 3: Answer block (read or edit mode)                     │
│  ROW 4: Evidence source chips             [Coverage] [Score] │
│  ROW 5: (conditional) Suggested addition hint                │
└──────────────────────────────────────────────────────────────┘
```

**Card container**:
- `bg-surface rounded-xl border border-subtle p-5`
- Left accent bar: implemented as `border-l-3` (custom 3px left border) — color changes by status:
  - Draft/default: `border-l-border-mid` (neutral)
  - Needs review: `border-l-[#fbbf24]` (amber)
  - Approved: `border-l-[#4ade80]` (green)
  - Edited: `border-l-[#60a5fa]` (blue)
- On hover: `border-border-mid` (the full border brightens slightly) — achieved with CSS transition on border-color
- No box shadow in default state. Shadow on hover: `shadow-[0_4px_16px_rgba(0,0,0,0.4)]`

**Row 1 — header**:
- Left cluster: Question ID chip + status badge (if any)
  - ID chip: `font-mono text-xs bg-raised text-muted px-2 py-0.5 rounded` — e.g. `Q-001`
  - Status badges: see Badges section 2.8. Only show the highest-priority badge (Approved trumps Edited trumps Needs Review)
- Right cluster: action buttons (always visible — do not hide Edit when Approved, as user may want to re-edit)
  - Edit: ghost button
  - Approve: only shown when status !== 'approved'

**Row 2 — question text**:
- `text-sm text-primary font-medium leading-relaxed mt-2 mb-3`
- Full question text, no truncation

**Row 3 — answer block**:

Read mode:
- `bg-raised rounded-md p-4 text-sm text-secondary leading-relaxed whitespace-pre-wrap`
- A 1px top-left corner marker: a thin amber `2px` top-border on the block to distinguish AI-generated content from user input. This is a subtle cue that this is machine-generated text.
- `border-t-2 border-amber-400/20` on the `bg-raised` block

Edit mode:
- Textarea replaces the block — same rounded-md, same padding
- `bg-raised border border-amber-400/40 rounded-md p-4 text-sm text-primary resize-none focus:outline-none focus:ring-2 focus:ring-amber-400/25`
- Below textarea: Save + Cancel buttons inline `gap-2 mt-2`

**Row 4 — metadata footer**:
- Left side: Evidence source chips — `bg-overlay border-border-subtle text-muted text-xs px-2 py-0.5 rounded font-mono` — each chip is a filename
  - Prefix: a 10px SVG file icon inline, `text-muted`
- Right side: Coverage badge + Certainty score — pushed right with `ml-auto`
  - Certainty: `font-mono text-xs` — e.g. `91%` in success green, `62%` in amber, `28%` in red
  - Coverage badge: see Badges section

**Row 5 — suggested addition hint** (conditional):
- `mt-3 bg-[#0c1a2e] border border-[#1e40af]/50 rounded-md px-3 py-2`
- Left: a 10px SVG lightbulb icon, `text-[#60a5fa]`
- Text: `text-xs text-[#60a5fa]` — the suggestion text
- This block should feel informational, not urgent

**Certainty reason** (when low):
- `text-xs text-muted italic mt-2` — kept very quiet, just context

---

### 2.6 Filter Tabs (Review screen)

Not pill buttons. A **tab bar with underline indicator**, like Linear's sidebar filters.

**Design**:
- Container: `flex gap-0 border-b border-subtle mb-6`
- Each tab: `px-4 py-2.5 text-sm font-medium relative cursor-pointer transition-colors`
  - Default: `text-muted hover:text-secondary`
  - Active: `text-primary`
  - Active underline: a `2px` bottom border `border-b-2 border-amber-400` — positioned absolute at the bottom of the tab
- Count in tab label: `text-xs ml-1` in same color as label, or use a `bg-overlay rounded px-1 text-muted` chip for counts

**Tab items** (no emoji):
- `All  12`
- `Ready  8`
- `Review  3`
- `Gaps  1`

The count is separated from the label by a space and shown in a slightly dimmer shade, not bold.

---

### 2.7 Export Screen

Not a centered card with a big emoji. More like a **completion report** — structured, clear, with a hint of "you did the thing."

**Layout**: max-w-2xl, centered, py-12

**Top section — result summary**:
- Heading: DM Serif Display, `text-3xl text-primary` — see copy
- Subtext: `text-sm text-secondary mt-1`

**Stats row**: Three metric blocks side by side, horizontally centered, separated by 1px `bg-border-subtle` vertical dividers. Each block:
- Number: `text-2xl font-bold font-mono` in semantic color (green for approved, neutral for total, red for gaps)
- Label: `text-xs text-muted uppercase tracking-wider mt-0.5`

**Warning callout** (if flagged questions exist):
- `bg-[#2d1a00] border border-[#92400e]/60 rounded-lg px-4 py-3 mt-6 text-sm text-[#fbbf24]`
- Left: a 14px SVG warning triangle icon
- Text: see copy section

**Download buttons**:
- Stacked vertically, `max-w-xs mx-auto mt-8 flex flex-col gap-3`
- Excel: primary button style (amber — see Buttons). Icon: a 14px SVG table/grid icon (not ⬇)
- PDF: secondary button style. Icon: a 14px SVG file-text icon
- Back to Review: ghost, `text-muted hover:text-secondary`, `← Back` — not verbose

**Bottom**: `text-xs text-muted text-center mt-10` — "Session data cleared when you close this tab."

---

### 2.8 Badges

A consistent, emoji-free badge system. All badges use the same height (`h-5`, `text-xs`, `px-2`, `rounded`) for optical alignment.

#### Coverage badges

| State       | Background      | Text       | Label          | Dot color   |
|-------------|-----------------|------------|----------------|-------------|
| Covered     | `#052e16`       | `#4ade80`  | `Covered`      | `#4ade80`   |
| Partial     | `#2d1a00`       | `#fbbf24`  | `Partial`      | `#fbbf24`   |
| No evidence | `#2d0a0a`       | `#f87171`  | `No evidence`  | `#f87171`   |

Structure: `[3px filled dot] [label]` — dot is a `w-1.5 h-1.5 rounded-full inline-block mr-1.5`.

No icon, no emoji. The colored dot carries all the semantic weight.

#### Status badges (card header)

| Status   | Background       | Text       | Label       |
|----------|------------------|------------|-------------|
| Approved | `rgba(74,222,128,0.08)` | `#4ade80` | `APPROVED`  |
| Edited   | `rgba(96,165,250,0.08)` | `#60a5fa` | `EDITED`    |
| Review   | `rgba(251,191,36,0.08)` | `#fbbf24` | `REVIEW`    |

Uppercase label, `font-mono text-[10px] tracking-wide font-semibold` — these should feel like status codes, not friendly tags.

---

### 2.9 Buttons

Four button types. All use `rounded-lg` (8px). All have `font-medium text-sm` text. All transitions `transition-all duration-150`.

#### Primary
```
bg-amber-400 text-[#0d0d0f] rounded-lg px-5 py-2 font-medium text-sm
hover:bg-amber-300
shadow: 0 0 0 1px rgba(245,158,11,0.3), 0 4px 12px rgba(245,158,11,0.15)
focus: ring-2 ring-amber-400/30
disabled: opacity-40 cursor-not-allowed (no bg change)
```

#### Secondary
```
bg-surface border border-mid text-primary rounded-lg px-5 py-2 font-medium text-sm
hover:bg-raised hover:border-strong
focus: ring-2 ring-white/10
```

#### Ghost
```
text-secondary rounded-lg px-3 py-1.5 font-medium text-sm (no bg, no border)
hover:text-primary hover:bg-raised
```

#### Danger
```
bg-[#2d0a0a] border border-[#991b1b]/60 text-[#f87171] rounded-lg px-3 py-1.5 font-medium text-sm
hover:bg-[#3d1010] hover:border-[#b91c1c]
```

#### Saving/loading inline state
When a button triggers an async action, swap label text to `Saving...` and add `opacity-70 pointer-events-none`. No spinner — the text change is enough.

---

## 3. Copy Rewrite

### Voice
Direct. Minimal. Slightly sardonic. A senior engineer who built this for themselves, not a startup writing for a pitch deck.

Rules:
- Never start a sentence with "AI will..." — the AI doing things is assumed
- No "Leverage", "Streamline", "Powerful", "Seamlessly"
- Short headings — 4 words max
- Subtext can have dry humor but must be genuinely useful
- Error messages tell you what to do, not just what went wrong

---

### Nav
- Wordmark: `seques` (lowercase, always)
- CTA: `+ New` — not "New Questionnaire"

---

### Step Indicator Labels
`Upload` → `Processing` → `Review` → `Export`

---

### Upload Screen

**Heading**: "Drop in your evidence."

**Subtext**: "Seques reads your compliance docs and drafts every answer. You review and ship."

**Compliance docs zone**:
- Default label: "SOC 2, ISO 27001, policies — PDF or Word"
- Default hint: "Drop files here or browse"
- Drag-over: "Drop to add"
- File added: "{n} doc{s} loaded" (inside zone, above file list)

**Questionnaire zone**:
- Default label: "The prospect's questionnaire"
- Default hint: "PDF, Excel, or paste questions below"
- Drag-over: "Drop to load"
- File added: file name + size — no label needed

**Paste textarea placeholder**:
```
1. Do you have MFA enforced for all users?
2. How is data encrypted at rest?
3. Do you hold a current SOC 2 Type II report?
```
(Unchanged — it's a concrete example, not branding copy)

**Model selector label**: `via` (lowercase, before the buttons)

**Status text** (bottom left):
- 0 docs: "Add evidence docs to continue."
- 1+ docs, no questionnaire: "{n} doc{s} ready — now add their questionnaire."
- Ready: "{n} doc{s} + questionnaire loaded."

**CTA button**:
- Ready: `Run it →`
- Loading: `Starting...`
- Disabled: `Run it →` (just dimmed — no text change)

**Error**:
> Something went wrong — is the backend running? (`{error}`)

---

### Processing Screen

**Terminal header** (above the panel): No separate heading — the terminal is self-explanatory.

**Log lines** (these are generated by the UI based on API status, not the backend):
```
{time}  ✓  Docs parsed
{time}  ✓  {n} questions extracted
{time}  ▶  Answering {processed} of {total}...
```

When done:
```
{time}  ✓  Done. {total} answers drafted.
```

**Below terminal**: "Usually 1–3 min. Depends on questionnaire size."

**Error state** (appended to log):
```
{time}  ✗  Failed — {error}
```
Below panel: `Something broke. [Try again →]` — "Try again" is a ghost button that calls `window.location.reload()` or triggers parent reset.

---

### Review Screen

**Heading**: "Review & approve." — not "Review Answers"

**Subtext** (inline stats):
`{total} questions · {ready} ready · {review} need a look · {gaps} gaps`

(Replace "·" dots with actual middot `·` or em-dash separators — the colored inline spans are fine to keep but remove the emoji-colored labels)

**Filter tabs**:
- `All  {total}`
- `Ready  {ready}`
- `Review  {review}`
- `Gaps  {gaps}`

**Empty state** (no questions in filter):
> "Nothing here. {filter === 'gaps' ? 'That's good.' : 'Check a different filter.'}"

Specifically:
- All empty: "Nothing to review. Something's off."
- Ready empty: "No ready answers yet — might need more docs."
- Review empty: "No flagged answers. You're in good shape."
- Gaps empty: "No gaps found. Either your docs are thorough or the questions were easy."

**Approve button label**: `Approve` (no emoji)

**Edit / Save / Cancel**: unchanged labels — they're self-evident

**Suggested addition hint text**: unchanged — this is AI-generated, not UI copy

**Export CTA** (top right):
- `{approved}/{total} approved`
- Button: `Export →`

---

### Export Screen

**Heading**: "Done. Export your response."

OR, if there are gaps: "Almost. Check your gaps."

**Subtext**:
- No gaps: "Everything's drafted. Download and send."
- Gaps > 0: "{gaps} question{s} couldn't be answered from your docs. Export anyway or go back."

**Stats labels** (below numbers):
- approved → `approved`
- total → `total questions`
- gaps → `gaps`

**Warning callout** (if flagged > 0):
> "{flagged} answer{s} not approved yet — exported as drafted. Review them before sending."

**Gaps callout** (if gaps > 0):
> "{gaps} question{s} have no evidence. They'll export as blank. Consider adding a note or uploading more docs."

**Buttons**:
- Excel: `Download Excel`
- PDF: `Download PDF`
- Back: `← Back to review`

**Bottom note**: "Your session data stays until you close this tab."

---

## 4. Google Fonts to Install

Add to `<head>` in `/Users/samrattalukder/Documents/projvtwo/seques/frontend/index.html`:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=DM+Serif+Display&family=JetBrains+Mono:wght@400;500&display=swap"
  rel="stylesheet"
/>
```

Font names for reference:
- `Inter` — 400, 500, 600, 700
- `DM Serif Display` — 400
- `JetBrains Mono` — 400, 500

---

## 5. Tailwind Config Additions

Replace the contents of `/Users/samrattalukder/Documents/projvtwo/seques/frontend/tailwind.config.js` with:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['"DM Serif Display"', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'Menlo', 'monospace'],
      },
      colors: {
        // Background layers
        base: '#0d0d0f',
        surface: '#141416',
        raised: '#1c1c20',
        overlay: '#242428',
        // Accent
        accent: {
          DEFAULT: '#f59e0b',
          dim: '#92400e',
        },
        // Text
        primary: '#f0ede8',
        secondary: '#9b9691',
        muted: '#5a5753',
        // Semantic
        success: {
          bg: '#052e16',
          text: '#4ade80',
          border: '#166534',
        },
        warning: {
          bg: '#2d1a00',
          text: '#fbbf24',
          border: '#92400e',
        },
        danger: {
          bg: '#2d0a0a',
          text: '#f87171',
          border: '#991b1b',
        },
        info: {
          bg: '#0c1a2e',
          text: '#60a5fa',
          border: '#1e40af',
        },
      },
      borderColor: {
        subtle: 'rgba(255,255,255,0.06)',
        mid: 'rgba(255,255,255,0.12)',
        strong: 'rgba(255,255,255,0.20)',
      },
      borderWidth: {
        3: '3px',
      },
      boxShadow: {
        card: '0 1px 2px rgba(0,0,0,0.5)',
        'card-hover': '0 4px 16px rgba(0,0,0,0.4)',
        'btn-primary':
          '0 0 0 1px rgba(245,158,11,0.3), 0 4px 12px rgba(245,158,11,0.15)',
        'input-focus': '0 0 0 2px rgba(245,158,11,0.25)',
        'glow-success': '0 0 0 1px rgba(74,222,128,0.2)',
      },
      backgroundImage: {
        'dot-grid':
          'radial-gradient(circle, rgba(255,255,255,0.04) 1px, transparent 1px)',
      },
      backgroundSize: {
        'dot-grid': '20px 20px',
      },
      animation: {
        'cursor-blink': 'blink 1s step-end infinite',
        'fade-in': 'fadeIn 150ms ease-out',
      },
      keyframes: {
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(4px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
```

---

## 6. Implementation Order

This is the minimal ordered change list. Each step is atomic and testable. Later steps build on earlier ones — do not reorder.

### Step 1 — Fonts and CSS baseline
**File**: `/Users/samrattalukder/Documents/projvtwo/seques/frontend/index.html`

Add the three Google Fonts `<link>` tags to `<head>`. This has zero visual side-effects until Tailwind config is updated.

---

### Step 2 — Tailwind config
**File**: `/Users/samrattalukder/Documents/projvtwo/seques/frontend/tailwind.config.js`

Apply the full config from section 5. This unlocks all the custom tokens. Now custom classes like `bg-base`, `text-primary`, `font-serif`, `shadow-btn-primary` are available everywhere.

---

### Step 3 — Global base styles
**File**: `/Users/samrattalukder/Documents/projvtwo/seques/frontend/src/index.css`

Replace contents with:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html {
    background-color: #0d0d0f;
    color: #f0ede8;
    font-family: 'Inter', system-ui, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  * {
    box-sizing: border-box;
  }

  /* Scrollbar — dark, minimal */
  ::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  ::-webkit-scrollbar-track {
    background: transparent;
  }
  ::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.12);
    border-radius: 3px;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: rgba(255,255,255,0.2);
  }
}
```

At this point the app turns dark everywhere even without touching any JSX.

---

### Step 4 — App.jsx (Nav + root layout)
**File**: `/Users/samrattalukder/Documents/projvtwo/seques/frontend/src/App.jsx`

Changes:
- Root div: `bg-base` replaces `bg-slate-50`
- Nav: new height, background, backdrop blur, bottom border using custom tokens
- Wordmark: amber bottom-border accent, Inter 600
- Step indicator component: inline in App.jsx (small enough to not need its own file)
- `+ New` button: ghost style, `+ New` text

The step indicator can be a small inline component:
```jsx
function StepIndicator({ current }) {
  const steps = ['upload', 'processing', 'review', 'export']
  const labels = ['Upload', 'Processing', 'Review', 'Export']
  return (
    <div className="hidden sm:flex items-center gap-2">
      {steps.map((step, i) => {
        const idx = steps.indexOf(current)
        const isDone = i < idx
        const isActive = i === idx
        return (
          <div key={step} className="flex items-center gap-2">
            {i > 0 && <div className="w-6 h-px bg-white/[0.06]" />}
            <span
              className={`text-xs font-medium font-sans transition-colors ${
                isActive ? 'text-amber-400' : isDone ? 'text-secondary' : 'text-muted'
              }`}
            >
              {isActive ? '●' : isDone ? '✓' : '○'} {labels[i]}
            </span>
          </div>
        )
      })}
    </div>
  )
}
```

---

### Step 5 — Upload.jsx
**File**: `/Users/samrattalukder/Documents/projvtwo/seques/frontend/src/screens/Upload.jsx`

Full visual overhaul per section 2.3. Key changes in order:
1. Outer div: `max-w-3xl`
2. H1: add `font-serif text-3xl`, change copy
3. Subtext: new copy, `text-secondary`
4. Drop zones: swap `bg-white border-dashed border-slate-300` for `bg-surface bg-dot-grid bg-dot-grid-size border border-subtle` approach. Use a style prop for background-size alongside the Tailwind class.
5. Drag-over state: `border-amber-400/50 bg-[rgba(245,158,11,0.05)]`
6. Remove emoji icons: replace `📋` with an inline SVG (see below)
7. File rows: `bg-raised` pill with SVG X button
8. Provider selector: amber border on selected, ghost on default
9. CTA button: amber primary style
10. Status text: new copy

**SVG icons to use** (inline, no icon library required — these are tiny enough):

File icon (for doc zones):
```svg
<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
  <polyline points="14 2 14 8 20 8"/>
</svg>
```

Spreadsheet icon (for questionnaire zone):
```svg
<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
  <rect x="3" y="3" width="18" height="18" rx="2"/>
  <line x1="3" y1="9" x2="21" y2="9"/>
  <line x1="3" y1="15" x2="21" y2="15"/>
  <line x1="9" y1="9" x2="9" y2="21"/>
</svg>
```

X / remove icon (14px, inline with file row):
```svg
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
  <line x1="18" y1="6" x2="6" y2="18"/>
  <line x1="6" y1="6" x2="18" y2="18"/>
</svg>
```

---

### Step 6 — Processing.jsx
**File**: `/Users/samrattalukder/Documents/projvtwo/seques/frontend/src/screens/Processing.jsx`

Replace `ProgressBar` component and layout entirely with the terminal widget concept from section 2.4.

Key implementation notes:
- Log lines are stored in `useState([])` and appended reactively as `status` changes
- Each line: `{ time: string, glyph: '▶'|'✓'|'✗', text: string, tag?: string }`
- Lines render with `animate-fade-in` on mount (Tailwind custom animation from config)
- Active line `▶` glyph: wrap in `<span className="text-amber-400 animate-pulse">`
- Blinking cursor `▋` after last line: `<span className="animate-cursor-blink text-amber-400">`
- Terminal chrome bar: three colored SVG circles (or just `w-2.5 h-2.5 rounded-full` divs in red/yellow/green) — do NOT use `#ff5f57 #ffbd2e #27c93f` as interactive — they're purely decorative
- Remove the `ProgressBar` function entirely

---

### Step 7 — QuestionCard.jsx
**File**: `/Users/samrattalukder/Documents/projvtwo/seques/frontend/src/components/QuestionCard.jsx`

Per section 2.5:
1. Card container: `bg-surface rounded-xl border border-subtle border-l-3 p-5` with dynamic `border-l-*` color
2. Replace `COVERAGE` emoji map with dot-based badge objects (no emoji)
3. Status badges: update pill styles to use semantic bg/text tokens from section 2.8
4. Buttons: Edit → ghost style, Approve → small secondary (not green filled)
5. Answer block: `bg-raised border-t-2 border-amber-400/20 rounded-md p-4`
6. Edit textarea: amber focus ring style
7. Evidence sources: file SVG icon + `font-mono` chips
8. Certainty: `font-mono text-xs` in semantic color — remove the emoji `📄`
9. Suggested addition: info box style from section 2.5
10. Remove all emoji references from JSX

---

### Step 8 — Review.jsx
**File**: `/Users/samrattalukder/Documents/projvtwo/seques/frontend/src/screens/Review.jsx`

1. Heading: new copy, DM Serif Display
2. Subtext stats: new copy, remove color-coded inline spans (or keep but desaturate to `text-secondary`)
3. Export button: amber primary style
4. Filter tabs: replace button pills with underline tab design from section 2.6
5. Tab labels: remove emoji, update to plain text + count
6. Empty state: per-filter copy from section 3
7. Card gap: `space-y-3` instead of `space-y-4` (tighter)

---

### Step 9 — Export.jsx
**File**: `/Users/samrattalukder/Documents/projvtwo/seques/frontend/src/screens/Export.jsx`

1. Remove the `📤` emoji entirely — no replacement icon needed; the heading carries it
2. Container: not a centered white card — use `max-w-2xl mx-auto px-6 py-12` with no card wrapper (content floats on dark bg)
3. Heading: DM Serif Display, new copy
4. Stats row: styled per section 2.7
5. Warning/gap callouts: semantic callout boxes (amber and red variants)
6. Download buttons: Excel → amber primary, PDF → secondary, Back → ghost
7. Bottom note: `text-xs text-muted text-center mt-10`

---

### Step 10 — Final pass
Audit all files for any remaining:
- `bg-white` → `bg-surface` or `bg-raised`
- `bg-slate-*` → custom tokens
- `text-slate-*` → `text-primary`, `text-secondary`, or `text-muted`
- `border-slate-*` → `border-subtle`, `border-mid`, `border-strong`
- `bg-blue-*` buttons → amber primary or secondary styles
- `bg-green-*` approve buttons → secondary style (the left border accent carries the green signal)
- Any remaining emoji characters in JSX (grep for Unicode ranges `\u2600`-`\u27BF` and `\u{1F300}`-`\u{1FFFF}`)

Run: `grep -rn "emoji\|📋\|📝\|📤\|✅\|⚠️\|🟢\|🟡\|🔴\|📄\|💡\|⬇" src/`

After clean, do a visual pass in both viewport sizes (mobile 375px, desktop 1280px) focusing on:
- Nav step indicator wrapping
- Drop zones on mobile (should stack, full width)
- QuestionCard metadata row wrapping (evidence chips + badges + certainty)
- Export stats row on narrow screens

---

## Design Decisions Log

The following choices were made deliberately and should not be revisited without good reason:

| Decision | Rationale |
|----------|-----------|
| Amber accent, not violet or emerald | Amber reads as "signal" in a security context (warning lights, status LEDs). Violet is overused in dev tooling (Linear, Prisma, etc). Emerald is too friendly for a tool dealing with compliance gaps. |
| DM Serif Display only for H1s | More than one serif heading per screen breaks the effect. It should feel like a deliberate editorial mark, not a font choice applied everywhere. |
| No progress bars on Processing | Progress bars are fine, but they have no personality and they lie (0% to 100% in ways that don't map to real time). The log-stream terminal widget maps to how the backend actually works — sequential steps — and signals technical precision. |
| Left border accent on cards, not colored bg | Full colored card backgrounds (green for approved, amber for review) create visual noise at scale when reviewing 20+ cards. A 3px left accent carries the status with much less cognitive weight. |
| No external icon library | The 4-5 SVG icons used are simple enough to inline. Adding heroicons or lucide-react for 5 icons is unnecessary dependency weight. |
| `border-l-3` (custom 3px) instead of `border-l-4` | Tailwind's `border-l-4` is 4px which is slightly too chunky. 3px is the visual sweet spot for a status accent without dominating the card. |
| No card shadows in default state | Dark backgrounds make box-shadows look muddy. Surface layering (`bg-base` → `bg-surface` → `bg-raised`) creates depth without needing shadows. Shadows are reserved for hover states and the primary button. |
