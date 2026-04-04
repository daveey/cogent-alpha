# Test In Progress: 20260403-011

**Status**: Testing across seeds 42-46
**Started**: 2026-04-03 21:45 UTC
**PID**: 2246
**Output**: test_results_011.txt

## Change

**Focus**: RETREAT_MARGIN parameter adjustment

**File**: `src/cogamer/cvc/agent/budgets.py` - line 15

**Description**: 
Increased `_RETREAT_MARGIN` from 15 to 20 to match alpha.0's more conservative retreat threshold. This makes agents retreat to hub earlier when HP is low, potentially improving survival rates.

**Hypothesis**: Alpha.0 uses RETREAT_MARGIN = 20, we use 15. More conservative retreat could reduce agent deaths and improve overall performance. Simple parameter change, well-tested by alpha.0.

## Baseline

Current baseline: **9.74 avg per cog** (from attempt 007: early scrambler activation)
- Seeds 42-46: 9.37, 11.44, 19.86, 2.64, 5.38

## Results

**Seed 42**: 19.42 per cog (baseline: 9.37) → **+107.2% improvement**
**Seed 43**: 2.45 per cog (baseline: 11.44) → **-78.6% regression**
**Seed 44**: 12.22 per cog (baseline: 19.86) → **-38.5% regression**
**Seed 45**: 5.95 per cog (baseline: 2.64) → **+125.4% improvement**
**Seed 46**: 6.68 per cog (baseline: 5.38) → **+24.2% improvement**

**Final Average**: 9.34 per cog vs baseline 9.74 → **-4.0% REGRESSION**
**Standard Deviation**: 6.63 (baseline: 6.61)

## Conclusion: REVERTED

Slight regression confirmed (-4.0%), but more critically **EXTREME INSTABILITY** detected:
- Individual seed swings: +107%, -79%, -38%, +125%, +24%
- Score range: 2.45 to 19.42 (8× spread)
- Unpredictable pattern: some scenarios massive gains, others catastrophic failures

**Key Learning**: RETREAT_MARGIN 20 (vs 15) creates unpredictable behavior. More conservative retreat helps some scenarios (agents survive longer) but hurts others (agents retreat too early, miss scoring opportunities). Similar to attempt 012 which showed +3.8% avg but was reverted due to 40% catastrophic failure rate.

**Reverted** budgets.py to RETREAT_MARGIN = 15. Alpha.0's value (20) appears tuned for machina_1 (2-team), not four_score (4-team) dynamics. Current value 15 better calibrated for multi-directional threat environment.

Expected completion: ~60-75 minutes (12-15 min/seed × 5 seeds)

## Monitoring

Check test status:
```bash
./check_test_011.sh
tail -f test_results_011.txt
```
