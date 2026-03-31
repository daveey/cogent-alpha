# Session 40 Log

**Timestamp**: 2026-03-31 17:05:00
**Approach**: IntelligentDesign

## Status: WAITING

Submitted beta:v60 (freeplay) and beta:v61 (tournament). Awaiting results.

## Analysis
- Tournament: beta:v7 rank #1 (10.00), tied with alpha.0:v891
- Freeplay: beta:v15 best at 1.81, alpha.0:v716 at 15.05 (8x gap)
- Freeplay scores declining from v15 (1.81) to v55 (1.57)
- Identified teammate penalty (10.0) added in v26 as regression candidate

## Change
Removed teammate_penalty (10.0) from aligner_target_score in helpers/targeting.py.

Rationale:
- Added after v15 (our freeplay best), coincides with freeplay decline
- In freeplay, teammates are from OTHER policies — the penalty avoids good junctions based on false coordination signals
- The claim system (12.0 penalty, 30-step expiry) already prevents duplicate targeting for same-policy agents
- Self-play and freeplay are weakly correlated, so self-play coordination loss is acceptable

## Test Results (Self-Play)
| Seed | Baseline | Modified | Diff |
|------|----------|----------|------|
| 42 | 2.05 | 0.78 | -1.27 |
| 43 | 2.53 | 2.53 | 0.00 |
| 44 | 1.04 | 0.89 | -0.15 |
| 45 | 2.53 | 1.68 | -0.85 |
| 46 | 1.47 | 3.39 | +1.92 |
| **Avg** | **1.92** | **1.85** | **-0.07 (-3.6%)** |

Self-play neutral (within documented variance range of 0.00-12.03).

## Submissions
- Freeplay: beta:v60 (beta-cvc)
- Tournament: beta:v61 (beta-teams-tiny-fixed)

## Key Discovery
SDK constants differ from IMPROVE.md documentation:
- JUNCTION_ALIGN_DISTANCE = 15 (doc says 3)
- JUNCTION_AOE_RANGE = 10 (doc says 4)
Code uses SDK values correctly, docs just outdated.
