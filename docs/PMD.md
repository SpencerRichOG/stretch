# Stretch PMD

For the team, not for Cubbie. One page, built only from SKILL.md, docs/BUILD-NOTES.md and the logs in docs/logs/. If this page and those files disagree, those files win.

## Purpose

Stretch is a Cubbie Skill (Cubbie Hackathon, Track 1) that finds where a college student quietly loses money on food, subscriptions, transport and gear, then texts a weekly meal-prep plan that fits their budget and kitchen. About two minutes a week: one Sunday meal-prep text, plus occasional "your school gives you this free" findings. Built around ASU Tempe; elsewhere it relies on web search and says results may be less precise.

## Modules

| Module | What it does | Files |
| --- | --- | --- |
| M1 Money Map onboarding | Saves school, stores, memberships, budget, diet, kitchen, subscriptions and schedule as labeled memory facts; builds profile.json for the scripts | references/onboarding.md, SKILL.md |
| M2 Sunday autopilot | Weekly check-in: real prices, a budget-exact meal plan, one message, optional cart fill (the student pays) | references/weekly-autopilot.md, scripts/fetch_deals.py, scripts/merge_prices.py, scripts/plan_meals.py |
| M3 Subscription and perks audit | Matches the student's subscriptions to student plans and school perks, with source URLs | references/perks.md |
| M4 Gear that pays for itself | Ranks kitchen gear by payback, respecting dorm bans | references/gear.md, scripts/payback.py |
| Monthly money check | Spending totals by category from receipts the student sends | references/money-check.md, scripts/tally.py |

Not built (spec Should/Could): job survey, calendar blocks, textbook or scholarship help. SKILL.md says so in one line and redirects.

## Price ladder (M2)

Best source first; each tier only for items still without a real price.

1. Weekly ads: fetch_deals.py reads Flipp's public weekly-ad search (HTTPS JSON, no key) and keeps only prices tied to a library item and a readable size. Default stores near ASU: ALDI, Target, Fry's and Safeway.
2. Shelf prices: Cubbie reads the store's own public page (assets/store_sites.json), one try per store. Walmart, Fry's, Safeway and CVS were blocked on a plain fetch on 2026-10-24.
3. The student: a price-tag photo or typed price, at most the 3 costliest items, once a week.
4. Estimates: typical prices, labeled "estimate".

merge_prices.py checks every shelf or student row (library item, size and unit, seen within 4 days, 25%-400% of typical, no card numbers) and drops ad rows far from typical. plan_meals.py labels each line ad deal, shelf price, student price or estimate, says "with card" or "with coupon" where needed, and prints "Real prices: N of M lines".

Rules that never bend: no bank logins, no moving money, the student approves and pays, no API keys, nothing sent to a team server, no getting around robot checks or sign-in walls, no invented prices.

## Who owns what

- Lucas: food engine (M2, the price ladder and its scripts) and the submission.
- Spencer: core (SKILL.md and the shared memory and profile contract).
- Kerem: money and video (the perks audit, the monthly money check and docs/demo-video.md).

## Known risks

- Flipp's search is unofficial and could change; exit 5 sends Cubbie to Tier 2 for every item.
- Walmart: almost no weekly-ad data near 85281 and shelf pages show a robot check, so the default cart site is Target.com (pickup or same-day delivery). Walmart.com and Instacart stay as options the student can choose.
- Target.com cart: UNVERIFIED in Cubbie's browser; only Target's search page was checked, by a plain fetch on 2026-10-24. Fallback after one try: a plain shopping list. When deals came from ALDI, Fry's or Safeway, the Target cart total can differ from the plan, and the cart text says so.
- Ad matching can still be wrong; merge_prices.py drops prices far from typical, but not every misread.
- DashPass is not promised (DoorDash's pages disagree, no ASU, sign-up window ended 2026-10-12). ASU dorm appliance bans limit gear advice.
- Recipe prices that come from typical prices are estimates, not live quotes.
- Kroger's official API (real Fry's shelf prices) needs each student to register a developer app; post-hackathon only.

## What is unproven

- No script has run from a real Cubbie sandbox; Tier 2 (shelf pages in Cubbie's browser) and Tier 3 (student photos) are untested on a real Cubbie.
- The Target.com cart fill is untested in Cubbie's browser.
- Store sites were checked by a plain fetch from a dev computer, not Cubbie's browser; Aldi and Sprouts shelf pages are unverified.
- Amazon Prime Student and Sun Devil Sync numbers are not verified.
- Not tested at other schools or stores.
- The Track 1 deadline is unconfirmed (the kit says within the first 10 hours of the event); confirm on hackathon.cubbie.ai or Discord.
