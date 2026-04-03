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

## Results

(Pending - will update when tests complete)
