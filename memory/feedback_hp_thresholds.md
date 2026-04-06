---
name: HP threshold retreat optimization pattern
description: Less conservative HP retreat thresholds consistently improve performance by maximizing field time
type: feedback
---

Reduce HP retreat thresholds to allow agents more field time before retreating.

**Why:** Agents were retreating too conservatively, reducing their time on objectives. Cycle 86 (aligner 50→45) showed +41.2% improvement, Cycle 87 (miner 15→12) showed +3.2% improvement. The pattern is validated across multiple roles.

**How to apply:** When optimizing agent behavior, consider HP threshold reductions of 10-20% for each role. Test systematically across all 5 seeds. Prioritize roles with higher base thresholds first, as they have more room for optimization. This approach has 100% success rate so far (2/2 attempts).
