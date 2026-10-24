# M2 Sunday autopilot

A scheduled check-in, run as a background task, that ends in one message. It also runs on demand when a student asks what to eat this week.

## Steps

1. Read the student's saved stores, weekly food budget, diet, dislikes, kitchen, memberships and delivery habit from memory. If the stores, budget or kitchen are missing, send one question for the missing piece and stop.
2. Find this week's deals. For each saved store (at most two), search the web for its current weekly ad or deals page near the student's ZIP, open it, and read it. Record only prices you actually read, and only for items in the recipe library. The library's item names are the keys of `assets/typical_prices.json` (chicken thighs, rice, eggs, black beans and so on). Write what you found to `~/.config/stretch/work/deals.json` (format below). If a store's ad cannot be read, skip that store, use typical prices, and say so in the message.
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

## The message

One message, plain text, lead with the total:

```text
This week's plan: $23.40 of your $41.
Deals: chicken thighs $1.99/lb, rice $2, eggs $2.49 (Fry's, ends Tue).
Sun: fried rice + rice and beans. Wed: chicken rice bowls.
Swap idea: frozen veggies instead of fresh saves a little.
Reply 1 build cart, 2 edit, 3 skip.
```

- Include the swap idea only if the script returned one.
- Mention the delivery comparison only if the student has a delivery habit, and only as one short line.
- If some items are estimates, add "a few prices are estimates" in one short line.
- The full shopping list is not in the first message. Send it when the student replies 2 or asks for it, as plain lines.

## Replies

- "1": build the cart (below).
- "2": ask what to change (a recipe they dislike, a lower budget, a store). Rerun `plan_meals.py`, using `--exclude` for a recipe they do not want or a changed profile for a new budget, and send the new plan in the same format.
- "3": do nothing, keep the schedule, and say you will be back next Sunday.

## Building the cart

Use the cart site the student saved (default Walmart.com, with pickup or delivery; Instacart and DoorDash are options for students elsewhere). Do this only after the student replies 1.

1. Open the site in the browser. If the student is not signed in, ask them to sign in through a secure login page or by taking over the browser. This is the only sign-in Stretch needs.
2. Search each item on the shopping list and add the closest match in the right size at the lowest price. If an item is out of stock, pick the nearest substitute and tell the student, or leave it out and say so.
3. Do not start any free trial or paid membership the site offers, and do not choose a delivery or pickup slot the student has not picked.
4. Show the cart in one text: item count, the site's total, and how it compares to the plan. Prices at checkout can differ from the ad, so say so in half a line.
5. Hand the browser to the student and tell them to review and pay. Never pay, never enter payment details, never accept terms for them.

If the site blocks you (a robot check, a login that will not work, a page that will not load), stop after one try. Do not keep retrying. Send the shopping list as plain lines, say which part was blocked, and let the student shop from the list.
