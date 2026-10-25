# P2 cart log, 2026-10-24 20:03 (Arizona)

- Agent: Claude Code (Claude Opus 5.5)
- Team member: Lucas (food engine)
- Branch: p2-cart (from origin/main at fc1a4b6). Not pushed.

## Problem

1. The cart store did not match the deal stores. Plan prices come from ALDI, Target, Fry's and Safeway ads, but the default cart site was Walmart.com. Walmart has almost no usable ads near 85281 and showed a robot check on a plain fetch. "Reply 1 build cart" would have built a basket at a store whose prices the plan never used.
2. The example message and the deals.json example in references/weekly-autopilot.md had made-up numbers ($23.40, $1.99/lb, "Fry's, ends Tue") that Cubbie could copy.

## Implemented

1. Default cart site is now Target.com (pickup or same-day delivery). Walmart.com and Instacart stay as options the student can choose; DoorDash stays as one for students elsewhere.
   - SKILL.md ("Stretch stores ... cart site").
   - references/onboarding.md: question 2, and the end-of-setup example ("Cart: Target.com pickup").
   - references/weekly-autopilot.md: "Building the cart".
2. "Building the cart" step 4: if any plan price came from a store other than the cart site, the cart text says so in one short line, because the cart total can then differ from the plan's ad prices. The one-try-then-plain-shopping-list fallback is unchanged.
3. Example labels ("example only", pointing Cubbie to the script output or the student's own answers). Formats are unchanged.
   - weekly-autopilot.md: the deals.json example, the shelf_prices.json example, the message example, the "9 of 12" price-source line and the "$14 bowl" delivery line.
   - onboarding.md: the Money Map summary example.
   - gear.md: the message example (use payback.py's output).
   - money-check.md: the example reply (use tally.py's output).
   - Left as is: the "$2.00 rice" field explanation, the Spotify line from the sourced perks catalog, the quoted "$41 until Friday" student message, and the team-only demo-video example.
4. docs/demo-video.md: setup answer says "cart site Target.com pickup"; the cart fallback names Target.com; checklist item 11 says to run the Target.com cart once off camera first.
5. docs/PMD.md and docs/BUILD-NOTES.md: why the default moved off Walmart.com, and that the Target.com cart in Cubbie's browser is UNVERIFIED (only Target's search page was checked, by a plain fetch on 2026-10-24).
6. No script, test or asset changed. No safety rule changed: the student signs in and pays, no trials or memberships, no getting around robot checks, one try then a plain shopping list.

## Tests

All pass:
- tests/test_fetch_deals.py: 13 tests OK.
- tests/test_plan_meals.py: 4 tests OK.
- `--sample`, exit 0 for all five: fetch_deals, plan_meals, payback, merge_prices, tally.
- Kit validator OK.
- Grep for "default Walmart", "Walmart.com", "cart site" and "bot check": no default-Walmart wording left. Walmart.com remains only as a student option and in Tier 2 shelf-price data (assets/store_sites.json, assets/sample_shelf_prices.json) and older logs.

## Blockers

- None for this work.

## What's left

1. Test Tier 2 (shelf pages in Cubbie's browser) on a real Cubbie.
2. Test Tier 3 (price-tag photo or typed price) on a real Cubbie.
3. Test the Target.com cart fill on a real Cubbie before the video. If it shows a robot check or a sign-in that will not work, record the shopping-list fallback.
4. Rerun the hero plan before recording.
5. Confirm the Track 1 deadline on hackathon.cubbie.ai or Discord. It is still unconfirmed.
