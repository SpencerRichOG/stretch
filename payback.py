#!/usr/bin/env python3
"""Rank kitchen gear by how fast it pays for itself (Stretch M4).

Payback math: item price / (what a delivery order costs - what a home-cooked meal costs)
= home-cooked meals to break even. Each item also shows how many MORE recipes it unlocks
for this student's kitchen and diet.

  python3 scripts/payback.py --profile profile.json --home-meal-cost 2.40 --banned toaster
  python3 scripts/payback.py --sample              # bundled sample data

Exit codes: 0 ok, 2 bad or missing input.
"""
import argparse
import json
import math
import sys

from stretchlib import (ASSETS, StretchError, fail, feasible_recipes, load_json, norm_equipment, student_filters)

SAMPLE_HOME_MEAL_COST = 2.40


def money(x):
    return f"${x:,.2f}"


def rank_gear(profile, recipes, gear, home_meal_cost, banned):
    _, _, _, kitchen = student_filters(profile)
    delivery = profile.get("delivery") or {}
    avg_order = delivery.get("avg_order")
    orders_per_week = delivery.get("orders_per_week")
    have_habit = isinstance(avg_order, (int, float)) and avg_order > 0
    saving = max(0.0, float(avg_order) - home_meal_cost) if have_habit else None

    current = feasible_recipes(recipes, profile)
    dorm = str(profile.get("housing", "")).lower() == "dorm"
    ranked, blocked, skipped_banned = [], [], []
    for g in gear:
        gid = norm_equipment(g["id"])
        if gid in kitchen:
            continue
        if gid in banned:
            skipped_banned.append(g["name"])
            continue
        missing = [r for r in g.get("requires", []) if norm_equipment(r) not in kitchen]
        if missing:
            blocked.append({"name": g["name"], "needs": missing})
            continue
        unlocked = len(feasible_recipes(recipes, profile, [gid])) - len(current)
        price = float(g["price"])
        if len(current) < 4 and unlocked >= 1:
            kind = "starter"
        elif unlocked >= 1:
            kind = "adds recipes"
        else:
            kind = "extra"
        # Payback only means something when the item lets the student cook meals they could not make before.
        meals = math.ceil(price / saving) if saving and saving > 0 and kind != "extra" else None
        weeks = round(meals / orders_per_week, 1) if meals and isinstance(orders_per_week, (int, float)) and orders_per_week > 0 else None
        ranked.append({
            "id": g["id"], "name": g["name"], "tier": g.get("tier"), "price": price, "kind": kind,
            "unlocks_recipes": unlocked, "meals_to_break_even": meals, "weeks_to_break_even": weeks,
            "check_housing": bool(dorm and g.get("housing") == "check"),
        })
    order = {"starter": 0, "adds recipes": 1, "extra": 2}
    ranked.sort(key=lambda x: (order[x["kind"]], x["weeks_to_break_even"] is None, x["weeks_to_break_even"] or 0,
                               -x["unlocks_recipes"], x["price"]))
    return {"ok": True, "recipes_possible_now": len(current), "home_meal_cost": home_meal_cost,
            "delivery_order_cost": float(avg_order) if have_habit else None, "saving_per_meal": saving,
            "ranked": ranked, "blocked": blocked, "skipped_banned": skipped_banned}


def render_text(r, top):
    lines = []
    if r["saving_per_meal"] is None:
        lines.append("No delivery habit given, so these are ranked by recipes unlocked, not by payback.")
    else:
        lines.append(f"Assumes a home meal replaces a delivery order (about {money(r['delivery_order_cost'])}) "
                     f"and costs about {money(r['home_meal_cost'])}, so each one saves about {money(r['saving_per_meal'])}.")
    lines.append(f"Recipes you can make now: {r['recipes_possible_now']}.")
    if not r["ranked"]:
        lines.append("No gear to suggest for this kitchen.")
    for i, it in enumerate(r["ranked"][:top], 1):
        label = {"starter": "starter gear", "adds recipes": "adds options", "extra": "nice to have, no new recipes"}[it["kind"]]
        bits = [f"{i}. {it['name']} (about {money(it['price'])})", label]
        if it["meals_to_break_even"] is not None:
            when = f"pays back after {it['meals_to_break_even']} home-cooked meal" + ("" if it["meals_to_break_even"] == 1 else "s")
            if it["weeks_to_break_even"] is not None:
                when += f" (about {it['weeks_to_break_even']} weeks)"
            bits.append(when)
        if it["unlocks_recipes"] > 0:
            bits.append(f"unlocks {it['unlocks_recipes']} more recipe" + ("" if it["unlocks_recipes"] == 1 else "s"))
        if it["check_housing"]:
            bits.append("check your housing rules first")
        lines.append("; ".join(bits))
    for b in r["blocked"]:
        lines.append(f"Skipped {b['name']}: needs {', '.join(b['needs'])}.")
    if r["skipped_banned"]:
        lines.append("Not suggested (housing rules): " + ", ".join(r["skipped_banned"]) + ".")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Gear payback ranking (Stretch M4).")
    ap.add_argument("--profile")
    ap.add_argument("--home-meal-cost", type=float, help="dollars per home-cooked meal (from plan_meals.py --json)")
    ap.add_argument("--banned", default="", help="comma-separated gear ids the student's housing bans")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--gear", default=str(ASSETS / "gear.json"))
    ap.add_argument("--recipes", default=str(ASSETS / "recipes.json"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--sample", action="store_true", help="use bundled sample profile")
    args = ap.parse_args()
    try:
        if args.sample:
            args.profile = args.profile or str(ASSETS / "sample_profile.json")
            if args.home_meal_cost is None:
                args.home_meal_cost = SAMPLE_HOME_MEAL_COST
        if not args.profile:
            raise StretchError("Pass --profile profile.json (or --sample to try it).")
        if args.home_meal_cost is None:
            raise StretchError("Pass --home-meal-cost with dollars per home-cooked meal (plan_meals.py prints it).")
        if args.home_meal_cost < 0:
            raise StretchError("--home-meal-cost cannot be negative.")
        profile = load_json(args.profile, "profile")
        recipes = load_json(args.recipes, "recipes")["recipes"]
        gear = load_json(args.gear, "gear")["items"]
        banned = {norm_equipment(b) for b in args.banned.split(",") if b.strip()}
        result = rank_gear(profile, recipes, gear, args.home_meal_cost, banned)
    except StretchError as e:
        fail(str(e), 2)
        return
    print(json.dumps(result, indent=2) if args.json else render_text(result, args.top))


if __name__ == "__main__":
    main()
