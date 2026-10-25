# M5 Monthly money check

Once a month (default the 1st), show the student where last month's money went, by category, and send two or three specific nudges with dollar amounts. Spending information comes only from receipt emails, receipt photos the student sends, and what the student types. No bank logins, no bank statements.

## Steps

1. Decide the month. On the scheduled check-in, use the month that just ended. If the student asks ("where did my money go?"), use the month they name, or last month.
2. Collect receipts.
   - If Gmail is connected, search it read-only for that month's receipts: food delivery, rideshare, groceries, restaurants, subscriptions and renewals ("your receipt", "order confirmation", "payment received", "your subscription").
   - If Gmail is not connected, ask once to connect it. If the student would rather not, ask them to type what they spent (place, rough amount, rough date) or to text receipt photos, and carry on with that.
   - Read any receipt photos the student sends.
3. Write `~/.config/stretch/work/receipts.json` (`mkdir -p` it first). For each receipt keep only the date, the local time if shown, the merchant name, the kind of merchant, the amount and one category. Use the student's Money Map categories, plus "food delivery" for delivery orders so the script can count them. Never write card numbers, account numbers, addresses or what was ordered. Add, if saved:
   - `last_month`: the previous month from Stretch monthly totals;
   - `money_map`: the monthly numbers from Stretch money map.
   The format is at the top of `scripts/tally.py`.
4. Run `python3 scripts/tally.py --receipts ~/.config/stretch/work/receipts.json` from this skill's folder.
   - Exit 0: a summary is printed.
   - Exit 2: one line starting with `ERROR` says what is wrong with the file. Fix the file and run it again. If you cannot, tell the student something went wrong on your side and give the totals in words.
5. Save the `SAVE` line's month and totals as Stretch monthly totals, in plain words ("Stretch monthly totals: October 2026: food delivery $140.95, groceries $104.25, ..."). Keep only the last three months. Save nothing else from the receipts.
6. Re-run the perks audit in `references/perks.md` against the subscriptions found. Mention only findings that are new since last month.
7. Send the reply (format below).

## Reply

Short plain text, like a friend texting. Lead with the number that matters. Then two or three nudges, each with a dollar amount from the script's output and something the student can take or leave. The student can say "skip" at any time.

- Base the nudges on the biggest changes, the late-night delivery count and anything over the Money Map. If nothing stands out, say so in one line and skip the nudges.
- Use only numbers the script printed, and say "about" when you round. Do not estimate savings the script did not print.
- Never shame. A month that went up is information, not a failure.
- Say the totals cover only receipts Stretch saw.
- End with the choices, for example "Reply 1 add freezer meals to Sunday's plan, 2 check my subscriptions, 3 skip."

Example reply (numbers from the sample data; always use the numbers from tally.py's output):

```text
October: about $347 across 16 receipts I could see.
Delivery was the big one: about $141 in 7 orders, up about $69 from September.
1. 5 of those orders were after 10 pm, $101.40 in total. I can add freezer meals to Sunday's plan for late nights.
2. Groceries were down about $36. Nice.
3. Your subscriptions are about $33 a month. Want me to check them for student prices?
Reply 1 add freezer meals, 2 check subscriptions, 3 skip.
```

## The monthly check-in

Create it only after the student agrees to a day and time. The default is the 1st of the month, at their weekly check-in time and in their time zone (Stretch schedule). Word it so it still makes sense days later:

"Stretch monthly money check: read references/money-check.md in the Stretch skill. Check the student's receipt emails from last month (or ask for receipt photos), tally them by category with the tally script, compare with the saved Stretch monthly totals and Money Map, text two or three nudges with dollar amounts, and save the new monthly totals."
