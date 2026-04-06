# scissors — Improvement TODOs

## Recent Wins
- [x] **Cycle 94: LLM objective wiring (+8.4%)** — Cyborg parity: LLM objective now affects pressure budgets
- [x] **Cycle 91: Junction AOE 10→20 (+1.5%)** — Alpha.0 parity: wider enemy detection for better survival
- [x] **Cycle 89: Scout HP 30→25 (+5.0%)** — Retreat optimization success (unlike scrambler)
- [x] **Cycle 87: Miner HP 15→12 (+3.2%)** — Continued retreat optimization pattern

## Next Candidates
- [ ] LLM stagnation detection enhancement: explicitly detect oscillation/stuck and suggest role changes
- [ ] Hotspot tracking: like alpha.0, track scramble events per junction to avoid repeatedly targeted junctions
- [ ] Read teammate vibes for coordination
- [ ] Explore non-HP parameters: junction scoring weights, claim penalties, etc.

## Completed
- [x] Hotspot tracking implemented
- [x] Wider enemy AOE for retreat (JUNCTION_AOE_RANGE 10→20) — IMPROVED!
- [x] RETREAT_MARGIN 15→20 tested and reverted
- [x] Aligner HP threshold optimization
- [x] Miner HP threshold optimization
- [x] Scrambler HP threshold 30→25 tested and reverted
- [x] Scout HP threshold optimization
- [x] LLM stagnation detection enhancement tested and reverted
- [x] Network bonus weight 0.5→1.0 tested and reverted
- [x] Late-game HP modifiers reduction tested and reverted
