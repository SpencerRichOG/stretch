#!/usr/bin/env python3
"""Merge shelf prices Cubbie read on store websites, and prices the student sent, into deals.json (Stretch M2).

Weekly-ad prices come from fetch_deals.py. For items still without one, Cubbie reads the store's own public
product page, or the student texts a price-tag photo, and writes what it saw to shelf_prices.json. This script
checks every row, drops anything that looks wrong and says why, and writes one deals.json for plan_meals.py
with every row labeled by source: ad, shelf or student.

  python3 scripts/merge_prices.py --deals deals.json --shelf shelf_prices.json --today 2026-10-24 --out deals.json
  python3 scripts/merge_prices.py --sample     # bundled fake data, writes nothing

Exit codes: 0 merged (even if no shelf row was kept), 2 bad input.
"""
import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

from stretchlib import ASSETS, StretchError, convert, fail, load_json

SAMPLE_DEALS = ASSETS / "sample_deals.json"
SAMPLE_SHELF = ASSETS / "sample_shelf_prices.json"
SAMPLE_TODAY = "2026-10-25"
MAX_AGE_DAYS = 4        # an older shelf price is stale
VALID_DAYS = 3          # a shelf price counts as this week's price for seen_on + 3 days
LOW, HIGH = 0.25, 4.0   # a unit price outside 25%..400% of typical is probably a misread size
KINDS = ("shelf", "student")
MAX_LINES = 25          # per printed list, keeps output far below Cubbie's 8,000-character read
LONG_DIGITS = re.compile(r"\d[\d -]{10,}\d")   # 12+ digits, possibly spaced: a card or account number (as tally.py)


def check_no_numbers(obj, where):
    """Refuse anything that looks like a card or account number. Page addresses are skipped: product URLs carry UPCs."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k != "url":
                check_no_numbers(v, f"{where}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            check_no_numbers(v, f"{where}[{i}]")
    elif isinstance(obj, str) and any(sum(ch.isdigit() for ch in m) >= 12 for m in LONG_DIGITS.findall(obj)):
        raise StretchError(f"{where} looks like a card or account number. Remove it; Stretch never stores those.")
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool) and len(str(int(abs(obj)))) >= 12:
        raise StretchError(f"{where} looks like a card or account number. Remove it; Stretch never stores those.")


def library_index(typical):
    index = {}
    for name, info in typical["items"].items():
        index[name.lower()] = name
        for alias in info.get("aliases", []):
            index[alias.lower()] = name
    return index


def off_typical(item, price, size, unit, amount, typical):
    """A reason to drop a price far from typical (probably a misread size), or None if it looks sane."""
    info = typical["items"][item]
    ratio = (price / amount) / (float(info["pack_price"]) / float(info["pack"]))
    if ratio < LOW or ratio > HIGH:
        return f"${price:.2f} for {size:g} {unit} is {ratio:.0%} of the typical price; probably a misread size"
    return None


def check_ad_row(d, index, typical):
    """A reason to drop an ad row whose price is far from typical, or None. Rows it cannot read pass through
    unchanged, so plan_meals.py reports them as it always has."""
    item = index.get(str(d.get("item", "")).strip().lower())
    if item is None:
        return None
    try:
        price = float(d["price"])
        size = float(d.get("size", 1))
        unit = str(d.get("unit") or typical["items"][item]["unit"])
        amount = convert(size, unit, typical["items"][item]["unit"])
    except (KeyError, TypeError, ValueError, StretchError):
        return None
    if price <= 0 or amount <= 0:
        return None
    return off_typical(item, price, size, unit, amount, typical)


def check_row(row, index, typical, today):
    """(deal, None) for a good row, or (None, reason) for one to drop. Never guesses a missing value."""
    if not isinstance(row, dict):
        return None, "not a price row"
    store = str(row.get("store") or "").strip()
    raw_item = str(row.get("item") or "").strip().lower()
    item = index.get(raw_item)
    if not store:
        return None, "no store"
    if item is None:
        return None, f"'{raw_item}' is not an item in the recipe library"
    kind = str(row.get("kind") or "shelf").strip().lower()
    if kind not in KINDS:
        return None, f"kind must be shelf or student (got '{kind}')"
    try:
        price = float(row.get("price"))
        size = float(row.get("size", 1))
    except (TypeError, ValueError):
        return None, "price and size must be numbers"
    if not (price > 0 and size > 0):
        return None, "price and size must be above zero"
    info = typical["items"][item]
    base = info["unit"]
    unit = str(row.get("unit") or base).strip().lower()
    if base == "can" and unit in ("oz", "floz") and size <= 30:
        size, unit = 1.0, "can"  # one standard can, priced by the can like the library
    try:
        amount = convert(size, unit, base)
    except StretchError:
        return None, f"unit '{unit}' cannot be turned into {base}"
    try:
        seen = date.fromisoformat(str(row.get("seen_on")))
    except ValueError:
        return None, "seen_on must be a date like 2026-10-24"
    if seen > today:
        return None, f"seen_on {seen} is after today"
    if (today - seen).days > MAX_AGE_DAYS:
        return None, f"seen on {seen}, more than {MAX_AGE_DAYS} days ago"
    why = off_typical(item, price, size, unit, amount, typical)
    if why:
        return None, why
    deal = {"store": store, "item": item, "price": round(price, 2), "size": size, "unit": unit,
            "valid_until": (seen + timedelta(days=VALID_DAYS)).isoformat(), "source": kind, "seen_on": seen.isoformat()}
    url = str(row.get("url") or "").strip()
    if url.startswith("https://"):
        deal["url"] = url.split("#")[0].split("?")[0]
    note = str(row.get("note") or "").strip()
    if note:
        deal["note"] = note[:80]
    return deal, None


def still_valid(d, today):
    try:
        return not d.get("valid_until") or date.fromisoformat(str(d["valid_until"])) >= today
    except ValueError:
        return False


def main():
    ap = argparse.ArgumentParser(description="Merge shelf and student prices into deals.json (Stretch M2).")
    ap.add_argument("--deals", help="deals.json from fetch_deals.py (a missing file means no ad prices)")
    ap.add_argument("--shelf", help="shelf_prices.json that Cubbie wrote")
    ap.add_argument("--today", help="the student's LOCAL date, YYYY-MM-DD")
    ap.add_argument("--out", help="where to write the merged deals.json (may be the same as --deals)")
    ap.add_argument("--sample", action="store_true", help="use bundled fake data and write nothing")
    args = ap.parse_args()
    notes = []
    try:
        typical = load_json(ASSETS / "typical_prices.json", "prices")
        if args.sample:
            args.deals = args.deals or str(SAMPLE_DEALS)
            args.shelf = args.shelf or str(SAMPLE_SHELF)
            args.today = args.today or SAMPLE_TODAY
        if not args.shelf:
            raise StretchError("Pass --shelf shelf_prices.json (or --sample to try it).")
        if not args.today:
            raise StretchError("Pass --today YYYY-MM-DD with the student's local date.")
        try:
            today = date.fromisoformat(args.today)
        except ValueError:
            raise StretchError(f"--today must look like 2026-10-25 (got '{args.today}').")
        deals_doc = {"deals": []}
        if args.deals:
            deals_path = Path(args.deals).expanduser()
            if deals_path.exists():
                deals_doc = load_json(deals_path, "deals")
            else:
                notes.append(f"No ad deals file at {args.deals}; merging shelf and student prices only.")
        shelf_doc = load_json(Path(args.shelf).expanduser(), "shelf prices")
        check_no_numbers(deals_doc, "deals")
        check_no_numbers(shelf_doc, "shelf prices")
        ad_rows = deals_doc.get("deals", []) if isinstance(deals_doc, dict) else deals_doc
        shelf_rows = shelf_doc.get("prices") if isinstance(shelf_doc, dict) else None
        if not isinstance(ad_rows, list):
            raise StretchError("The deals file needs a \"deals\" list.")
        if not isinstance(shelf_rows, list):
            raise StretchError("The shelf prices file needs a \"prices\" list.")
    except StretchError as e:
        fail(str(e), 2)
        return

    index = library_index(typical)
    merged, dropped = [], []
    for i, d in enumerate(ad_rows, 1):
        if not isinstance(d, dict):
            continue
        if str(d.get("source") or "").lower() in KINDS:
            continue  # from an earlier merge; shelf_prices.json is the full list, so a rerun never doubles them
        why = check_ad_row(d, index, typical)
        if why:
            dropped.append(f"DROPPED ad row {i} ({d.get('store') or '?'}, {d.get('item') or '?'}): {why}")
            continue
        merged.append(dict(d, source="ad"))
    ad_count = len(merged)
    ad_dropped = len(dropped)
    kept = []
    for i, row in enumerate(shelf_rows, 1):
        deal, why = check_row(row, index, typical, today)
        if deal:
            kept.append(deal)
        else:
            who = ", ".join(str(row.get(k) or "?") for k in ("store", "item")) if isinstance(row, dict) else "?"
            dropped.append(f"DROPPED row {i} ({who}): {why}")
    merged.extend(kept)

    if args.out and not args.sample:
        doc = dict(deals_doc) if isinstance(deals_doc, dict) else {}
        doc["_merged"] = f"shelf and student prices merged for {today.isoformat()}"
        doc["deals"] = merged
        out = Path(args.out).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(doc, indent=2), encoding="utf-8")

    print(f"MERGED: {len(kept)} shelf or student prices kept, {len(dropped) - ad_dropped} dropped; "
          f"{ad_count} ad prices kept from deals.json, {ad_dropped} dropped.")
    for d in kept[:MAX_LINES]:
        extra = ", ".join(x for x in (f"seen {d['seen_on']}", d.get("note")) if x)
        print(f"- {d['item']}: ${d['price']:.2f} for {d['size']:g} {d['unit']} at {d['store']} "
              f"({'shelf price' if d['source'] == 'shelf' else 'student price'}, {extra})")
    for line in dropped[:MAX_LINES]:
        print(line)
    stores = []
    for d in merged:
        tag = f"{d.get('store') or '?'} ({d['source']})"
        if tag not in stores:
            stores.append(tag)
    if stores:
        print("STORES: " + ", ".join(stores))
    real = {index.get(str(d.get("item", "")).strip().lower()) for d in merged if still_valid(d, today)}
    missing = [name for name in typical["items"] if name not in real]
    if missing:
        print("NO_REAL_PRICE: " + ", ".join(missing)
              + " (ask the student about the costliest few; plan_meals.py uses estimates for the rest).")
    for n in notes:
        print("NOTE: " + n)
    if args.out and args.sample:
        print("NOTE: --sample never writes --out.")
    elif args.out:
        print(f"WROTE: {args.out}")
    else:
        print("NOTE: no --out given, nothing written.")
    sys.exit(0)


if __name__ == "__main__":
    main()
