#!/usr/bin/env python3
"""Fetch real shelf prices from the nearest Target into deals.json (Stretch M2). No sign-up, no student key.

Weekly ads only list what is on sale, so most of a shopping list used to fall back to estimates.
Target's website loads its prices from a public JSON service (redsky.target.com) using a site key
that is embedded in every target.com page. This script reads that key from the homepage (falling
back to known values), finds the nearest Target to the ZIP, and searches each recipe item there.
It is not an official API and may change; on failure it exits 5 and the plan uses ad prices.

  python3 scripts/target_prices.py --zip 85281 --today 2026-10-25 --out deals.json
  python3 scripts/target_prices.py --sample      # bundled saved response, no network, touches nothing

With --out pointing at an existing deals.json (from fetch_deals.py), its rows are kept and these
are added; plan_meals.py uses the cheapest valid price per item.

Exit codes: 0 prices written, 2 bad input, 5 Target could not be reached.
"""
import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from fetch_deals import ITEMS, matches, read_size
from stretchlib import ASSETS, StretchError, convert, fail, load_json

REDSKY = "https://redsky.target.com/redsky_aggregations/v1/web"
# Public site keys seen in target.com's own pages; the live one is read from the homepage first.
KNOWN_KEYS = ["9f36aeafbe60771e321a7cc95a78140772ab3e96", "ff457966e64d5e877fdbad070f276d18ecec4a01"]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
SAMPLE_FILE = ASSETS / "sample_target.json"
SAMPLE_TODAY = "2026-10-25"
VISITOR = "0190000000000000STRETCH0000000000"


def get(url, timeout, accept="application/json"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept,
                                               "Origin": "https://www.target.com", "Referer": "https://www.target.com/"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def site_keys(timeout):
    keys = []
    try:
        page = get("https://www.target.com/", timeout, accept="text/html")
        keys += re.findall(r'"apiKey"\s*:\s*"([0-9a-f]{40})"', page)
        keys += re.findall(r'apiKey\\?"\s*:\s*\\?"([0-9a-f]{40})', page)
    except (urllib.error.URLError, OSError, ValueError):
        pass
    seen, out = set(), []
    for k in keys + KNOWN_KEYS:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def find_stores(node):
    """Every dict carrying a store_id, wherever the response nests them."""
    if isinstance(node, dict):
        if "store_id" in node:
            yield node
        for v in node.values():
            yield from find_stores(v)
    elif isinstance(node, list):
        for v in node:
            yield from find_stores(v)


def nearest_store(key, zip_code, timeout):
    q = urllib.parse.urlencode({"limit": 5, "within": 15, "place": zip_code, "key": key, "channel": "WEB"})
    doc = json.loads(get(f"{REDSKY}/nearby_stores_v1?{q}", timeout))
    stores = list(find_stores(doc))
    return stores[0] if stores else None


def search(key, term, store_id, timeout):
    q = urllib.parse.urlencode({
        "key": key, "channel": "WEB", "keyword": term, "page": f"/s/{term}", "count": 24, "offset": 0,
        "pricing_store_id": store_id, "store_ids": store_id, "visitor_id": VISITOR,
        "default_purchasability_filter": "true"})
    doc = json.loads(get(f"{REDSKY}/plp_search_v2?{q}", timeout))
    return ((doc.get("data") or {}).get("search") or {}).get("products") or []


def money(text):
    m = re.search(r"\$\s*(\d+(?:\.\d+)?)", str(text or ""))
    return float(m.group(1)) if m else None


def store_label(store):
    name = str(store.get("location_name") or "").strip()
    return f"Target ({name})" if name else "Target"


def rows_for_item(item_name, products, store, today, typical):
    """The cheapest product per unit that matches the library item and has a readable size."""
    rule = ITEMS[item_name]
    base_unit = typical["items"][item_name]["unit"]
    best = None
    for p in products:
        title = html.unescape(str(((p.get("item") or {}).get("product_description") or {}).get("title") or "")).strip()
        text = title.lower()
        if not title or not matches(text, rule):
            continue
        price = p.get("price") or {}
        shown = str(price.get("formatted_current_price") or "")
        if "-" in shown or "see" in shown.lower():
            continue  # a price range across sizes or "see price in cart"; not one clear price
        now = price.get("current_retail") or money(shown)
        if not now or float(now) <= 0:
            continue
        now = float(now)
        regular = price.get("reg_retail") or money(price.get("formatted_comparison_price")) or now
        regular = max(float(regular), now)
        if re.search(r"/\s*lb\b|per lb|per pound", shown.lower() + " " + text):
            size, unit = 1.0, "lb"  # priced per pound
        else:
            got = read_size(text, rule)
            if not got:
                continue
            size, unit = got
            if unit == "ct":
                unit = "each"
            if base_unit == "can" and unit in ("oz", "floz", "g") and size <= 30:
                size, unit = 1.0, "can"
        if item_name == "chicken thighs" and unit != "lb":
            continue  # chicken packs vary in weight; only trust a per-pound price or a stated weight
        if unit != base_unit and rule.get("fallback") and rule["fallback"][1] == base_unit:
            try:
                convert(size, unit, base_unit)
            except StretchError:
                size, unit = rule["fallback"]  # a 24 oz jar of a by-the-jar item is one jar
        try:
            amount = convert(size, unit, base_unit)
        except StretchError:
            continue
        if amount <= 0:
            continue
        on_sale = now < regular - 0.005
        row = {"store": store_label(store), "item": item_name, "price": round(now, 2), "size": size, "unit": unit,
               "valid_until": today.isoformat(), "kind": "sale" if on_sale else "shelf", "ad_text": title[:120]}
        if on_sale:
            row["regular_price"] = round(regular, 2)
        cost = now / amount
        if best is None or cost < best[0]:
            best = (cost, row)
    return [best[1]] if best else []


def merge(existing_path, new_rows):
    """Keep rows from another source (weekly ads), replace this script's earlier rows."""
    p = Path(existing_path).expanduser()
    if not p.exists():
        return new_rows
    try:
        old = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return new_rows
    old_rows = old.get("deals", []) if isinstance(old, dict) else old
    return [r for r in old_rows if r.get("kind") not in ("shelf", "sale")] + new_rows


def main():
    ap = argparse.ArgumentParser(description="Real Target shelf prices into deals.json (Stretch M2).")
    ap.add_argument("--zip", help="the student's 5-digit ZIP code")
    ap.add_argument("--today", help="the student's LOCAL date, YYYY-MM-DD")
    ap.add_argument("--out", help="deals.json to write (rows from fetch_deals.py already in it are kept)")
    ap.add_argument("--store-id", help="a Target store id, to skip the nearest-store lookup")
    ap.add_argument("--items", default="", help="comma-separated library items (default: all)")
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
        items = [s.strip().lower() for s in args.items.split(",") if s.strip()] or list(ITEMS)
        unknown = [i for i in items if i not in ITEMS]
        if unknown:
            raise StretchError("Unknown item(s): " + ", ".join(unknown) + ". Use names from assets/typical_prices.json.")
        sample = load_json(SAMPLE_FILE, "sample") if args.sample else None
    except StretchError as e:
        fail(str(e), 2)
        return

    key = None
    if sample is not None:
        store = sample["store"]
    else:
        store, last_error = None, "no response"
        for k in site_keys(args.timeout):
            if args.store_id:
                store = {"store_id": args.store_id}
            else:
                try:
                    store = nearest_store(k, args.zip, args.timeout)
                except urllib.error.HTTPError as e:
                    last_error = f"HTTP {e.code}"
                    continue  # most likely a stale key; try the next one
                except (urllib.error.URLError, OSError, ValueError) as e:
                    fail(f"Could not reach Target ({e.__class__.__name__}). Use fetch_deals.py prices only.", 5)
            if store:
                key = k
                break
        if not key:
            fail(f"Could not find a Target near {args.zip} ({last_error}). Use fetch_deals.py prices only.", 5)

    rows, missing, failures = [], [], 0
    for item in items:
        try:
            products = sample.get(item, []) if sample is not None else search(
                key, ITEMS[item]["q"], store["store_id"], args.timeout)
        except (urllib.error.URLError, OSError, ValueError):
            failures += 1
            missing.append(item)
            if failures >= 3 and not rows:
                fail("Target stopped answering product searches. Use fetch_deals.py prices only.", 5)
            continue
        found = rows_for_item(item, products, store, today, typical)
        rows.extend(found) if found else missing.append(item)
        if sample is None:
            time.sleep(0.3)
    if failures and failures == len(items):
        fail("Could not load any Target prices. Use fetch_deals.py prices only.", 5)

    label = store_label(store)
    if args.out and not args.sample:
        out = Path(args.out).expanduser()
        all_rows = merge(out, rows)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"_source": f"Target shelf prices at {label} plus any weekly ads, "
                                              f"for {today.isoformat()}", "deals": all_rows}, indent=2),
                       encoding="utf-8")

    print(f"PRICES: {len(rows)} of {len(items)} items priced at {label}, store {store.get('store_id')}"
          + (" (SAMPLE, not real prices)." if args.sample else "."))
    for r in rows[:25]:
        extra = f" (on sale, usually ${r['regular_price']:.2f})" if r.get("regular_price") else ""
        print(f"- {r['item']}: ${r['price']:.2f} for {r['size']:g} {r['unit']}{extra}")
    if missing:
        print("NO_PRICE: " + ", ".join(missing) + " (not matched at this store; plan_meals.py uses an ad price or estimate).")
    if failures:
        print(f"NOTE: {failures} lookup(s) failed to load; those items count as missing.")
    if args.out and args.sample:
        print("NOTE: --sample never writes --out.")
    elif args.out:
        print(f"WROTE: {args.out}")
    sys.exit(0)


if __name__ == "__main__":
    main()
