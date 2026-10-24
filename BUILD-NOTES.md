# Stretch build notes

For the team, not for Cubbie. Cubbie reads SKILL.md and the files it points to; this file records why things are the way they are.

## What is built (all four Must modules)

- M1 Money Map onboarding: references/onboarding.md, memory labels in SKILL.md, profile.json contract.
- M2 Sunday autopilot: references/weekly-autopilot.md plus scripts/plan_meals.py (exact budget math, bundled recipe library in assets/recipes.json).
- M3 Subscription and perks audit: references/perks.md (catalog with source URLs, verified 2026-10-24).
- M4 Gear that pays for itself: references/gear.md plus scripts/payback.py.

## Deviations from the spec, and why

1. DashPass hero line. The spec promises a free year of DashPass. DoorDash's two student pages disagree with each other, neither lists ASU, and the stated sign-up window ended 2026-10-12. perks.md tells Cubbie never to promise it. For the demo video, test with a real ASU-verified account first; otherwise use Uber One student ($4.99/mo after a 4-week trial) or Spotify student ($6.99/mo).
2. Dorm appliance bans. ASU's housing checklist (2024 file, undated inside) bans toasters, hot plates and crock pots/instant pots. The spec's Tier 2 includes a toaster and air fryer. payback.py takes `--banned` and the gear list carries a housing "check" flag, so Cubbie never recommends a banned item and tells students to confirm the rest with housing.
3. Memory keys. The spec lists "memory keys" but Cubbie memory is free text, not keyed fields. We use labeled facts ("Stretch kitchen: ...") and turn them into profile.json for scripts.
4. A pan requires a stove in gear.json. A microwave-only dorm student is not shown a pan as a first purchase. Check this against the spec's "hero thread" example before recording, because that example assumed a pan.
5. Not built (spec Should/Could): monthly spending scan, job survey, calendar blocks, textbook help. SKILL.md says so in one line and redirects.

## Verified facts and where they came from

All in references/perks.md with URLs and the date checked. Not verified: Amazon Prime Student (page blocks automated reading), Sun Devil Sync event pages (same). Do not quote numbers for those.

## Known risks

- Walmart.com may show a bot check when Cubbie's browser builds the cart. SKILL.md falls back to a plain shopping list after one try. Test on a real Cubbie before the video.
- Whether Fry's or Walmart weekly ads can be read reliably by Cubbie's web ability is untested. Missing deals fall back to typical prices (assets/typical_prices.json), which are rough estimates labeled as such.
- Recipe prices are estimates, not live quotes.
- Submission link: the kit's cubbie-hackathon SKILL.md says to submit the pinned commit link; cubbie-testing.md says the repository link. Ask in Discord (https://discord.gg/7eJADTbQMT) or check hackathon.cubbie.ai before submitting.
- Track 1 deadline: the kit says finish within the first 10 hours of the event. The exact time was not found. Confirm on hackathon.cubbie.ai or Discord.

## Scripts

Standard library only, Python 3.9+. Both have `--sample`. Exit codes: plan_meals 0/2/3/4, payback 0/2. Output stays well under Cubbie's 8,000-character read limit.
