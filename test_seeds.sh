#!/bin/bash
# Test across seeds 42-46 and extract per-cog scores

for seed in 42 43 44 45 46; do
  echo "Testing seed $seed..."
  ANTHROPIC_API_KEY= PYTHONPATH=src/cogamer python3 -m cogames play \
    -m four_score \
    -p class=cvc.cogamer_policy.CvCPolicy \
    -c 32 -r none --seed $seed 2>&1 | grep "per cog" || echo "FAILED seed $seed"
done
