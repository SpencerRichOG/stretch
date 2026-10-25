# P2 coverage log, 2026-10-24 18:01 (Arizona)

- Agent: Claude Code (Claude Opus 5.5)
- Team member: Lucas (food engine)
- Branch: p2-coverage (from origin/main at 8d011a7). Not pushed.

## Diagnosis (live Flipp, ZIP 85281, 2026-10-24)

- No store filter: 35 ad prices for 12 of 22 items, from 14 merchants.
- No ad price: ground turkey, rice, chickpeas, lentils, frozen broccoli, frozen mixed vegetables, frozen spinach, carrots, canned tuna, tofu.
- Main causes:
  - Chickpeas, lentils and tofu had no hits at all.
  - Ground turkey and carrots: the ad shows no size.
  - Rice: the only sized ad is a multi-product ad with ranges ("Tomatoes 14.5-15 oz., Rice 16 oz. or Beans 15-15.5 oz.").
  - Frozen vegetables: only an 8-14 oz range.
  - Canned tuna: found only by the query "tuna".
- Fry's chicken ($0.99/lb with card) shows up only for the queries "chicken thigh" and "chicken drumsticks".
- Walmart: 1 raw hit across 33 searches (a chips ad).
- Three wrong rows were kept:
  - Knorr "Pasta or Rice Sides" as pasta;
  - El Pato tomato sauce as salsa;
  - a Restaurant Depot case price for cheese.

## Implemented

1. fetch_deals.py:
   - second queries for chicken thighs and canned tuna;
   - reads the size from the one part of a multi-product ad that names the item;
   - drops case-only prices;
   - bad words "side" (pasta) and "de tomate" (salsa);
   - one WARNING line for a `--stores` name with no usable ad price, or an unknown name.
   - Exit codes, `--sample` and the User-Agent are unchanged. The chicken-per-pound rule is unchanged.
2. tests/test_fetch_deals.py (stdlib unittest, offline):
   - multi-product rice 16 oz accepted;
   - rejected: two matching parts, a range inside the matching part, no matching part;
   - also case-only, pasta sides and chicken without a per-pound price.
   - assets/sample_flipp.json has one new rejected two-part rice row.
3. plan_meals.py: lines that need a store card or coupon now say "with card" or "with coupon". Before, the condition was dropped.
4. assets/store_sites.json:
   - "status" is blocked for Walmart, Fry's, CVS and Safeway (one try in Cubbie's browser, then Tier 3);
   - unverified for Aldi and Sprouts;
   - loaded for Target.
5. SKILL.md, weekly-autopilot.md, onboarding.md:
   - default stores ALDI, Target, Fry's and Safeway when none, or only Walmart, are given;
   - Walmart ads and shelf prices are usually unavailable, and Walmart shelf prices are never promised;
   - at most four stores;
   - a blocked or failed store goes straight to Tier 3 (top 3 items);
   - the WARNING lines are explained;
   - the shelf example uses the recorded Target price.
6. docs/demo-video.md: the hero stores are now ALDI, Target, Fry's and Safeway. Rerun the plan right before recording. There was no Walmart shelf-price claim.
7. docs/PMD.md (new, one page) and the BUILD-NOTES.md updates, including the Kroger API as the post-hackathon Fry's route.

## Tests

All pass:
- fetch_deals 0/2/5 (5 from Python 3.12, see below).
- merge_prices 0/2, with drops for a 10x shelf row, a 10x ad row and a stale row.
- plan_meals 0/2/3/4, payback 0/2, tally 0/2.
- 9 unit tests.
- Python 3.9 syntax (7 files).
- Kit validator OK.
- `--sample` with `--out` wrote nothing, and the temp HOME stayed empty.
- Longest output: 2,161 characters (fetch_deals, live, no filter).

Python note: Python 3.12 on this dev machine has no CA certificates. fetch_deals.py exits 5 there by design, and certificate checks were not turned off. Live runs used `py -3.13`. Cubbie's sandbox could behave the same way; exit 5 sends Cubbie to Tier 2.

## Hero profile (live, 2026-10-24)

$41 budget; microwave, stove, pan and pot; 85281; 5 days x 2 meals.

| stores | before | after |
| --- | --- | --- |
| Fry's,Walmart | $15.88, 2 of 7 real | $13.95, 4 of 8 real |
| ALDI,Target,Fry's,Safeway | $15.97, 3 of 7 real | $12.04, 5 of 8 real |

- The plan now includes chicken and rice bowls.
- Still estimates: frozen broccoli, frozen mixed vegetables and frozen spinach (no sized ad this week), plus rice for Fry's,Walmart.

## Blockers

- None for this work.
- Ground turkey, carrots and frozen vegetables cannot get ad prices without guessing a size, so they wait for Tier 3.

## What's left

1. Test Tier 2 and Tier 3 on a real Cubbie. Both are still unproven there.
2. Rerun the hero plan before recording.
3. Confirm the Track 1 deadline on hackathon.cubbie.ai or Discord. It is still unconfirmed.
