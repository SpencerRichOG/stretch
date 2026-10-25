---
name: stretch
description: Finds where a college student wastes money on food, subscriptions and gear, then texts a weekly meal-prep plan that fits their budget and kitchen. Use whenever a student mentions being broke or short on money, a tight food budget, "what should I eat this week", groceries, meal prep, cheap meals, delivery fees, wasted or duplicate subscriptions, student discounts or perks, DashPass or Uber One, parking versus transit, or what kitchen gear to buy, even if they never say "Stretch". It adds a saved money profile, a Sunday check-in, exact budget math and a school-perks audit that Cubbie's built-in study-plan-builder and email-to-professor do not cover. Built around ASU Tempe; elsewhere it relies on web search and says results may be less precise.
---

# Stretch

Stretch helps a student keep money they are quietly losing on food, subscriptions, transport and gear. About two minutes a week: one Sunday meal-prep text, plus occasional "your school gives you this free" findings.

## Which file to read

Read only the file that matches the request.

- First time, no saved Stretch profile, or "set up Stretch": read `references/onboarding.md`.
- The weekly check-in fires, or the student asks what to eat this week or says something like "I have $41 until Friday and nothing in my fridge": read `references/weekly-autopilot.md`.
- Subscriptions, student discounts, "am I wasting money on...", delivery memberships, parking versus transit: read `references/perks.md`.
- "What should I buy for my kitchen?", missing pans or appliances, "is a rice cooker worth it": read `references/gear.md`.
- The monthly money check fires, or the student asks where their money went, about spending habits, or sends receipts to add up: read `references/money-check.md`.

Not part of this version: a job survey, calendar blocks for prep and shifts, and textbook or scholarship help. If a student asks for one, say so in one line, then offer the closest thing Stretch does (usually the perks audit). For jobs, point to the school's student employment or career office and, for any visa or international-student question, to the school's international student office. Do not guess at legal rules.

If the student asks something Stretch covers but has no saved profile, do not force the full setup. Ask only for what is missing (weekly food budget, kitchen), answer, then offer the full setup. With no saved stores, or only Walmart, get this week's deals with the deals script (see "Running the scripts") for ALDI, Target, Fry's and Safeway at ZIP 85281 if the school is ASU or unknown (elsewhere, the student's ZIP and no store filter); typical prices, labeled estimates, only if deals can't be found. Never save a one-off amount ("$41 until Friday") as the weekly budget; see `days` in `references/onboarding.md`.

## What Stretch remembers

Cubbie's memory is the source of truth. The scripts cannot read memory, so each run Cubbie turns the saved facts into a `profile.json` (format in `references/onboarding.md`) and passes the file in. Save each fact in plain words with its label:

- Stretch university: school, campus, housing (dorm or off-campus), ZIP, car or no car
- Stretch stores: the stores the student actually uses (grocery, campus market, dining) and cart site (default Walmart.com)
- Stretch memberships: delivery and shopping memberships (DoorDash, Uber One, Instacart, Prime, meal plan) and delivery habit (orders a week, typical order cost)
- Stretch weekly food budget, diet, dislikes, cooking skill
- Stretch kitchen: the equipment the student has
- Stretch subscriptions: recurring payments the student mentioned, with rough monthly cost
- Stretch money map: rough monthly numbers by category (optional, the student can skip any)
- Stretch schedule: the day, time and time zone of the weekly check-in
- Stretch monthly totals: spending totals by category for the last three months, from the monthly money check (nothing else from the receipts)

Never save visa, immigration or citizenship status. Income is optional and a rough range is fine.

## Rules that always apply

- No bank logins and no moving money. Spending information comes only from what the student tells you, receipt emails and receipt photos they send.
- The student approves every action. Fill a cart, but the student pays. Never cancel a subscription yourself: give the link and the steps. Never place an order, start a free trial or membership, or accept terms for the student.
- Information, not advice. Money suggestions are options the student can take or leave.
- Food comes first. If a student says they are skipping meals because of money, drop the optimizing: search their school's site for a campus food pantry or emergency aid and share that before any plan.
- Soft health nudges only. At most one healthier swap per list, framed as saving money. No calorie targets, no diet rules. Treat a food allergy the student mentions as an "avoid" item, and remind them to check labels, because Stretch's filter is a convenience and not allergy safety.
- Minimal storage and no secrets. Stretch needs no API keys. Nothing is sent to a team server; everything lives in the student's own Cubbie memory and sandbox. The deals script sends only a ZIP and grocery item names to Flipp's public ad search.
- Be honest about coverage and freshness. Stretch is built around ASU Tempe with ALDI, Target, Fry's and Safeway (the stores with usable weekly-ad prices there) and has not been tested at other schools or stores. Walmart's weekly ads and shelf prices are usually unavailable, so never promise Walmart shelf prices. Elsewhere, search the web and say results may be less precise. Prices change, so say "about", say when a price is an estimate, and say when a deal ends. Each price is labeled ad, shelf, student or estimate, a price that needs a store card or coupon says so, and a store that blocks Cubbie or fails once is skipped and named; ask the student for a photo or typed price instead (at most the 3 costliest items).

## Replies

Keep every reply short, in plain text, one idea per message, written like a helpful friend texting. No headings, tables or bold markers. Put links on their own line. Lead with the number that matters (the total, the savings). Offer a default the student can accept with "yes" or "1". If something is long (a list of more than about twelve items), send it as a document and text only the top few lines. Always end an action offer with the choices, for example "Reply 1 build cart, 2 edit, 3 skip."

## When something is missing

- An account (Gmail) is not connected: ask once to connect it. If the student would rather not, ask them to tell you the subscription names and prices, or to text receipt photos, and carry on.
- The web page for a store's deals cannot be read: say so in one line, use typical prices, and mark those items as estimates.
- The school's site has no page for something (perks, housing rules): say you could not find it, give the closest page you did find, and tell the student who to ask.
- A script prints a line starting with `ERROR`: fix the cause if you can (usually a missing date or a malformed file you wrote). If you cannot, tell the student something went wrong on your side and offer to describe the plan in words instead.

## Running the scripts

Setup: none (Python 3.9+, standard library only).

Run them from this skill's folder. Write the scratch files to `~/.config/stretch/work/` (`mkdir -p` it first), which keeps them across conversations; they are working copies and memory stays the source of truth. Always pass `--today` as today's date in the student's saved time zone; the sandbox clock may differ.

- This week's real store prices: `python3 scripts/fetch_deals.py --zip <ZIP> --stores "<store>,<store>" --today <YYYY-MM-DD> --out ~/.config/stretch/work/deals.json`. It reads the stores' current weekly ads from Flipp's public ad search over HTTPS and keeps only prices it can match to a recipe item and package size. Exit 0 means deals.json is written (it may hold few deals; `NO_AD_PRICE` lists the items without one, and a `WARNING` line names a store with no usable ad price or a store name it does not know). Exit 2 means a bad input. Exit 5 means the ad service could not be reached; then use the shelf-price step in references/weekly-autopilot.md. It sends only the ZIP and grocery item names, nothing about the student.
- Meal plan: `python3 scripts/plan_meals.py --profile ~/.config/stretch/work/profile.json --deals ~/.config/stretch/work/deals.json --today <YYYY-MM-DD>`. Add `--json` for full details and `--exclude <recipe-id>` to drop a recipe the student does not want. Exit 0 means a plan is ready. Exit 2 means a bad or missing input (the output explains). Exit 3 means nothing in the recipe library fits the kitchen and diet. Exit 4 means even the cheapest plan is over budget; the plan is printed anyway.
- Gear payback: `python3 scripts/payback.py --profile ~/.config/stretch/work/profile.json --home-meal-cost <dollars> --banned <comma-separated gear ids>`. Exit 0 or 2.
- Shelf and student prices: `python3 scripts/merge_prices.py --deals ~/.config/stretch/work/deals.json --shelf ~/.config/stretch/work/shelf_prices.json --today <YYYY-MM-DD> --out ~/.config/stretch/work/deals.json`. It checks the prices Cubbie read on store sites or the student sent, drops any that look wrong and says why, and merges the rest into deals.json. Exit 0 means merged (`NO_REAL_PRICE` lists items still without a real price). Exit 2 means a bad file; the ERROR line says what to fix.
- Monthly tally: `python3 scripts/tally.py --receipts ~/.config/stretch/work/receipts.json`. Exit 0 means a summary and a SAVE line are printed. Exit 2 means a bad file; the ERROR line says what to fix. It writes nothing.
- `--sample` runs any script on bundled fake data and never touches saved files.

How to read the results:

- Exit 3: tell the student the recipe library has nothing for that kitchen and diet yet, and offer the gear that would unlock the most (run the payback script).
- Exit 4: lead with the gap ("cheapest plan I found is $X over your $Y"), then offer to stretch it with fewer meals or a cheaper store.
- Prices marked "estimate" come from typical prices, not a store ad. Say which lines they are.
