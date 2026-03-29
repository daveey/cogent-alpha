# Session 001 — Establish Baseline & First Improvement

## Current State
- Best score: none (first session)
- Best version: none
- Total sessions: 0

## Plan
1. Run local scrimmage to establish baseline score
2. Analyze the pressure budget system and early-game role allocation
3. Improve the `_pressure_budgets` override in `coglet_policy.py` to be resource-aware like the base engine, preventing aligners from starving when resources are low
4. Test improvement locally and compare against baseline

## Target Files
- `cogames/cvc/agent/coglet_policy.py` — pressure_budgets override

## Rationale
The current `CogletAgentPolicy._pressure_budgets()` override uses simple step thresholds and ignores resource levels entirely. The base `PressureMixin._pressure_budgets()` adapts budgets based on `team_min_resource` and `team_can_refill_hearts`. When resources are low, the override keeps 5 aligners running even though they can't get hearts or gear, wasting steps. Making the override resource-aware should improve efficiency.
