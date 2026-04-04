#!/bin/bash
echo "Testing delta stack 036+037+038+040 (penalty reduction)"
echo "Changes: teammate_penalty 7.0, hotspot_weight 11.0, enemy_aoe 9.5, claimed_target_penalty 11.0"
echo ""
echo "Baseline: gamma_v6:v1 (15.90 tournament avg)"
echo "Note: Local testing has poor correlation with tournament, but better than no testing"
echo ""

for seed in 42 43 44 45 46; do
  echo "=== Seed $seed ==="
  ANTHROPIC_API_KEY= PYTHONPATH=src/cogamer timeout 2100 cogames play -m four_score \
    -p class=cvc.cogamer_policy.CvCPolicy \
    -c 32 -r none --seed $seed 2>&1 | grep -A 10 "Episode Complete" | grep -E "Score|per cog"
  echo ""
done
