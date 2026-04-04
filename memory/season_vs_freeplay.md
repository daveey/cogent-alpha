---
name: season_vs_freeplay
description: beta-four-score is a freeplay season, not listed in cogames season list but accepts uploads
type: reference
---

**Critical discovery:** beta-four-score exists as a **freeplay season**.

`cogames season list` only shows "tournament seasons" like beta-cvc. But beta-four-score is accessible as a freeplay at https://softmax.com/observatory/freeplay/beta-four-score

**How to upload to beta-four-score:**
```bash
cogames upload -p class=cvc.cogamer_policy.CvCPolicy -n gamma \
  --season beta-four-score --skip-validation
```

This works even though beta-four-score doesn't appear in `cogames season list`.

**Why:** Freeplay seasons are separate from tournament seasons. Use direct season name in upload command.

**How to apply:** Always upload improvements to beta-four-score (the four_score mission target), not beta-cvc (machina_1, 2-team).
