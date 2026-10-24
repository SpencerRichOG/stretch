# M1 Money Map onboarding

Run this the first time a student uses Stretch. It takes about five minutes over a few texts. Save every answer to memory as you go, so Cubbie never asks twice, and let the student skip anything.

## How to ask

- Two or three questions per message, no more. Suggest a default where one exists.
- Rough numbers are fine. "Not sure" is a valid answer; move on.
- Never ask for a bank login, card number or account number. Never ask about visa or citizenship status.

## The questions, in order

1. Where. University, whether they live in a dorm or off campus, ZIP code, and whether they have a car. Save as Stretch university, with housing as dorm or off-campus.
2. Stores. Search for grocery stores near the student's campus or ZIP, on-campus markets and dining, then ask "which of these do you actually use?" Save the answer as Stretch stores. Keep at most two for weekly deals. Also ask which site they'd use for a grocery cart (default Walmart.com) and save it with Stretch stores.
3. Delivery and memberships. DoorDash, Uber One, Instacart, Prime, a campus meal plan. Save as Stretch memberships, with what they pay each month if they know.
4. Food. Weekly food budget (suggest a number they can say yes to), diet (none, vegetarian, vegan or pescatarian), dislikes or foods to avoid, and cooking skill (none, basic or comfortable). Save as Stretch weekly food budget, diet, dislikes and cooking skill. Also ask roughly how many delivery or takeout orders a week they place and what a typical one costs; that powers the comparison and the gear payback. Save that as the delivery habit under Stretch memberships.
5. Kitchen. Ask them to reply with what they have: microwave, stove, oven, pan, pot, knife, cutting board, blender, air fryer, rice cooker, toaster, sheet pan. Save as Stretch kitchen. If they live in a dorm, ask whether they have shared kitchen access, and save that with Stretch kitchen.
6. Money Map starter categories. Housing, food, transport (including a parking pass), subscriptions (including AI tools), school costs, health (gym, supplements, insurance), personal and fun, income. Rough monthly numbers; any category can be skipped. Save as Stretch money map and Stretch subscriptions.
7. Open end. "Anything else you pay for regularly?" Add each new category to the map.
8. Schedule. Which day and time for the weekly text. Default Sunday 6 pm in the student's local time. Confirm their time zone (for ASU, America/Phoenix, which has no daylight saving). Save day, time and time zone as Stretch schedule. Do not create the check-in until the student agrees to a time. Create only this weekly check-in, nothing monthly.

## What to send at the end

One short summary text, then create the weekly check-in.

Example:

```text
Here's your Money Map:
Food budget $41/week. Kitchen: microwave, pan, pot.
Stores: Fry's and Walmart.
Subscriptions: about $34/month across 4.
I'll text your meal-prep plan every Sunday at 6 pm.
```

Create the weekly check-in worded so it still makes sense days later:

"Stretch weekly plan: read the student's saved Stretch profile from memory (stores, weekly food budget, diet and dislikes, kitchen, memberships, delivery habit), then follow references/weekly-autopilot.md in the Stretch skill, using today's date in the student's saved time zone (Stretch schedule) for --today, and send one message that ends with 'Reply 1 build cart, 2 edit, 3 skip'. Do this as a background task."

## The profile.json format

Build this file from memory every time a script needs it. Save it as `~/.config/stretch/work/profile.json`. Leave out any field you do not know; the defaults are shown.

```json
{
  "weekly_food_budget": 41,
  "diet": "none",
  "avoid": ["mushrooms"],
  "kitchen": ["microwave", "stove", "pan", "pot", "knife", "cutting_board"],
  "cooking_skill": "basic",
  "days": 5,
  "meals_per_day": 2,
  "housing": "dorm",
  "delivery": {"orders_per_week": 3, "avg_order": 18.0}
}
```

- `weekly_food_budget` (required): dollars, a number above zero. For a one-off request like "I have $41 until Friday", use that amount for that run only. Set `days` to today through the named day, counting both (Saturday to Friday is 7), at most 7, and keep `meals_per_day` as saved (default 2). Say the day count in one short line so the student can correct it. Never save the one-off amount as Stretch weekly food budget; do save a kitchen answer as Stretch kitchen.
- `diet`: none, vegetarian, vegan or pescatarian. `avoid`: words for foods to leave out.
- `kitchen`: equipment names in lowercase with underscores (cutting_board, air_fryer, rice_cooker, sheet_pan). Common spellings like "skillet" or "stovetop" are understood.
- `cooking_skill`: none, basic or comfortable. `days`: 1 to 7. `meals_per_day`: 1 to 3.
- `housing` (from Stretch university): "dorm" makes the gear ranking add "check your housing rules" notes.
- `delivery` (the delivery habit in Stretch memberships): leave it out if the student has no delivery habit.

The names in "What Stretch remembers" (SKILL.md) are the shared contract: every module reads and writes memory under those same labels.
