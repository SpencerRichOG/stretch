#!/usr/bin/env python3
"""Fetch this week's real store ad prices near a ZIP and write deals.json (Stretch M2).

Reading weekly-ad pages in a browser is slow and often blocked, so this script asks Flipp's
public weekly-ad search (the data behind flipp.com, HTTPS JSON, no key) for each item in the
recipe library and keeps only prices it can tie to a library item and a package size.

  python3 scripts/fetch_deals.py --zip 85281 --stores "Fry's,Walmart" --today 2026-10-25 --out deals.json
  python3 scripts/fetch_deals.py --sample      # bundled saved response, no network, touches nothing

Every price written is one the store's ad shows. An item whose size cannot be read from the ad
is left out rather than guessed, so plan_meals.py falls back to a typical price and labels it.

Exit codes: 0 deals written (possibly none), 2 bad input, 5 could not reach the ad service.
"""
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from stretchlib import ASSETS, StretchError, convert, fail, load_json

SEARCH_URL = "https://backflipp.wishabi.com/flipp/items/search"
SAMPLE_FILE = ASSETS / "sample_flipp.json"
SAMPLE_TODAY = "2026-10-25"

# How to find each library item in an ad. "words" must all appear (as word starts) in the ad text,
# "any" lists alternatives where at least one must appear, "bad" rejects look-alikes.
# "fallback" is a package size used only when the ad names the item but not its size, and only for
# items sold in one standard size (a dozen eggs, a 15 oz can).
ITEMS = {
    "chicken thighs": {"q": "chicken thighs", "words": ["chicken"], "any": ["thigh", "drumstick", "leg quarter"],
                       "bad": ["breaded", "nugget", "cooked", "rotisserie", "wing", "breast", "boneless skinless breast",
                               "frozen fried", "sausage", "broth", "soup", "dog", "cat"]},
    "ground turkey": {"q": "ground turkey", "words": ["ground", "turkey"], "bad": ["sausage", "jerky", "deli", "burger patties"]},
    "eggs": {"q": "eggs", "words": ["egg"], "bad": ["noodle", "roll", "nog", "plant", "liquid", "egg white", "salad", "bites",
                                                    "dye", "chocolate", "easter", "drop"],
             "fallback": (12, "each")},
    "rice": {"q": "rice", "words": ["rice"], "bad": ["cake", "krispie", "vinegar", "roni", "cooked", "microwav", "ready",
                                                     "noodle", "bowl", "cauliflower", "pudding", "cereal", "chex", "wine",
                                                     "milk", "cracker", "side", "seasoned", "spanish", "fried", "mexican"]},
    "pasta": {"q": "pasta", "any": ["pasta", "spaghetti", "penne", "macaroni", "rotini", "elbows"],
              "bad": ["sauce", "salad", "cheese", "kit", "dinner", "frozen", "fresh", "ravioli", "tortellini", "helper"],
              "fallback": (1, "lb")},
    "pasta sauce": {"q": "pasta sauce", "any": ["pasta sauce", "marinara", "spaghetti sauce"],
                    "bad": ["alfredo", "pesto", "vodka"], "fallback": (1, "each")},
    "black beans": {"q": "black beans", "words": ["black", "bean"], "bad": ["dry", "dried", "soup", "chips", "refried"],
                    "fallback": (1, "can")},
    "chickpeas": {"q": "chickpeas", "any": ["chickpea", "garbanzo"], "bad": ["hummus", "pasta", "snack", "dry", "dried"],
                  "fallback": (1, "can")},
    "lentils": {"q": "lentils", "words": ["lentil"], "bad": ["soup", "pasta", "chips", "snack"]},
    "diced tomatoes": {"q": "diced tomatoes", "words": ["tomato"], "any": ["diced", "canned"],
                       "bad": ["sauce", "paste", "soup", "fresh", "grape", "cherry", "roma"], "fallback": (1, "can")},
    "tortillas": {"q": "tortillas", "words": ["tortilla"], "bad": ["chip", "strips", "soup", "kit", "bowl"]},
    "shredded cheese": {"q": "shredded cheese", "words": ["shredded"], "any": ["cheese", "cheddar", "mozzarella", "blend"],
                        "bad": ["plant", "dairy free"]},
    "salsa": {"q": "salsa", "words": ["salsa"], "bad": ["chip", "verde chicken", "seasoning", "mix", "dip"],
              "fallback": (1, "each")},
    "frozen broccoli": {"q": "frozen broccoli", "words": ["broccoli"], "any": ["frozen", "steam", "florets"],
                        "bad": ["cheese sauce", "rice", "fresh", "crown", "slaw"]},
    "frozen mixed vegetables": {"q": "frozen mixed vegetables", "words": ["vegetable"], "any": ["mixed", "frozen", "blend"],
                                "bad": ["oil", "broth", "soup", "chips", "juice", "fresh", "tray", "platter"]},
    "frozen spinach": {"q": "frozen spinach", "words": ["spinach"], "any": ["frozen", "chopped", "cut leaf"],
                       "bad": ["dip", "salad", "baby", "fresh", "artichoke"]},
    "onions": {"q": "onions", "words": ["onion"], "bad": ["ring", "soup", "dip", "powder", "green", "fried", "crispy", "chips"]},
    "carrots": {"q": "carrots", "words": ["carrot"], "bad": ["cake", "juice", "baby food", "chips"]},
    "potatoes": {"q": "potatoes", "words": ["potato"], "bad": ["chip", "salad", "tots", "fries", "mashed", "hash", "sweet",
                                                           "frozen", "skins", "soup", "bread", "rolls"]},
    "peanut butter": {"q": "peanut butter", "words": ["peanut", "butter"], "bad": ["cup", "cookie", "cracker", "bar",
                                                                                   "candy", "powder", "pretzel", "filled"]},
    "canned tuna": {"q": "canned tuna", "words": ["tuna"], "bad": ["steak", "fillet", "sushi", "fresh", "kit", "salad",
                                                                   "pouch", "frozen"],
                    "fallback": (1, "can")},
    "tofu": {"q": "tofu", "words": ["tofu"], "bad": ["dessert", "noodle", "skin", "puff"], "fallback": (1, "each")},
}

UNIT_WORDS = {
    "lb": "lb", "lbs": "lb", "pound": "lb", "pounds": "lb", "oz": "oz", "ounce": "oz", "ounces": "oz",
    "fl oz": "floz", "fl. oz": "floz", "kg": "kg", "g": "g", "ct": "ct", "count": "ct", "pk": "ct", "pack": "ct",
    "dozen": "dozen", "doz": "dozen", "gal": "gal", "gallon": "gal", "qt": "qt", "pt": "pt",
}
SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:-\s*\d+(?:\.\d+)?\s*)?(fl\.? oz|lbs?|pounds?|ounces?|oz|kg|g|ct|count|pk|pack|"
                     r"dozen|doz|gallon|gal|qt|pt)\b\.?", re.I)
RANGE_RE = re.compile(r"\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\s*(?:fl\.? oz|lbs?|oz|ct)", re.I)
MULTI_RE = re.compile(r"(\d+)\s*(?:for|/)\s*$", re.I)


def has_word(text, word):
    return re.search(r"\b" + re.escape(word), text) is not None


def matches(name, rule):
    if any(has_word(name, w) for w in rule.get("bad", [])):
        return False
    if not all(has_word(name, w) for w in rule.get("words", [])):
        return False
    alts = rule.get("any")
    return not alts or any(has_word(name, w) for w in alts)


def read_size(name, rule):
    """(size, unit) from the ad text, or the item's standard size, or None if it cannot be told."""
    if RANGE_RE.search(name):
        return None  # "14.5-15 oz" style ranges cover several products; do not guess which one
    sizes = SIZE_RE.findall(name)
    if len(sizes) == 1:
        amount, word = sizes[0]
        unit = UNIT_WORDS.get(word.lower().rstrip("."), UNIT_WORDS.get(word.lower().replace(".", "")))
        if unit and float(amount) > 0:
            return float(amount), unit
    if len(sizes) > 1:
        return None  # several products in one ad block
    if has_word(name, "dozen"):
        return 12.0, "each"
    return rule.get("fallback")


def per_unit_price(raw):
    """Price for one unit of what the ad sells, and whether it is a per-pound price. None if unusable."""
    price = raw.get("current_price")
    if price in (None, "") or float(price) <= 0:
        return None
    price = float(price)
    pre = str(raw.get("pre_price_text") or "").strip()
    post = str(raw.get("post_price_text") or "").strip().lower()
    m = MULTI_RE.search(pre)
    if m:
        price = price / int(m.group(1))
    elif pre and re.search(r"\d", pre):
        return None  # "buy 2 get 1" and similar; the real per-item price is not clear
    if "%" in post or "off" in post.split():
        return None  # a discount, not a price
    per_lb = bool(re.search(r"(^|/|\b)lbs?\b", post))
    return round(price, 2), per_lb, post


def local_day(stamp, offset_hours):
    if not stamp:
        return None
    try:
        dt = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (dt.astimezone(timezone(timedelta(hours=offset_hours)))).date()


def store_match(merchant, wanted):
    m = merchant.lower().replace("’", "'")
    return not wanted or any(w in m for w in wanted)


def deals_from_items(item_name, raw_items, wanted_stores, today, offset_hours, typical):
    """Turn one item's raw ad hits into deals.json rows: the cheapest per store, with a readable size."""
    rule = ITEMS[item_name]
    base_unit = typical["items"][item_name]["unit"]
    best = {}
    for raw in raw_items:
        merchant = str(raw.get("merchant_name") or raw.get("merchant") or "").strip()
        name = str(raw.get("name") or "").strip()
        if not merchant or not name or not store_match(merchant, wanted_stores):
            continue
        text = name.lower()
        if not matches(text, rule):
            continue
        priced = per_unit_price(raw)
        if not priced:
            continue
        price, per_lb, post = priced
        if per_lb:
            size, unit = 1.0, "lb"
        else:
            if rule is ITEMS["chicken thighs"]:
                continue  # chicken packs vary in weight; only trust a per-pound price
            got = read_size(text, rule)
            if not got:
                continue
            size, unit = got
            if unit == "ct":
                unit = "each"
            if base_unit == "can" and unit in ("oz", "floz", "g") and size <= 30:
                size, unit = 1.0, "can"  # one standard can, priced by the can like the library
        if unit != base_unit and rule.get("fallback") and rule["fallback"][1] == base_unit:
            try:
                convert(size, unit, base_unit)
            except StretchError:
                size, unit = rule["fallback"]  # a 24 oz jar of a by-the-jar item is one jar
        try:
            amount_in_base = convert(size, unit, base_unit)
        except StretchError:
            continue  # e.g. a can size for an item the library prices by the pound
        if amount_in_base <= 0:
            continue
        until = local_day(raw.get("valid_to"), offset_hours)
        if until and until < today:
            continue
        start = local_day(raw.get("valid_from"), offset_hours)
        if start and start > today + timedelta(days=7):
            continue
        row = {"store": merchant, "item": item_name, "price": price, "size": size, "unit": unit,
               "valid_until": until.isoformat() if until else None, "ad_text": name[:120]}
        if any(w in post for w in ("card", "coupon", "member", "rewards")):
            row["condition"] = post[:60]
        unit_cost = price / amount_in_base
        if merchant not in best or unit_cost < best[merchant][0]:
            best[merchant] = (unit_cost, row)
    return [row for _, row in sorted(best.values(), key=lambda t: t[0])]


def fetch_item(query, zip_code, timeout):
    params = urllib.parse.urlencode({"locale": "en-us", "postal_code": zip_code, "q": query})
    req = urllib.request.Request(f"{SEARCH_URL}?{params}", headers={
        "User-Agent": "Mozilla/5.0 (Stretch skill for Cubbie)", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8")).get("items", [])


def main():
    ap = argparse.ArgumentParser(description="Fetch real weekly-ad prices into deals.json (Stretch M2).")
    ap.add_argument("--zip", help="the student's 5-digit ZIP code")
    ap.add_argument("--stores", default="", help="comma-separated store names to keep (empty keeps every store)")
    ap.add_argument("--today", help="the student's LOCAL date, YYYY-MM-DD")
    ap.add_argument("--out", help="where to write deals.json")
    ap.add_argument("--items", default="", help="comma-separated library items to look up (default: all)")
    ap.add_argument("--utc-offset", type=float, default=-7, help="student's UTC offset in hours (Arizona is -7)")
    ap.add_argument("--timeout", type=float, default=15)
    ap.add_argument("--sample", action="store_true", help="use a bundled saved response, no network")
    args = ap.parse_args()
    try:
        typical = load_json(ASSETS / "typical_prices.json", "prices")
        if args.sample:
            args.zip = args.zip or "85281"
            args.today = args.today or SAMPLE_TODAY
        if not args.zip or not re.fullmatch(r"\d{5}", args.zip):
            raise StretchError("Pass --zip with a 5-digit US ZIP code (or --sample to try it).")
        if not args.today:
            raise StretchError("Pass --today YYYY-MM-DD with the student's local date.")
        try:
            today = date.fromisoformat(args.today)
        except ValueError:
            raise StretchError(f"--today must look like 2026-10-25 (got '{args.today}').")
        wanted = [s.strip().lower().replace("’", "'") for s in args.stores.split(",") if s.strip()]
        items = [s.strip().lower() for s in args.items.split(",") if s.strip()] or list(ITEMS)
        unknown = [i for i in items if i not in ITEMS]
        if unknown:
            raise StretchError("Unknown item(s): " + ", ".join(unknown) + ". Use names from assets/typical_prices.json.")
        sample = load_json(SAMPLE_FILE, "sample") if args.sample else None
    except StretchError as e:
        fail(str(e), 2)
        return

    deals, missing, failures = [], [], 0
    for item in items:
        try:
            raw = sample.get(item, []) if sample is not None else fetch_item(ITEMS[item]["q"], args.zip, args.timeout)
        except (urllib.error.URLError, OSError, ValueError) as e:
            failures += 1
            missing.append(item)
            if failures >= 3 and not deals:
                fail(f"Could not reach the weekly-ad service ({e.__class__.__name__}). Read the store ad pages instead.", 5)
            continue
        found = deals_from_items(item, raw, wanted, today, args.utc_offset, typical)
        if found:
            deals.extend(found)
        else:
            missing.append(item)
        if sample is None:
            time.sleep(0.2)

    if failures and failures == len(items):
        fail("Could not reach the weekly-ad service. Read the store ad pages instead.", 5)

    doc = {"_source": f"Flipp weekly ads near {args.zip}, fetched for {today.isoformat()}"
                      + (" (SAMPLE, not real prices)" if args.sample else ""),
           "deals": deals}
    if args.out and not args.sample:
        out = Path(args.out).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(doc, indent=2), encoding="utf-8")

    stores = sorted({d["store"] for d in deals})
    print(f"DEALS: {len(deals)} real ad prices for {len({d['item'] for d in deals})} of {len(items)} items"
          + (f" from {', '.join(stores)}." if stores else "."))
    for d in deals[:25]:
        cond = f" ({d['condition']})" if d.get("condition") else ""
        ends = f", ends {d['valid_until']}" if d.get("valid_until") else ""
        print(f"- {d['item']}: ${d['price']:.2f} for {d['size']:g} {d['unit']} at {d['store']}{cond}{ends}")
    if missing:
        print("NO_AD_PRICE: " + ", ".join(missing) + " (plan_meals.py will use typical prices and mark them estimates).")
    if failures:
        print(f"NOTE: {failures} lookup(s) failed to load; those items count as missing.")
    if args.out and args.sample:
        print("NOTE: --sample never writes --out.")
    elif args.out:
        print(f"WROTE: {args.out}")
    sys.exit(0)


if __name__ == "__main__":
    main()
