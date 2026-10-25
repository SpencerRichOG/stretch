# M2 Sunday autopilot

A scheduled check-in, run as a background task, that ends in one message. It also runs on demand when a student asks what to eat this week.

## Steps

1. Read the student's saved stores, weekly food budget, diet, dislikes, kitchen, memberships and delivery habit from memory. A missing store list never stops the plan: with no saved stores, or only Walmart, use ALDI, Target, Fry's and Safeway at ZIP 85281 if the school is ASU or unknown (elsewhere, the student's ZIP and no store filter), and say so in one line, for example "I used ALDI, Target, Fry's and Safeway near ASU, the stores with this week's ads. Walmart's ads and shelf prices usually aren't available to me. Tell me your stores to change that." Never promise Walmart shelf prices. If the weekly budget or the kitchen is truly missing and the student did not just give it, ask one short question for only that piece, then continue once they answer. A one-off amount ("$41 until Friday") is for this run only and is never saved as the weekly budget; see `days` in `references/onboarding.md`.
2. Find real prices, best source first. Go to the next tier only for items that still have no real price.
   - Tier 1, weekly ads. Run `fetch_deals.py` (see "Running the scripts" in SKILL.md) with the student's ZIP, their saved stores (at most four; with none saved or only Walmart, the defaults from step 1) and their local date. It writes `~/.config/stretch/work/deals.json` itself; never type prices into that file. Quote store names and prices from its output exactly. Some prices need the store's card or a digital coupon (the fetch output and the plan's shopping list say "with card" or "with coupon"); say so in a few words when you quote one, and never present it as a regular shelf price.
     - A `WARNING: unknown store` line: ask the student once to check the store's name, and plan with the other stores meanwhile.
     - A `WARNING: no usable ad prices from <store>` line: that store's items go to Tier 2, or straight to Tier 3 if `assets/store_sites.json` marks the store "blocked" and its one try fails.
     - Exit 0 with zero deals for the saved stores: rerun once without `--stores` to see every store near the ZIP. If another store has better prices, mention it in one line, but plan with the student's own stores unless they say otherwise.
     - Exit 5 (the ad service could not be reached): go on to Tier 2 for every item.
   - Tier 2, shelf prices. Do this as a background task. For the items still listed under `NO_AD_PRICE` (every item after exit 5), look up the regular price on each saved store's own public website, one store at a time. Start with the items that are the biggest part of the plan's cost, and do at most about 12 lookups per store and about 25 in all. For each item, search the web for "<store> <item> price <ZIP>", or open the store's public product search page in the browser (address patterns are in `assets/store_sites.json`; for a store not listed there, use its "generic" entry). Read only what the page shows: the price, the package size and unit, the store location or "online price" label, and the page address. Choose the plain store-brand or cheapest regular item in a normal size.
     - A store whose `status` in `assets/store_sites.json` is "blocked" (Walmart, Fry's, Safeway and CVS, from a plain fetch on 2026-10-24) gets one lookup in the browser. If that one lookup shows a robot check or fails, skip the store and go straight to Tier 3 for its items.
     - If any store's site shows a robot check, a sign-in wall or a location prompt that needs sign-in, or fails to load, stop after that one try for that store, note it as blocked, and send its items straight to Tier 3; go on with the other stores. Never retry, never sign in for the student, and never work around a check.
     - Never write down a price you did not see on the page. Leaving an item out is better than guessing.
     - Write what you saw to `~/.config/stretch/work/shelf_prices.json` (format below), then run `python3 scripts/merge_prices.py --deals ~/.config/stretch/work/deals.json --shelf ~/.config/stretch/work/shelf_prices.json --today <YYYY-MM-DD> --out ~/.config/stretch/work/deals.json`. It drops rows that look wrong and prints why; do not add them back. `NO_REAL_PRICE` lists the items that still have no real price.
   - Tier 3, the student. For at most the 3 costliest items under `NO_REAL_PRICE` (including the items of a store that was blocked or failed once), add one line to the plan message: "Can you text me a photo of the price tag or your cart total for X?" Read the photo, or accept a typed price. Add each price to shelf_prices.json with "kind": "student" and today's date, rerun merge_prices.py and plan_meals.py, and send the updated total. Ask once a week at most.
   - Tier 4, estimates. Everything else uses typical prices, and plan_meals.py labels those lines "estimate".
3. Write `profile.json` from memory (see `references/onboarding.md`), then run `plan_meals.py` with the student's local date (see "Running the scripts" in SKILL.md). Use `--json` once so you also have `home_cost_per_meal` for the gear ranking.
4. Handle the exit code as SKILL.md describes.
5. Send one message (format below).
6. Perk nudge: if the saved memberships or subscriptions match a perks finding (see `references/perks.md`), send at most one short second text about it. One per week at most, and skip it if you sent that finding recently.
7. Wait for the student's reply.

## deals.json

```json
{
  "deals": [
    {"store": "Fry's", "item": "chicken thighs", "price": 1.99, "size": 1, "unit": "lb", "valid_until": "2026-10-28"},
    {"store": "Fry's", "item": "rice", "price": 2.00, "size": 2, "unit": "lb", "valid_until": "2026-10-28"},
    {"store": "Fry's", "item": "eggs", "price": 2.49, "size": 1, "unit": "dozen", "valid_until": "2026-10-28"}
  ]
}
```

- `price` is what the store charges for `size` of `unit`. Units understood: lb, oz, g, kg, each, ct, dozen, can, gal, qt, pt, floz, l, ml.
- `valid_until` is the ad's last day, as YYYY-MM-DD. Expired deals are ignored.
- Meat and produce sold by weight are priced per pound. Packaged goods are priced per package (a 2 lb bag of rice at $2.00 is size 2, unit lb, price 2.00).
- If two stores both list an item, put both in; the script keeps the cheaper one and records the store.
- Do not copy a price you did not see. Leaving an item out is better than guessing.
- `fetch_deals.py` also adds `ad_text` (the ad's wording) and `condition` ("with card"); `plan_meals.py` ignores them. `merge_prices.py` adds `source` (ad, shelf or student), `url` and `note`.

## shelf_prices.json

Cubbie writes this file only from prices it saw on a store's page (kind "shelf") or that the student sent (kind "student").

```json
{"prices": [
  {"store": "Target", "item": "eggs", "price": 1.49, "size": 12, "unit": "each", "seen_on": "2026-10-24",
   "url": "https://www.target.com/...", "kind": "shelf", "note": "online price"}
]}
```

- `item` is a recipe-library name (the keys of `assets/typical_prices.json`). `size` and `unit` work as in deals.json.
- `seen_on` is the date the price was read. Rows older than 4 days are dropped.
- `url` is the page address; leave it out for a student photo. `note` says "online price" or the store location, plus "with card" if it is a member price.
- Never put card or account numbers in this file. merge_prices.py refuses any file that contains one.

## The message

One message, plain text, lead with the total:

```text
This week's plan: $23.40 of your $41.
Deals: chicken drumsticks or thighs $1.99/lb, rice $2, eggs $2.49 (Fry's, ends Tue).
Sun: fried rice + rice and beans. Wed: chicken rice bowls.
Swap idea: frozen veggies instead of fresh saves a little.
Reply 1 build cart, 2 edit, 3 skip.
```

- Include the swap idea only if the script returned one.
- Mention the delivery comparison only if the student has a delivery habit, and only as one short line.
- Add one short line on where prices came from, taken from the plan's "Real prices" line, for example "9 of 12 prices are real (store ads, store sites or your photo); 3 are estimates." If a store blocked the lookup, add half a line: "Walmart's site blocked me; its items are estimates until you send a price."
- The full shopping list is not in the first message. Send it when the student replies 2 or asks for it, as plain lines.

## Replies

- "1": build the cart (below).
- "2": ask what to change (a recipe they dislike, a lower budget, a store). Rerun `plan_meals.py`, using `--exclude` for a recipe they do not want or a changed profile for a new budget, and send the new plan in the same format.
- "3": do nothing, keep the schedule, and say you will be back next Sunday.

## Delivery price check

Only when the student has a delivery habit. Compare one typical order with the planned home meal, in one short line. Delivery apps are only a comparison, never a price source for groceries.

- Prices come from the student, who types or screenshots the restaurant's menu price and the fees shown before checkout, or from the restaurant's public menu page on DoorDash or Uber Eats, opened once in the browser without signing in.
- If the site asks for an address or sign-in, or shows a robot check, stop and ask the student for a screenshot instead.
- Label it "menu price plus fees as shown, about", for example "That $14 bowl was about $21 with fees; tonight's home meal is about $1.70."
- Never place an order, never start a membership or trial, and never sign in for the student.

## Building the cart

Use the cart site the student saved (default Target.com, with pickup or same-day delivery; Walmart.com and Instacart are options the student can choose, and DoorDash is one for students elsewhere). Do this only after the student replies 1.

1. Open the site in the browser. If the student is not signed in, ask them to sign in through a secure login page or by taking over the browser. This is the only sign-in Stretch needs.
2. Search each item on the shopping list and add the closest match in the right size at the lowest price. If an item is out of stock, pick the nearest substitute and tell the student, or leave it out and say so.
3. Do not start any free trial or paid membership the site offers, and do not choose a delivery or pickup slot the student has not picked.
4. Show the cart in one text: item count, the site's total, and how it compares to the plan. Prices at checkout can differ from the ad, so say so in half a line. If any plan price came from a store other than the cart site (for example a Fry's or ALDI ad with a Target cart), say so in one short line, for example "The Fry's and ALDI deals aren't in this Target cart, so the total can differ from the plan's ad prices."
5. Hand the browser to the student and tell them to review and pay. Never pay, never enter payment details, never accept terms for them.

If the site blocks you (a robot check, a login that will not work, a page that will not load), stop after one try. Do not keep retrying. Send the shopping list as plain lines, say which part was blocked, and let the student shop from the list.
