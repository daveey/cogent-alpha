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
**Seed 46**: Running (final seed)...

**Avg so far**: 10.01 (seeds 42-45) vs baseline avg 10.83 → **-7.6% regression**

**EXTREME INSTABILITY**: Two seeds with massive improvements (42: +107%, 45: +125%), two seeds with major regressions (43: -79%, 44: -38%). This variance pattern is catastrophic for production use. Need seed 46 to finalize, but likely revert due to unpredictability.

Expected completion: ~60-75 minutes (12-15 min/seed × 5 seeds)

## Monitoring

Check test status:
```bash
./check_test_011.sh
tail -f test_results_011.txt
```
