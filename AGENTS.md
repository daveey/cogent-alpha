# AGENTS.md

Instructions for AI agents working with this repository.

## Cogent Lifecycle

On startup, read and follow `cogent/hooks/on-wake.md`.
At session end, read and follow `cogent/hooks/on-sleep.md`.

## Skills

Skills are in `cogent/skills/`. Read the SKILL.md file and follow its instructions.

- **improve** — One improvement iteration: analyze code, implement a change, test across seeds, auto-submit if improved.
- **proximal-cogent-optimize** — PCO cycle: play a game, collect experience, LLM proposes patches, test, submit.
- **dashboard** — Generate HTML dashboard from cogent state showing experiments, scores, and learnings.
- **memory-wipe** — Nuclear reset of memory and state. Identity survives.

## Docs

- [docs/coglet.md](docs/coglet.md) — Coglet framework: COG/LET primitives, mixins, runtime
- [docs/architecture.md](docs/architecture.md) — Policy architecture, program table, PCO, alpha.0 reference
- [docs/strategy.md](docs/strategy.md) — What works, what to try, dead ends, learnings
- [docs/rules.md](docs/rules.md) — Game rules, constants, team coordination
- [docs/cogames.md](docs/cogames.md) — CLI setup, running, uploading, monitoring
- [docs/tools.md](docs/tools.md) — Development rules & constraints
