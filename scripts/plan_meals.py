#!/usr/bin/env python3
"""Fit a weekly meal-prep plan to a student's budget, kitchen and diet (Stretch M2).

Cubbie reads the student's saved profile and this week's store deals first, writes them as
two small JSON files, then runs this script for the exact math. See SKILL.md and
references/weekly-autopilot.md for the file formats.

  python3 scripts/plan_meals.py --profile profile.json --deals deals.json --today 2026-10-25
  python3 scripts/plan_meals.py --sample            # bundled sample data, touches nothing
  python3 scripts/plan_meals.py ... --exclude egg-fried-rice   # the student's "edit": leave a recipe out

Exit codes: 0 plan ready, 2 bad or missing input, 3 nothing fits the kitchen/diet,
4 cheapest plan is still over budget (the plan is printed anyway).
"""
import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import date, timedelta
from itertools import combinations, combinations_with_replacement

from stretchlib import (ASSETS, StretchError, convert, fail, feasible_recipes, load_json)

SAMPLE_TODAY = "2026-10-25"
FAMILY_REPEAT_PENALTY = 2.00  # dollars of "cost" charged per repeated recipe family (keeps the week varied)
SOURCE_LABELS = {"ad": "ad deal", "shelf": "shelf price", "student": "student price", "estimate": "estimate"}


def parse_day(text, label):
    try:
        return date.fromisoformat(str(text))
    except ValueError:
        raise StretchError(f"{label} must look like 2026-10-25 (got '{text}').")


def build_price_book(typical, deals, today):
    """Start from typical prices, then override with the cheapest valid store deal per item."""
    index = {}
    for name, info in typical["items"].items():
        index[name.lower()] = name
        for alias in info.get("aliases", []):
            index[alias.lower()] = name
    book = {}
    for name, info in typical["items"].items():
        pack = float(info["pack"])
        book[name] = {
            "unit": info["unit"], "pack": pack, "unit_price": float(info["pack_price"]) / pack,
            "loose": bool(info.get("loose", False)), "source": "estimate", "store": None,
        }
    notes = []
    for d in deals:
        raw = str(d.get("item", "")).strip().lower()
        name = index.get(raw)
        if name is None:
            notes.append(f"Ignored a deal for '{raw}' (not an item in the recipe library).")
            continue
        if "price" not in d:
            raise StretchError(f"The deal for '{raw}' has no price.")
        try:
            price = float(d["price"])
            size = float(d.get("size", 1))
        except (TypeError, ValueError):
            raise StretchError(f"The deal for '{raw}' needs a numeric price and size.")
        if price <= 0 or size <= 0:
            raise StretchError(f"The deal for '{raw}' needs a price and size above zero.")
        source = str(d.get("source") or "ad").strip().lower()
        if source not in ("ad", "shelf", "student"):
            raise StretchError(f"The deal for '{raw}' has an unknown source '{source}' (use ad, shelf or student).")
        until = d.get("valid_until")
        if until and parse_day(until, f"valid_until for '{raw}'") < today:
            notes.append(f"Skipped the expired deal for {name} (ended {until}).")
            continue
        base_unit = book[name]["unit"]
        pack_in_base = convert(size, d.get("unit") or base_unit, base_unit)
        unit_price = price / pack_in_base
        current = book[name]
        if current["source"] != "estimate" and current["unit_price"] <= unit_price:
            continue  # keep the cheaper deal
        loose = bool(d.get("loose", current["loose"]))
        book[name] = {"unit": base_unit, "pack": pack_in_base, "unit_price": unit_price, "loose": loose,
                      "source": source, "store": d.get("store")}
    return book, notes


def line_cost(entry, need):
    """Buy whole packs unless the item is sold loose by weight."""
    if entry["loose"]:
        return need, None, need * entry["unit_price"]
    packs = max(1, math.ceil(need / entry["pack"] - 1e-9))
    buy = packs * entry["pack"]
    return buy, packs, buy * entry["unit_price"]


def needs_for(combo, by_id):
    need = defaultdict(float)
    for rid in combo:
        for ing in by_id[rid]["ingredients"]:
            need[ing["item"]] += float(ing["amount"])
    return need


def total_cost(combo, by_id, book):
    return sum(line_cost(book[item], n)[2] for item, n in needs_for(combo, by_id).items())


def pick(feasible, batches, book, budget):
    """Return (combo, cost, over_budget, by_id).

    Among all ways to fill `batches` cooking batches, take the plan with the best
    variety-adjusted score that fits the budget. If none fits, take the cheapest one.
    """
    by_id = {r["id"]: r for r in feasible}
    within, cheapest = None, None
    # Different recipes each batch whenever the library allows it: a week of one dish is not a plan.
    pool = combinations if len(by_id) >= batches else combinations_with_replacement
    for combo in pool(sorted(by_id), batches):
        cost = total_cost(combo, by_id, book)
        families = {by_id[c]["family"] for c in combo}
        score = cost + FAMILY_REPEAT_PENALTY * (batches - len(families))
        if cheapest is None or cost < cheapest[0] - 1e-9:
            cheapest = (cost, combo)
        if cost <= budget + 1e-9 and (within is None or score < within[0] - 1e-9):
            within = (score, cost, combo)
    if within is not None:
        return within[2], within[1], False, by_id
    return cheapest[1], cheapest[0], True, by_id


def qty_text(qty, unit):
    q = f"{qty:.2f}".rstrip("0").rstrip(".")
    if unit == "each":
        return q
    if unit == "can":
        return f"{q} can" + ("" if q == "1" else "s")
    return f"{q} {unit}"


def money(x):
    return f"${x:,.2f}"


def build_result(profile, deals, today, recipes_doc, typical, exclude=frozenset()):
    budget = profile.get("weekly_food_budget")
    if not isinstance(budget, (int, float)) or budget <= 0:
        raise StretchError("The profile needs weekly_food_budget as a number above zero.")
    days = int(profile.get("days", 5))
    per_day = int(profile.get("meals_per_day", 2))
    if not (1 <= days <= 7 and 1 <= per_day <= 3):
        raise StretchError("days must be 1-7 and meals_per_day must be 1-3.")
    servings = int(recipes_doc.get("servings", 4))
    meals_needed = days * per_day
    batches = math.ceil(meals_needed / servings)

    book, notes = build_price_book(typical, deals, today)
    recipes = recipes_doc["recipes"]
    for r in recipes:  # catch library typos early
        for ing in r["ingredients"]:
            if ing["item"] not in book:
                raise StretchError(f"Recipe '{r['id']}' uses '{ing['item']}', which has no price entry.")

    feasible = [r for r in feasible_recipes(recipes, profile) if r["id"] not in exclude]
    if not feasible:
        return {"ok": False, "reason": "no_recipes"}, 3

    combo, cost, over, by_id = pick(feasible, batches, book, float(budget))
    need = needs_for(combo, by_id)
    shopping, estimated, from_deals, pantry = [], [], [], []
    for item in sorted(need):
        buy, packs, c = line_cost(book[item], need[item])
        entry = book[item]
        shopping.append({"item": item, "buy": round(buy, 3), "unit": entry["unit"], "packs": packs,
                         "cost": round(c, 2), "source": entry["source"], "store": entry["store"]})
        (estimated if entry["source"] == "estimate" else from_deals).append(item)
    sources = {k: sum(1 for s in shopping if s["source"] == k) for k in ("ad", "shelf", "student", "estimate")}
    for rid in combo:
        for p in by_id[rid].get("pantry", []):
            if p not in pantry:
                pantry.append(p)

    half = math.ceil(len(combo) / 2)
    groups = [combo[:half], combo[half:]]
    sessions = []
    for i, grp in enumerate([g for g in groups if g]):
        when = today + timedelta(days=0 if i == 0 else 3)
        sessions.append({"label": f"Cook session {i + 1}", "date": when.isoformat(), "day": when.strftime("%a %b %d"),
                         "recipes": [{"id": rid, "name": by_id[rid]["name"]} for rid in grp]})

    swap = next((by_id[r]["swap"] for r in combo if by_id[r].get("swap")), None)
    meals_covered = batches * servings
    result = {
        "ok": True, "over_budget": over, "total": round(cost, 2), "budget": float(budget),
        "left": round(float(budget) - cost, 2), "meals_needed": meals_needed, "meals_covered": meals_covered,
        "home_cost_per_meal": round(cost / meals_needed, 2),
        "sessions": sessions, "shopping_list": shopping, "deal_items": from_deals, "estimated_items": estimated,
        "price_sources": sources, "pantry_assumed": pantry, "swap": swap, "notes": notes, "recipes_considered": len(feasible),
    }
    d = profile.get("delivery") or {}
    if isinstance(d.get("avg_order"), (int, float)) and d["avg_order"] > 0:
        result["delivery_compare"] = {"avg_order": float(d["avg_order"]),
                                      "same_meals_delivered": round(d["avg_order"] * meals_needed, 2)}
    return result, (4 if over else 0)


def render_text(r):
    lines = []
    if r["over_budget"]:
        lines.append(f"OVER BUDGET: cheapest plan found is {money(r['total'])} vs {money(r['budget'])} "
                     f"(over by {money(-r['left'])}).")
    else:
        lines.append(f"Plan total {money(r['total'])} of {money(r['budget'])} budget ({money(r['left'])} left).")
    lines.append(f"Covers {r['meals_covered']} meals for {r['meals_needed']} needed, about "
                 f"{money(r['home_cost_per_meal'])} per meal.")
    for s in r["sessions"]:
        names = "; ".join(x["name"] for x in s["recipes"])
        lines.append(f"{s['label']} ({s['day']}): {names}")
    lines.append("Shopping list:")
    for it in r["shopping_list"]:
        label = SOURCE_LABELS[it["source"]]
        where = f"{label} at {it['store']}" if it["store"] and it["source"] != "estimate" else label
        lines.append(f"- {qty_text(it['buy'], it['unit'])} {it['item']}: {money(it['cost'])} ({where})")
    ps = r["price_sources"]
    lines.append(f"Real prices: {len(r['shopping_list']) - ps['estimate']} of {len(r['shopping_list'])} lines "
                 f"(ad {ps['ad']}, shelf {ps['shelf']}, student {ps['student']}); estimates: {ps['estimate']}.")
    if r["estimated_items"]:
        lines.append("Priced from typical prices, not a store deal: " + ", ".join(r["estimated_items"]) + ".")
    if r["pantry_assumed"]:
        lines.append("Assumes you already have: " + ", ".join(r["pantry_assumed"]) + ".")
    if r.get("delivery_compare"):
        dc = r["delivery_compare"]
        lines.append(f"For comparison, {r['meals_needed']} delivery meals at about {money(dc['avg_order'])} each "
                     f"is about {money(dc['same_meals_delivered'])}.")
    if r["swap"]:
        lines.append("Swap idea: " + r["swap"])
    for n in r["notes"]:
        lines.append("Note: " + n)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Budget meal-prep planner (Stretch M2).")
    ap.add_argument("--profile", help="profile.json (see SKILL.md)")
    ap.add_argument("--deals", help="deals.json from this week's ads (optional)")
    ap.add_argument("--today", help="the student's LOCAL date, YYYY-MM-DD")
    ap.add_argument("--recipes", default=str(ASSETS / "recipes.json"))
    ap.add_argument("--prices", default=str(ASSETS / "typical_prices.json"))
    ap.add_argument("--exclude", default="", help="comma-separated recipe ids to leave out (the student's 'edit')")
    ap.add_argument("--json", action="store_true", help="print full JSON instead of the short text")
    ap.add_argument("--sample", action="store_true", help="use bundled sample profile and deals")
    args = ap.parse_args()
    try:
        if args.sample:
            args.profile = args.profile or str(ASSETS / "sample_profile.json")
            args.deals = args.deals or str(ASSETS / "sample_deals.json")
            args.today = args.today or SAMPLE_TODAY
        if not args.profile:
            raise StretchError("Pass --profile profile.json (or --sample to try it).")
        if not args.today:
            raise StretchError("Pass --today YYYY-MM-DD with the student's local date.")
        today = parse_day(args.today, "--today")
        profile = load_json(args.profile, "profile")
        deals_doc = load_json(args.deals, "deals") if args.deals else []
        deals = deals_doc.get("deals", []) if isinstance(deals_doc, dict) else deals_doc
        recipes_doc = load_json(args.recipes, "recipes")
        typical = load_json(args.prices, "prices")
        exclude = {x.strip() for x in args.exclude.split(",") if x.strip()}
        known = {r["id"] for r in recipes_doc["recipes"]}
        unknown = sorted(exclude - known)
        if unknown:
            raise StretchError("Unknown recipe id(s) in --exclude: " + ", ".join(unknown))
        result, code = build_result(profile, deals, today, recipes_doc, typical, exclude)
    except StretchError as e:
        fail(str(e), 2)
        return
    if not result["ok"]:
        print("NO_RECIPES: nothing in the library fits this kitchen, diet and avoid list. "
              "Basic gear (see references/gear.md) would unlock options.")
        sys.exit(code)
    print(json.dumps(result, indent=2) if args.json else render_text(result))
    sys.exit(code)


if __name__ == "__main__":
    main()
