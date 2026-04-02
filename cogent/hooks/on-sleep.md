# On Sleep

Persist everything and shut down cleanly.

## Steps

1. **Write session log** — If any improvement work was done this session, write a session log to `cogent/memory/sessions/YYYYMMDD-NNN.md` following the format in `cogent/MEMORY.md`. Skip if no improvement work was done.

2. **Update learnings** — If anything surprising or non-obvious was discovered, append to `cogent/memory/learnings.md`.

3. **Update todos** — Refresh `cogent/todos.md` with current priorities. Mark completed items, add new ones discovered this session.

4. **Update state** — Write current `approach_stats` to `cogent/state.json`.

5. **Fold stale learnings** — If any entries in `learnings.md` have already been incorporated into `docs/strategy.md`, remove them.

6. **Summarize if needed** — If there are 5+ session logs without a covering summary, write one to `cogent/memory/summaries/weekly-YYYYMMDD.md` and clean up old session logs per `cogent/MEMORY.md` cleanup rules.

7. **Commit and push**:
   ```bash
   git add cogent/
   git commit -m "cogent sleep: persist session state"
   git push
   ```

8. **Say goodnight** — Brief sign-off as the cogent (use the name and personality from `cogent/IDENTITY.md`).
