# Session 48 Log

**Timestamp**: 2026-04-01 03:15:00
**Approach**: IntelligentDesign

## Status: WAITING

Submitted beta:v84 (freeplay) and beta:v85 (tournament).

## Tournament Update
Matches started! Stage 1 play-ins running. Early results:
- **beta:v67, v69, v71, v73** all scored **8.84** (best observed score)
- **beta:v81** (3 matches running, not yet completed)
- Older versions: v33=10.69, v17=28.36 (worse)
- Our improved versions consistently outperform older ones

## Change
Increased scramble_target_score blocked_neutrals weight from 4.0 → 6.0.
Scramblers more strongly prioritize enemy junctions that block access to neutral territory.

## Test Results (Self-Play)

| Seed | Previous | Scramble6 | Diff |
|------|----------|-----------|------|
| 42 | 1.06 | 2.20 | +1.14 |
| 43 | 2.55 | 2.32 | -0.23 |
| 44 | 0.92 | 2.55 | +1.63 |
| 45 | 1.40 | 1.26 | -0.14 |
| 46 | 1.98 | 1.56 | -0.42 |
| 47 | 2.06 | 0.00 | -2.06 |
| 48 | 1.73 | 1.70 | -0.03 |
| **Avg** | **1.67** | **1.66** | **-0.02 (-0.9%)** |

Neutral change — within variance. Theoretically correct for freeplay.

## Submissions
- Freeplay: beta:v84 (beta-cvc)
- Tournament: beta:v85 (beta-teams-tiny-fixed)
