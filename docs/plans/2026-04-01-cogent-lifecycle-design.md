# Cogent Lifecycle & Onboarding Design

## Overview

All cogent state, lifecycle hooks, and skills live in a single visible `cogent/` directory at the repo root. Lifecycle hooks are markdown instructions the LLM follows at the right moments. Skills are markdown instructions read on demand. No plugins, no Claude Code skill registration, no hidden directories.

## Directory Structure

```
cogent/
├── hooks/
│   ├── on-create.md        # Onboarding (runs on user's local Claude)
│   ├── on-wake.md          # Boot / session start (runs on the cogent)
│   └── on-sleep.md         # Shutdown (runs on the cogent)
├── skills/
│   ├── improve/SKILL.md
│   ├── dashboard/SKILL.md
│   └── proximal-cogent-optimize/SKILL.md
├── IDENTITY.md             # Name, archetype, motto, doctrine
├── INTENTION.md            # Overarching goal
├── state.json              # Approach stats (PCO vs design attempts/improvements)
├── todos.md                # Priorities and improvement candidates
└── memory/
    ├── learnings.md        # Running insights from play
    ├── sessions/           # Per-session logs (YYYYMMDD-NNN.md)
    └── summaries/          # Compressed session summaries
```

## Hooks

Lifecycle hooks are markdown files containing instructions the LLM reads and follows. They are not registered with Claude Code's skill system. The cogent's `AGENTS.md` tells the LLM when to read them.

| Hook | Runs where | When | Purpose |
|------|-----------|------|---------|
| `on-create.md` | User's local Claude | Once, during onboarding | Fork, name, identity, launch, verify |
| `on-wake.md` | On the cogent | Every boot / session start | Restore state, check standing, report status |
| `on-sleep.md` | On the cogent | Session end / shutdown | Persist state, write logs, commit, push |

## Skills

Skills live in `cogent/skills/` and are read by the LLM when directed by `on-wake.md` or the user. They are not registered as Claude Code slash commands.

| Skill | Purpose |
|-------|---------|
| `improve` | One iteration: analyze code, implement change, test across seeds, auto-submit if improved |
| `proximal-cogent-optimize` | PCO cycle: play game, collect experience, LLM proposes patches, test, submit |
| `dashboard` | Generate HTML training dashboard from cogent state |

## Onboarding Flow (`on-create.md`)

Runs on the **user's local Claude Code**. Triggered by pasting `play.md` (hosted on softmax.com), which fetches `cogent/hooks/on-create.md` from `metta-ai/cogamer` via raw GitHub URL.

### Step 1 — Name (RPG character creation)

Generate 6-8 random handle-style names (lowercase, hyphens, sci-fi/Culture ship inspired). User picks one or writes their own.

### Step 2 — Archetype

Choose a play style: Strategist, Berserker, Trickster, Guardian, Explorer, or custom. Expanded into 2-3 sentences for the personality section.

### Step 3 — Motto

Generate 4 archetype-themed battle cries. User picks one or writes their own.

### Step 4 — Doctrine

Choose an approach: "Rush early, scale late", "Adapt to everything", "Economy first", "Pressure never stops", "Evolving", or custom.

### Step 5 — Launch

```bash
cogent <name> create
```

This command (from `metta-ai/cogent` CLI):
- Forks `metta-ai/cogamer` to `<user>/cogent-<name>` (private)
- Generates ed25519 deploy key, adds to repo, stores as `GIT_SSH_KEY` secret
- Uploads user's SSH public key
- Creates cogent record in control plane DB
- Launches ECS Fargate task

### Step 6 — Identity

Clone the fork locally. Write `cogent/IDENTITY.md` with the chosen name, archetype, motto, and doctrine. Commit and push.

### Step 7 — Verify

Poll `cogent <name> status` until heartbeat confirms the cogent is alive. Then:

```bash
cogent <name> send "hello"
```

Wait for a response. Report success to the user.

## Boot Flow (`on-wake.md`)

Runs on the **cogent** at every boot or session start. `AGENTS.md` tells the LLM: "read `cogent/hooks/on-wake.md` and follow it."

1. Read `cogent/IDENTITY.md` — name, archetype, motto, doctrine
2. Read `cogent/INTENTION.md` — overarching goal
3. Read `cogent/memory/` — recent session logs, learnings, summaries
4. Read `cogent/state.json` — approach statistics
5. Read `cogent/todos.md` — current priorities
6. Check tournament standing (leaderboard commands)
7. Report status: identity, last session, scores/ranking, priorities, recommended action
8. Wait for direction (don't auto-improve)

## Shutdown Flow (`on-sleep.md`)

Runs on the **cogent** at session end or shutdown signal.

1. Write session log to `cogent/memory/sessions/YYYYMMDD-NNN.md`
2. Update `cogent/memory/learnings.md` with new insights
3. Update `cogent/todos.md` with current priorities
4. Update `cogent/state.json` with approach stats
5. Fold learnings already captured in `docs/strategy.md`
6. Write summaries if 5+ session logs exist
7. `git add cogent/ && git commit && git push`
8. Graceful sign-off

## Entry Point: `play.md`

Hosted on `softmax.com`. Minimal content the user pastes into their local Claude Code:

```markdown
# Play CoGames

Fetch and run the cogamer setup skill:
https://raw.githubusercontent.com/metta-ai/cogamer/main/cogent/hooks/on-create.md
```

Claude fetches the raw markdown from GitHub and follows the instructions directly. No repo clone needed at this stage.

## Cogent Boot Sequence (platform level)

1. ECS task starts, entrypoint clones the cogent's fork
2. Secrets injected (deploy key, SSH pubkey, cogames token)
3. MCP server started
4. Claude Code launched
5. `AGENTS.md` tells LLM to read `cogent/hooks/on-wake.md`
6. Cogent is alive and reporting status

## Changes Required

### In `metta-ai/cogamer`

- **Move** `.cogent/*` to `cogent/` (IDENTITY.md, INTENTION.md, state.json, todos.md, memory/)
- **Create** `cogent/hooks/on-create.md` — the onboarding flow
- **Move** existing `/wakeup` skill content to `cogent/hooks/on-wake.md`
- **Move** existing `/sleep` skill content to `cogent/hooks/on-sleep.md`
- **Move** skills (`improve`, `dashboard`, `proximal-cogent-optimize`) from `.claude/skills/` to `cogent/skills/`
- **Update** `AGENTS.md` — reference `cogent/hooks/on-wake.md` instead of `/wakeup` skill
- **Remove** `.cogent/` directory and old skill locations

### In `metta-ai/cogent` (platform)

- No changes needed — `cogent create` already handles fork, keys, launch

### On `softmax.com`

- Host `play.md` at a public URL
