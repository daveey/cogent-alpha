---
name: coach.dashboard
description: Generate an HTML training dashboard showing experiment history, score graphs, learnings, and TODOs. Opens in browser. Use when asked for "dashboard", "training status", "coach dashboard", or "show progress".
---

# Coach Dashboard

Generate a self-contained HTML dashboard from `.coach/` state and open it in the browser.

## Steps

1. **Read all coach state**:
   - `.coach/state.json` — current scores, rank, sessions
   - `.coach/todos.md` — TODOs and dead ends
   - `.coach/session_config.md` — policy name, season
   - Scan `.coach/sessions/*/log.md` — all session logs

2. **Extract experiment timeline** from session logs:
   - For each session: timestamp, what was tried, result (improved/regressed/neutral), score
   - Build a list of `{session, change, result, score, signals}`

3. **Generate HTML dashboard** using the visual-explainer skill patterns:
   - **Hero KPIs**: current rank, best score, total sessions, tournament status
   - **Score chart**: line chart (Chart.js) showing score progression over sessions
   - **Experiment log**: table of all sessions with change description, result badge (green/red/neutral), score delta
   - **Beliefs & learnings**: key insights extracted from session logs (what works, what doesn't)
   - **Dead ends**: list from todos.md with strikethrough
   - **Active TODOs**: current priorities from todos.md
   - **PCO signals**: latest loss signal magnitudes (resource, junction, survival)

4. **Write to** `~/.agent/diagrams/coach-dashboard.html`

5. **Open in browser**: `open ~/.agent/diagrams/coach-dashboard.html`

## Design

Use the Catppuccin Mocha palette (dark-first). Chart.js via CDN for the score graph. Staggered fade-in animations. Responsive grid layout. Both light and dark themes.
