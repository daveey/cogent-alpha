# Test In Progress: 20260403-010

**Status**: Testing across seeds 42-46
**Started**: 2026-04-03 19:23 UTC
**PID**: 1173
**Output**: test_results.txt

## Change

**Focus**: LLM stagnation detection (softer approach)

**File**: `src/cogamer/cvc/programs.py` - `_build_analysis_prompt()`

**Description**: 
Enhanced LLM analysis prompt with softer stagnation detection guidance:
- Added explicit definitions of "Stalled" (12+ steps no movement) and "Oscillating" (repeating positions)
- Provided suggestive examples instead of prescriptive rules (e.g., "stalled miner far from extractors → try 'aligner'")
- Emphasized "STRONGLY PREFER null" to minimize role churn and maintain team stability
- Made objective guidance more contextual and clear

## Hypothesis

Failed attempt 002 used prescriptive rules ("stalled miner→aligner") which caused -41.6% regression due to excessive role switching disrupting team coordination.

This softer approach gives the LLM:
1. Better context about what stalled/oscillating actually means
2. Suggestive examples rather than rigid rules
3. Strong bias toward stability (null)
4. Room to make nuanced decisions based on game state

Expected outcome: Improved LLM decision-making without the role churn that killed attempt 002.

## Baseline

Current baseline: **9.74 avg per cog** (from attempt 007: early scrambler activation)
- Seeds 42-46: 9.37, 11.44, 19.86, 2.64, 5.38

## Monitoring

Check test status:
```bash
ps aux | grep "[p]ython3 -m cogames play"
tail -30 test_results.txt
```

Test PID 1173 running seeds sequentially. Expected completion: 50-75 minutes (10-15 min/seed × 5 seeds).

## Results

**Seed 42**: 6.03 per cog (baseline: 9.37) → **-35.6% regression**
**Seed 43**: 7.48 per cog (baseline: 11.44) → **-34.6% regression**
**Seed 44**: 5.98 per cog (baseline: 19.86) → **-69.9% regression**
**Seed 45**: 4.71 per cog (baseline: 2.64) → **+78.4% improvement**
**Seed 46**: 5.33 per cog (baseline: 5.38) → **-0.9% regression**

**Final Average**: 5.91 per cog vs baseline 9.74 → **-39.4% REGRESSION**

## Conclusion: REVERTED

Major regression confirmed. Reverted `programs.py` to original simpler prompt.

**Key Learning**: Both prescriptive (attempt 002: -41.6%) and softer/suggestive (this attempt: -39.4%) LLM role guidance approaches fail with similar magnitude. The problem is not the phrasing but likely the LLM role suggestion mechanism itself. Adding verbose guidance, examples, and "STRONGLY PREFER null" emphasis did not help - performance nearly identical to prescriptive failure.

**Recommendation**: Abandon LLM-driven role changes entirely. Consider alternative coordination mechanisms that don't rely on LLM suggestions.
