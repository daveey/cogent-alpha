# Session 50 Log

**Timestamp**: 2026-04-01 04:45:00
**Approach**: IntelligentDesign

## Status: WAITING

Submitted beta:v86 (freeplay) and beta:v87 (tournament).

## Tournament Update
- Stage 2 at 68.3% complete (243 matches), 16 policies remaining
- Our improved versions scored 8.84 in stage 1 (best)

## Change
Reduced stall detection threshold from 12→8 steps in both main.py and targeting.py.
Agents that get stuck on walls now unstick 4 steps sooner.

## Test Results (Self-Play)

| Seed | Previous | Unstick8 | Diff |
|------|----------|----------|------|
| 42 | 1.06 | 1.79 | +0.73 |
| 43 | 2.55 | 2.16 | -0.39 |
| 44 | 0.92 | 1.19 | +0.27 |
| 45 | 1.40 | 1.36 | -0.04 |
| 46 | 1.98 | 1.90 | -0.08 |
| 47 | 2.06 | 1.79 | -0.27 |
| 48 | 1.73 | 1.56 | -0.17 |
| **Avg** | **1.67** | **1.68** | **+0.01 (+0.4%)** |

Average neutral but **variance halved** (1.63→0.97) and **min improved** (0.92→1.19).
No zero seeds. Faster unstick = more consistent performance.

## Submissions
- Freeplay: beta:v86 (beta-cvc)
- Tournament: beta:v87 (beta-teams-tiny-fixed)
