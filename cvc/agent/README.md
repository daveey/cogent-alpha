# CvC Agent — Coglet Policy for Cogs vs Clips

This is the coglet CvC tournament agent. It plays the Cogs vs Clips game on the cogames platform.

## Architecture

```
CogletPolicy (cvc_policy.py)
  └── CogletBrainAgentPolicy (per-agent: heuristic + LLM brain)
        └── CogletAgentPolicy (anthropic_pilot.py: macro directives)
              └── SemanticCogAgentPolicy (semantic_cog.py: core heuristic)
                    └── helpers/ (targeting, resources, geometry, types)
```

**Three layers:**
- **Fast path**: Python heuristic runs every step (10,000 steps/episode). Role-based behavior: aligners capture junctions, scramblers disrupt enemy junctions, miners collect resources, scouts explore.
- **Slow path**: LLM brain (Claude) analyzes game state ~20 times per episode. Produces `MacroDirective` (resource bias, role hints) that steers the heuristic.
- **Learnings**: End-of-episode data written to `/tmp/coglet_learnings/` for post-game analysis.

## Files

| File | Purpose |
|------|---------|
| `cogames/cvc/cvc_policy.py` | Top-level policy: LLM brain, learnings writer |
| `cogames/cvc/policy/anthropic_pilot.py` | `CogletAgentPolicy`: resource-aware directives, miner retreat |
| `cogames/cvc/policy/semantic_cog.py` | Core heuristic (~1300 lines): role selection, navigation, combat |
| `cogames/cvc/policy/helpers/targeting.py` | Target scoring for aligners and scramblers |
| `cogames/cvc/policy/helpers/resources.py` | Inventory, phases, retreat thresholds, heart batching |
| `cogames/cvc/policy/helpers/geometry.py` | Movement, pathfinding, exploration patterns |
| `cogames/cvc/policy/helpers/types.py` | Constants and tuning parameters |
| `cogames/setup_policy.py` | Setup script: installs `anthropic` SDK in tournament sandbox |

## Cogames CLI

The cogames CLI is at `/home/user/.venv-cogames/bin/cogames`. All commands below assume this path (or add it to PATH).

```bash
export COGAMES=/home/user/.venv-cogames/bin/cogames
```

## Local Testing

### Quick test (1 episode, self-play)

```bash
cd /home/user/coglet/cogames

$COGAMES scrimmage \
  -m machina_1 \
  -p class=cvc.cvc_policy.CogletPolicy \
  -c 8 -e 1 --seed 42 \
  --action-timeout-ms 30000
```

Output includes per-agent metrics table and **Average Per-Agent Reward** (the score).

### Multi-episode eval (more reliable)

```bash
$COGAMES scrimmage \
  -m machina_1 \
  -p class=cvc.cvc_policy.CogletPolicy \
  -c 8 -e 5 --seed 42 \
  --action-timeout-ms 30000
```

### JSON output (for scripting)

```bash
$COGAMES scrimmage \
  -m machina_1 \
  -p class=cvc.cvc_policy.CogletPolicy \
  -c 8 -e 1 --seed 42 \
  --action-timeout-ms 30000 \
  --format json
```

### Against another policy (pickup eval)

```bash
$COGAMES run \
  -m machina_1 \
  -p class=cvc.cvc_policy.CogletPolicy \
  -p class=baseline \
  -c 8 -e 5 --seed 42 \
  --action-timeout-ms 30000
```

### Interactive play (GUI/terminal)

```bash
$COGAMES play \
  -m machina_1 \
  -p class=cvc.cvc_policy.CogletPolicy \
  -c 8 --seed 42
```

### Save replay for later viewing

```bash
$COGAMES scrimmage \
  -m machina_1 \
  -p class=cvc.cvc_policy.CogletPolicy \
  -c 8 -e 1 --seed 42 \
  --action-timeout-ms 30000 \
  --save-replay-dir ./replays

$COGAMES replay ./replays/<file>.json.z
```

## Tournament Submission

### Upload and submit in one step

```bash
cd /home/user/coglet/cogames

$COGAMES ship \
  -p class=cvc.cvc_policy.CogletPolicy \
  -n coglet-v0 \
  -f cvc -f mettagrid_sdk -f setup_policy.py \
  --setup-script setup_policy.py \
  --season beta-cvc \
  --skip-validation
```

`ship` = bundle + validate + upload + submit. Use `--skip-validation` to skip Docker validation (faster, use when you've already tested locally). Use `--dry-run` to validate without uploading.

### Upload only (no submit)

```bash
$COGAMES upload \
  -p class=cvc.cvc_policy.CogletPolicy \
  -n coglet-v0 \
  -f cvc -f mettagrid_sdk -f setup_policy.py \
  --setup-script setup_policy.py \
  --no-submit
```

### Submit a previously uploaded version

```bash
$COGAMES submit coglet-v0 --season beta-cvc
# Or a specific version:
$COGAMES submit coglet-v0:v6 --season beta-cvc
```

## Checking Results

### Leaderboard

```bash
# Full leaderboard
$COGAMES leaderboard beta-cvc

# Just our policy
$COGAMES leaderboard beta-cvc --policy coglet-v0

# Just our policies (all names)
$COGAMES leaderboard beta-cvc --mine
```

### Via API (no CLI needed)

```bash
curl -s -H "Authorization: Bearer $COGAMES_TOKEN" \
  "https://api.observatory.softmax-research.net/tournament/seasons/beta-cvc/leaderboard" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
coglet = [e for e in data if 'coglet' in e.get('policy',{}).get('name','').lower()]
for e in coglet:
    p = e['policy']
    print(f\"Rank #{e['rank']}/{len(data)}: {p['name']} v{p['version']} — Score: {e['score']:.3f} +/- {e['score_stddev']:.3f} ({e['matches']} matches)\")
print(f'Top: {data[0][\"score\"]:.3f} ({data[0][\"policy\"][\"name\"]} v{data[0][\"policy\"][\"version\"]})')
"
```

### Match history

```bash
# Recent matches
$COGAMES matches -s beta-cvc --policy coglet-v0

# Match details with logs
$COGAMES matches <match-id> --logs

# Download logs
$COGAMES matches <match-id> -d ./match-logs
```

### Submissions

```bash
$COGAMES submissions --policy coglet-v0
```

## Debugging

### Check policy loads correctly

```bash
cd /home/user/coglet/cogames
python3 -c "
from cvc.cvc_policy import CogletPolicy
print('Policy class loaded OK')
print('Short names:', CogletPolicy.short_names)
"
```

### Validate bundle in Docker (before uploading)

```bash
$COGAMES ship \
  -p class=cvc.cvc_policy.CogletPolicy \
  -n coglet-v0 \
  -f cvc -f mettagrid_sdk -f setup_policy.py \
  --setup-script setup_policy.py \
  --dry-run
```

### Check LLM brain is active

The LLM brain requires `ANTHROPIC_API_KEY` or `COGORA_ANTHROPIC_KEY`. In tournament, secrets are passed via `--secret-env`:

```bash
$COGAMES upload \
  -p class=cvc.cvc_policy.CogletPolicy \
  -n coglet-v0 \
  -f cvc -f mettagrid_sdk -f setup_policy.py \
  --setup-script setup_policy.py \
  --secret-env COGORA_ANTHROPIC_KEY=$COGORA_ANTHROPIC_KEY \
  --season beta-cvc
```

Without the key, the policy still works (pure heuristic, no LLM calls).

### Read learnings from a local game

```bash
ls /tmp/coglet_learnings/
cat /tmp/coglet_learnings/game_*.json | python3 -m json.tool | head -50
```

### Common issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: mettagrid` | Wrong Python env | Use `/home/user/.venv-cogames/bin/cogames` |
| `Action timeout (noop)` | LLM call too slow | Increase `--action-timeout-ms` or reduce `_LLM_INTERVAL` |
| Score = 0 | Policy crashed silently | Check stderr, run with `--format json` for details |
| Upload fails auth | Missing/expired token | Run `$COGAMES login` or set `COGAMES_TOKEN` |

## Key Game Mechanics

- **Map**: 88x88 grid, 10,000 steps per episode
- **Teams**: 8 cogs (us) vs clips (opponent)
- **Score**: aligned junctions held per tick (higher = better)
- **Roles**: aligner (capture junctions), scrambler (disrupt enemy), miner (collect resources), scout (explore)
- **Resources**: carbon, oxygen, germanium, silicon — needed for gear and hearts
- **Hearts**: required for aligners/scramblers to act on junctions
- **Hub**: team base — deposit resources, get gear, refill hearts

## Tunable Parameters

Key constants in `helpers/types.py`:
- `_HP_THRESHOLDS` — when each role retreats
- `_HEART_BATCH_TARGETS` — hearts to collect before acting
- `_EMERGENCY_RESOURCE_LOW` — threshold for emergency mining
- `_CLAIMED_TARGET_PENALTY` — cost for targeting already-claimed junctions
- `_TARGET_CLAIM_STEPS` — how long a claim lasts
- `_EXTRACTOR_MEMORY_STEPS` — how long to remember extractor locations

Key constants in `semantic_cog.py`:
- `_RETREAT_MARGIN` — HP buffer for retreat decisions
- `_ALIGNER_GEAR_DELAY_STEPS` — delay before aligners get gear
- `_TARGET_SWITCH_THRESHOLD` — cost to switch targets
- `_MINING_ALIGNER_MIN_RESOURCE` — when aligners switch to mining

Key parameters in `anthropic_pilot.py`:
- `_MINER_MAX_HUB_DISTANCE` — max distance before miner retreats

Key scoring weights in `targeting.py`:
- `aligner_target_score()` — distance, expansion potential, enemy AoE, hub proximity
- `scramble_target_score()` — distance, blocked neutrals, corner pressure, threat to friendlies
