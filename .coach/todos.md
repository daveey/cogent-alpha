# Coach TODO

## Current Priorities
- [ ] Check tournament results for coglet-v0:v11 and compare with previous versions
- [ ] Analyze match logs against specific opponents to identify weaknesses

## Improvement Ideas
- [ ] Tune scrambler vs aligner ratio further (try 2 aligners + 3 scramblers)
- [ ] Make pressure budgets resource-aware (reduce when resources critically low)
- [ ] Reduce late-game heart batch targets (currently escalates to 6, try capping at 4)
- [ ] Investigate high death count (8.25 per agent) — improve retreat timing
- [ ] Try adaptive scrambler count based on enemy junction presence
- [ ] Optimize aligner target scoring — current hub_penalty may be too aggressive for far junctions
- [ ] Reduce early game hub camping (steps 1-20 healing wait)

## Done
- [x] Establish baseline scores (avg 1.84 local, 3-episode seed 42)
- [x] Double scrambler allocation (1→2) — 3x local improvement (avg 5.67)
