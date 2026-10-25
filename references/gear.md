# M4 Gear that pays for itself

Recommend the few kitchen items that would save the student the most money, ranked by how fast each pays for itself. "No pan or rice cooker" often means every meal is bought, not made.

## Steps

1. Read the saved kitchen, housing and delivery habit from memory. If you do not know what a typical delivery order costs them, ask once ("What's a normal DoorDash order for you, about $18?").
2. Dorm rules first. If the student lives in a dorm, search their university's housing "what not to bring" or prohibited-items page, read it, and list the appliances it bans. Never suggest a banned item. Pass those to the script as `--banned` using the gear ids from `assets/gear.json` (toaster, air_fryer, rice_cooker, blender, microwave). For items the page does not mention, tell the student to check with housing before buying.
3. Run `scripts/payback.py` (see "Running the scripts" in SKILL.md). Use `home_cost_per_meal` from the latest `plan_meals.py --json` run for `--home-meal-cost`, or about 2.50 if there has been no plan yet, and say it is about.
4. Send one message with the top three items.

## The math

Payback is item price divided by what one delivery order costs minus what one home-cooked meal costs: that is the number of home-cooked meals to break even. It only means something when the item lets the student cook meals they could not make before and those meals replace ordering. The script therefore shows payback only for items that unlock at least one recipe, and labels items that unlock none as nice to have. Gear that needs another item (a pan needs a stove) is skipped with a note.

## Tiers

Prices are rough new, budget-brand estimates in `assets/gear.json`; say "around".

- Tier 1 (the set is around $50): pan, pot, chef's knife, cutting board, sheet pan, meal-prep containers.
- Tier 2: rice cooker or air fryer, blender, shaker bottle, toaster, and a microwave if the student has none.

Each new item unlocks more recipes in the weekly plan. Update Stretch kitchen in memory only after the student says they bought or now have it.

## Arizona State University housing

The ASU housing "What not to bring" checklist I found (2024 file, no date inside) bans open heating elements, naming toasters, hot plates and crock pots or instant pots, plus items that are not UL listed. It does not mention air fryers, rice cookers, microwaves, blenders or coffee makers. So for ASU dorm students: pass `--banned toaster`, and tell them to check with ASU Housing before buying an air fryer, rice cooker or blender. Re-check the current housing page when you can, because the checklist may have changed. Source: https://housing.asu.edu/sites/default/files/2024-06/2024-What-to-Bring-Checklist-Housing-061124.pdf

## Where to buy cheap

Mention these as places to look, with no promised prices: move-out sales at the end of the semester, Buy Nothing groups near campus, and back-to-school sales. Offer to search for a Buy Nothing group near their campus.

## The message

Example only; always use the numbers from payback.py's output:

```text
Cheapest way to start cooking:
1. Pan, about $12. You can't cook on the stove without one, and it opens up 4 more meals.
2. Pot, about $12. Pays back after about 1 home-cooked meal at your usual $18 order.
3. Check ASU housing before an air fryer, not sure it's allowed.
```

Keep it to three items. Mention the dorm rule whenever it changed the list.
