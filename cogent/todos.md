# gamma — Improvement TODOs

## In Progress
- [ ] (20260403-016) Expansion bonus increase: 5.0→6.0 per junction (+20%) for aggressive territory control. Uploaded as gamma_v4:v1, awaiting tournament validation.

## Completed
- [x] (20260403-014) Enemy AOE penalty increase: 8.0→10.0 (+25%) → +42.3% improvement (7.45→10.60). Uploaded as gamma_v2:v1, rank #37 on beta-cvc.
- [x] (ID) Wider enemy AOE for retreat: wired _near_enemy_territory (radius 20) into _should_retreat — +458% avg score
- [x] (20260403-001) LLM objective feature: wired up expand/defend/economy_bootstrap objectives to pressure budgets — was broken, now functional
- [x] (20260403-001) Documentation: added four_score.md, updated all docs for multi-team format
- [x] (20260403-004) Hotspot penalty increase: 8→12 base, 5→6 mid → +107.9% on seed 42 (6.03→12.54). Agents avoid contested far junctions in 4-team format.
- [x] (20260403-007) Early scrambler activation: step 100→50 → +7.84% avg (9.03→9.74). Earlier disruption against 3 opponents in 4-team, maintains 50-step resource bootstrap.
- [x] (20260403-011) Teammate penalty increase: 6.0→9.0 → validated via tournament (gamma:v1 rank #46, 9.96 avg). Better coordination in multi-agent scenarios.
- [x] **UPLOADED gamma:v1 to beta-cvc** - includes 004+007+011, running in competitive pool

## Failed Attempts
- [x] (20260403-015-REVERTED) Scrambler expansion-blocking priority: blocked_neutrals 6.0→8.0 (+33%) → -52.0% regression (7.45→3.58). Over-prioritization disrupted targeting balance.
- [x] (20260403-002-REVERTED) LLM stagnation: prescriptive role-change rules → -41.6% regression. Too aggressive switching disrupted stability.
- [x] (20260403-003-REVERTED) Early pressure ramp: 30→15 steps → -5.97% regression. Too early, disrupted resource bootstrapping.
- [x] (20260403-005-REVERTED) Defensive scrambling: removed corner_pressure bonus → -0.77% regression. Minimal impact, offensive push may help in 4-team.
- [x] (20260403-006-REVERTED) Network bonus increase: 0.5→1.5 (3×) → -64.2% regression. Too aggressive clustering, agents failed to expand.
- [x] (20260403-008-REVERTED) Scrambler threat_bonus increase: 10.0→15.0 → -17.04% regression. Over-defending existing junctions hurt expansion disruption.
- [x] (20260403-009-REVERTED) Claim duration reduction: 30→20 steps → -53.0% regression. Too short, caused massive claim duplication and wasted coordination.
- [x] (20260403-010-REVERTED) Mid-game pressure ramp: step 3000→2000 → -47.13% regression. Premature resource burn, exhausted economy before sustainable.
- [x] (20260403-012-REVERTED) Nearby teammate role awareness in LLM: +3.8% avg BUT 40% catastrophic failure rate (variance 22.14). Extreme instability, LLM role suggestions trigger pathological behavior.
- [x] (20260403-010-llm-softer-REVERTED) Softer LLM stagnation detection: detailed guidance + "STRONGLY PREFER null" emphasis → -39.4% regression (5.91 vs 9.74). Verbose prompt with examples performed as badly as prescriptive approach (-41.6%). Both attempts to improve LLM role suggestions have failed catastrophically. Pattern: LLM-driven role changes may be fundamentally flawed.

## Testing Strategy (CPU Constraint Resolved)
- [x] **ADOPTED: Tournament-based validation** - Upload to beta-cvc, analyze match results
  - Matches complete in 5-15 minutes vs 75+ min local testing
  - Real competitive data vs self-play
  - Can iterate much faster
- [ ] ~~Single seed/2-seed/longer cycles~~ - abandoned due to 75+ min timeout with no output
- [ ] ~~GPU access~~ - not needed with tournament validation

## Candidates
- [ ] Read teammate vibes: Count nearby teammate roles to avoid duplicate aligners heading to same area
- [ ] ~~LLM stagnation detection~~ **ABANDONED** - Both prescriptive (-41.6%) and softer (-39.4%) approaches failed. LLM role suggestions appear fundamentally problematic.
- [ ] Teammate vibe awareness in targeting: If teammate vibe shows aligning to nearby junction, deprioritize that junction
- [ ] Test mixed-policy matches (vs alpha.0, corgy) to validate competitive performance
- [ ] Four_score spawn corners: Adjust initial exploration offsets for corner spawns vs center hubs
- [ ] Claim duration: Don't reduce globally - maybe reduce only for far junctions (>30 distance)?
- [ ] Analyze why stalled detection triggers: is threshold too sensitive? Are agents frequently stalling legitimately?

## Blockers
- [x] ~~COGAMES_TOKEN auth: Secret exists in store but not in container environment.~~ **RESOLVED** - Auth now working after container restart
- [ ] **CPU TESTING SPEED: CRITICAL** - 30-50+ min per seed for 32-agent four_score makes rapid iteration impossible. 5-seed validation takes 2.5-4 hours. Need either:
  - GPU access for faster testing
  - Single-seed validation protocol
  - Acceptance of 3-4 hour improvement cycles
  - Alternative test approach (fewer agents, shorter games)
