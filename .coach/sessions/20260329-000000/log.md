# Session 001 Log

## 2026-03-29 00:00 — Session Start
First coaching session. No prior results. Establishing baseline.

## Step 1: Local Baseline
3-episode baseline (seed 42): 2.17, 2.74, 0.60 → avg **1.84**

## Step 2: Improvement Attempts
1. Removed `_pressure_budgets` override (use base resource-aware logic): avg 1.82 — no improvement
2. Reduced heart retreat margin (2 per heart vs 5): avg 1.71 — slightly worse
3. Capped heart_batch_target at 4: avg 1.84 — no improvement
4. **Doubled scramblers (3 aligners + 2 scramblers from step 100)**: avg **5.67** (episodes: 1.76, 13.89, 1.35) — 3x improvement!

## Step 3: Analysis
- Scramblers neutralized 68.88 junctions per agent (vs 7.5 baseline)
- Team aligned 102 junctions (vs 67 baseline)
- Enemy junctions lost 183.67 (vs 60 baseline)
- Deaths reduced to 6.62 (vs 8.25 baseline)
- Resource mining increased dramatically

Key insight: With only 1 scrambler, enemy junctions in AoE range flip our junctions back. 2 scramblers effectively protect our alignment network.

## Step 4: Commit & Submit
Committing change to `cogames/cvc/agent/coglet_policy.py` — doubled scrambler allocation.
Committed and pushed to `claude/implement-coach-command-dTPMM`.
Uploaded to tournament as **coglet-v0:v11** (qualifying pool).

**WAITING**: submitted, checking results next session.
