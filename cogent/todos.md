# scissors — Improvement TODOs

## In Progress
- [ ] Network bonus cap 4→5: scissors_v1:v13 qualifying - rewards highly connected junction chains (+84.5% local)

## Current Status (20260405 UTC)
**Tournament Rankings (beta-cvc):**
- 🏆 gamma_v6:v1: rank #5, 17.16 avg (51 matches) - **TOP 5!**
  - Stack: 014 + 015 + 016 + 018 (network_bonus 0.5→0.75)
- scissors_v1:v13: qualifying - network_bonus cap 4→5 (+84.5% local: 4.15→7.66 avg)

**Progress:** Scissors first improvement uploaded!
- Local testing: 7.66 avg (seeds 42-46: 5.72, 8.62, 4.58, 14.93, 4.43)
- Builds on gamma_v6 stack + network_bonus cap increase

**Active Testing:**
- Scissors: network_bonus cap 4→5 in beta-cvc qualifying

## Completed (Design Approach: 8 validated improvements)
- [x] (004) Hotspot penalty increase: 8→12 base - avoid contested far junctions
- [x] (007) Early scrambler: step 100→50 - earlier disruption vs 3 opponents
- [x] (011) Teammate penalty: 6.0→9.0 - better multi-agent coordination
- [x] (014) Enemy AOE penalty: 8.0→10.0 - avoid contested territory
- [x] (015) Scrambler blocked_neutrals: 6.0→8.0 - prioritize expansion-blocking
- [x] (016) Expansion bonus: 5.0→6.0 - aggressive safe territory expansion
- [x] (018) Network bonus: 0.5→0.75 - improved chain-building consolidation
- [x] (network-bonus-cap-5) Network bonus cap: 4→5 - reward highly connected junction chains (+84.5%)

## Candidates
- [ ] Test gamma_scissors:v1 performance once qualifying completes
- [ ] Analyze gamma_v5:v1 match replays for further optimization opportunities
- [ ] Consider stacking corner exploration (017) with expansion stack (014+015+016)
- [ ] Investigate claim duration tuning for far junctions (>30 distance)
- [ ] Read teammate vibes for better coordination
- [ ] Test mixed-policy matches vs alpha.0, dinky, slanky

## Failed Attempts
- [x] (002) LLM prescriptive role-change: -41.6%
- [x] (003) Early pressure ramp (30→15): -5.97%
- [x] (005) Defensive scrambler (remove corner_pressure): -0.77%
- [x] (006) Network bonus 3×: -64.2%
- [x] (008) Scrambler threat_bonus 15.0: -17.04%
- [x] (009) Claim duration 30→20: -53.0%
- [x] (010) Mid-game pressure ramp (3000→2000): -47.13%
- [x] (012) LLM teammate role awareness: +3.8% avg but 40% catastrophic failure
- [x] (010-llm-softer) Softer LLM stagnation: -39.4%
- [x] (017) Corner-safe exploration (22→15 offsets): -62.8%
- [x] (019) Hub penalty reduction (8.0→6.0): -48.6%
- [x] (020) Teammate penalty increase (9.0→10.0): -42.8%
- [x] (021) Hotspot weight base reduction (12.0→11.0): -9.8%
- [x] (022) Hotspot weight mid-tier reduction (6.0→5.5): canceled (built on failed 021)
- [x] (023) Hub penalty mid-tier reduction (3.0→2.7): -29.0%
- [x] (024) Expansion cap increase (36→42): -20.7%
- [x] (025) Enemy AOE range increase (10→12): -39.0%
- [x] (026) Scrambler corner pressure increase (8.0→7.0 divisor): -44.3%
- [x] (027) Target switch threshold reduction (3.0→2.5): -33.3%
- [x] (028) Hotspot cap increase (3→4): -33.8%
- [x] (029-035) Parallel experiments batch: Reverted before validation. Violated "one change per session" principle.
- [x] (119) Revert corner-safe to original exploration offsets: -16.8% (extreme variance)

## Strategy
- **Tournament-based validation** works well - continue using beta-cvc for fast feedback
- **Conservative incremental changes** succeed; aggressive tuning fails
- **Synergistic improvements** (014+015, 016) compound better than isolated changes
- **LLM role suggestions fundamentally flawed** - avoid this approach
- **Expansion vs defense balance critical** - over-indexing either way regresses
- **Parameter tuning exhausted** - 11 consecutive failures (019-028). Current gamma_v6:v1 parameters are optimal for this architecture.

## Next Session
- **CRITICAL**: Parameter tuning has hit a wall. Need architectural improvements:
  - LLM stagnation detection (docs/strategy.md "What To Try")
  - Better junction discovery - agents miss junctions behind walls
  - Read teammate vibes for better coordination
  - PCO evolution - run more epochs
- Current rank: #9 (15.75 avg). Leaders: dinky:v27 at 26.91 (+71% gap)
- Gap suggests architectural differences, not parameter tuning
