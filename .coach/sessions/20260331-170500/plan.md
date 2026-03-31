# Session 40 Plan

## Status
- Tournament: beta:v7 rank #1 (10.00), tied with alpha.0:v891
- Freeplay: beta:v15 best at 1.81, alpha.0:v716 at 15.05 (8x gap)
- Recent matches: beta:v59=0.83, v57=0.96 (stage-1, still qualifying)
- Self-play baseline: seeds 42-46, avg ~2.04

## Analysis
Freeplay scores have declined from v15 (1.81) to recent versions (~1.57).
The teammate penalty (10.0) in aligner_target_score was introduced in v26
(session 36). Freeplay dropped from 1.69 (v23) to 1.45 (v26) around that time.

In freeplay, teammates are from OTHER policies with unpredictable behavior.
The penalty causes our aligners to avoid junctions near teammates even when
those teammates aren't actually targeting those junctions. The claim system
(12.0 penalty, 30-step expiry) already handles coordination for same-policy agents.

## Change
Remove teammate penalty from aligner_target_score in helpers/targeting.py:
- `teammate_penalty = 10.0 if teammate_closer else 0.0` → remove entirely
- Keep the teammate_closer parameter for backward compatibility but ignore it

## Expected Impact
- Self-play: neutral (claim system still prevents duplicates)
- Freeplay: positive (aligners choose better junctions without false coordination signals)
