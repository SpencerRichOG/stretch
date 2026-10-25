# Stretch build notes

For the team, not for Cubbie. Cubbie reads SKILL.md and the files it points to; this file records why things are the way they are.

## What is built (all four Must modules, plus the monthly money check)

- M1 Money Map onboarding: references/onboarding.md, memory labels in SKILL.md, profile.json contract.
- M2 Sunday autopilot: references/weekly-autopilot.md plus scripts/plan_meals.py (exact budget math, bundled recipe library in assets/recipes.json).
- M3 Subscription and perks audit: references/perks.md (catalog with source URLs, verified 2026-10-24).
- M4 Gear that pays for itself: references/gear.md plus scripts/payback.py.
- Monthly money check (spending scan from receipts): references/money-check.md plus scripts/tally.py (exit 0/2).
- Price ladder for M2: references/weekly-autopilot.md step 2. Tier 1 weekly ads (scripts/fetch_deals.py), Tier 2 shelf prices Cubbie reads on the store's own public site (assets/store_sites.json, one try per store, blocked stores named), Tier 3 a price-tag photo or typed price from the student (top 3 items at most), Tier 4 typical-price estimates. scripts/merge_prices.py checks every shelf or student row (library item, size and unit, seen within 4 days, 25%-400% of typical, no card numbers) and merges them into deals.json (exit 0/2). plan_meals.py labels each line ad deal, shelf price, student price or estimate and prints a "Real prices: N of M lines" count.

## Deviations from the spec, and why

1. DashPass hero line. The spec promises a free year of DashPass. DoorDash's two student pages disagree with each other, neither lists ASU, and the stated sign-up window ended 2026-10-12. perks.md tells Cubbie never to promise it. The demo video uses the Spotify student finding instead (see docs/demo-video.md); do not show or promise DashPass.
2. Dorm appliance bans. ASU's housing checklist (2024 file, undated inside) bans toasters, hot plates and crock pots/instant pots. The spec's Tier 2 includes a toaster and air fryer. payback.py takes `--banned` and the gear list carries a housing "check" flag, so Cubbie never recommends a banned item and tells students to confirm the rest with housing.
3. Memory keys. The spec lists "memory keys" but Cubbie memory is free text, not keyed fields. We use labeled facts ("Stretch kitchen: ...") and turn them into profile.json for scripts.
4. A pan requires a stove in gear.json. A microwave-only dorm student is not shown a pan as a first purchase. Check this against the spec's "hero thread" example before recording, because that example assumed a pan.
5. Not built (spec Should/Could): job survey, calendar blocks, textbook help. The monthly spending scan is built (references/money-check.md, scripts/tally.py). SKILL.md says so in one line and redirects.

## Verified facts and where they came from

All in references/perks.md with URLs and the date checked. Not verified: Amazon Prime Student (page blocks automated reading), Sun Devil Sync event pages (same). Do not quote numbers for those.

## Known risks

- Walmart.com may show a bot check when Cubbie's browser builds the cart. SKILL.md falls back to a plain shopping list after one try. Test on a real Cubbie before the video.
- Weekly ads: Cubbie reading ad pages gave mostly estimates, so scripts/fetch_deals.py now pulls real ad prices from Flipp's public search (backflipp.wishabi.com, HTTPS JSON, no key). Checked 2026-10-24 for ZIP 85281 with no store filter: 35 ad prices for 12 of 22 items from 14 merchants. Of the target stores, ALDI, Target, Fry's Food Stores and Safeway had usable ad prices; Walmart, CVS Pharmacy and Sprouts Farmers Market had none. `--stores` now accepts common names (Frys, Aldi, CVS, Sprouts). It is unofficial and could change; exit 5 sends Cubbie to Tier 2 (shelf prices) for every item. Not yet run from a real Cubbie sandbox. Walmart regular shelf prices are not in weekly ads.
- Price sources considered: Kroger's official API (real Fry's shelf prices per store) needs each student to register a developer app for a client ID and secret, too much friction for now. Instacart's API is partner-only. Scripts never pose as a browser, use a store's private or unofficial app APIs, or get around robot checks; shelf prices come only from Cubbie reading the store's public page (Tier 2) or from the student (Tier 3).
- Shelf pages, plain fetch from a dev computer on 2026-10-24 (not Cubbie's browser): Target loaded with prices; Walmart and Safeway showed robot checks; CVS returned 403; Fry's timed out; Sprouts and Aldi pages build with JavaScript. So for the default stores (Fry's, Walmart) Tier 2 may fall back to the student's photo. Do not promise Walmart shelf prices in the video. Test on a real Cubbie.
- Recipe prices are estimates, not live quotes.
- Submission link: answered; submit the repository link (see docs/submission-draft.md).
- Track 1 deadline: the kit says finish within the first 10 hours of the event. The exact time was not found. Confirm on hackathon.cubbie.ai or Discord.

## Scripts

Standard library only, Python 3.9+. All have `--sample`. Exit codes: plan_meals 0/2/3/4, payback 0/2, fetch_deals 0/2/5, merge_prices 0/2, tally 0/2. Output stays well under Cubbie's 8,000-character read limit.
