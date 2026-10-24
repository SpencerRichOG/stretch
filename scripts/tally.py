#!/usr/bin/env python3
"""Tally a month of receipts by category (Stretch M5 money check).

Cubbie reads the student's receipt emails or receipt photos, writes what it found to a JSON file,
and passes the file in. This script never reads memory, never writes files and never sees card or
account numbers (it refuses a file that looks like it holds one).

Input (receipts.json):
  {
    "month": "2026-10",                          # optional; receipts outside it are skipped
    "transactions": [
      {"date": "2026-10-03", "time": "23:15",    # time is optional, local 24-hour clock
       "merchant": "ExampleEats",                 # optional
       "merchant_type": "food delivery app",      # optional
       "category": "food delivery", "amount": 18.40}
    ],
    "last_month": {"month": "2026-09", "totals": {"food delivery": 150.0}},   # optional
    "money_map": {"food delivery": 120, "groceries": 200}                       # optional, monthly
  }

  python3 scripts/tally.py --receipts receipts.json
  python3 scripts/tally.py --sample              # bundled, clearly fake data

Late night means a time from 22:00 to 03:59. Delivery means the category "food delivery".

Exit codes: 0 ok, 2 bad or missing input.
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
DELIVERY = "food delivery"
LATE_START, LATE_END = 22, 4          # 22:00 up to (not including) 04:00
MIN_SWING = 5.0                      # changes smaller than this are not worth a nudge
MAX_CATEGORIES = 15
LONG_DIGITS = re.compile(r"\d[\d -]{10,}\d")   # 12+ digits, possibly spaced: a card or account number


class TallyError(Exception):
    pass


def plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


def money(x):
    sign = "-" if x < 0 else ""
    return f"{sign}${abs(x):,.2f}"


def month_label(ym):
    try:
        return datetime.strptime(ym, "%Y-%m").strftime("%B %Y")
    except (TypeError, ValueError):
        return str(ym)


def check_no_numbers(obj, where):
    """Refuse anything that looks like a card or account number, anywhere in the file."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            check_no_numbers(v, f"{where}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            check_no_numbers(v, f"{where}[{i}]")
    elif isinstance(obj, str) and any(sum(ch.isdigit() for ch in m) >= 12 for m in LONG_DIGITS.findall(obj)):
        raise TallyError(f"{where} looks like a card or account number. Remove it; Stretch never stores those.")


def load(path):
    try:
        with open(path, encoding="utf-8-sig") as f:   # tolerate a BOM from Windows editors
            data = json.load(f)
    except FileNotFoundError:
        raise TallyError(f"file not found: {path}")
    except json.JSONDecodeError as e:
        raise TallyError(f"{path} is not valid JSON ({e.msg}, line {e.lineno}).")
    if not isinstance(data, dict) or not isinstance(data.get("transactions"), list):
        raise TallyError(f"{path} needs a \"transactions\" list.")
    check_no_numbers(data, "file")
    return data


def parse_tx(t, i):
    if not isinstance(t, dict):
        raise TallyError(f"transactions[{i}] is not an object.")
    try:
        day = datetime.strptime(str(t.get("date")), "%Y-%m-%d").date()
    except ValueError:
        raise TallyError(f"transactions[{i}] needs \"date\" as YYYY-MM-DD.")
    amount = t.get("amount")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise TallyError(f"transactions[{i}] needs \"amount\" as a number of dollars.")
    category = str(t.get("category") or "").strip().lower()
    if not category:
        raise TallyError(f"transactions[{i}] needs a \"category\".")
    hour = None
    if t.get("time") not in (None, ""):
        try:
            hour = datetime.strptime(str(t["time"]), "%H:%M").hour
        except ValueError:
            raise TallyError(f"transactions[{i}] \"time\" must be HH:MM (24-hour) or left out.")
    return {"day": day, "hour": hour, "category": category, "amount": float(amount)}


def number_map(obj, name):
    if obj is None:
        return {}
    if not isinstance(obj, dict):
        raise TallyError(f"\"{name}\" must be an object of category: dollars.")
    out = {}
    for k, v in obj.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise TallyError(f"\"{name}\" value for \"{k}\" must be a number.")
        out[str(k).strip().lower()] = float(v)
    return out


def tally(data):
    month = data.get("month")
    if month is not None:
        try:
            datetime.strptime(str(month), "%Y-%m")
        except ValueError:
            raise TallyError("\"month\" must be YYYY-MM.")
    txs = [parse_tx(t, i) for i, t in enumerate(data["transactions"])]
    skipped = 0
    if month:
        kept = [t for t in txs if t["day"].strftime("%Y-%m") == month]
        skipped = len(txs) - len(kept)
        txs = kept
    elif txs:
        month = max(t["day"] for t in txs).strftime("%Y-%m")

    totals = {}
    for t in txs:
        totals[t["category"]] = round(totals.get(t["category"], 0.0) + t["amount"], 2)

    delivery = [t for t in txs if t["category"] == DELIVERY]
    late = [t for t in delivery if t["hour"] is not None and (t["hour"] >= LATE_START or t["hour"] < LATE_END)]
    no_time = sum(1 for t in delivery if t["hour"] is None)

    last = data.get("last_month") or {}
    if not isinstance(last, dict):
        raise TallyError("\"last_month\" must be an object with \"month\" and \"totals\".")
    last_totals = number_map(last.get("totals"), "last_month.totals")
    money_map = number_map(data.get("money_map"), "money_map")

    swings = []
    if last_totals:
        for c in sorted(set(totals) | set(last_totals)):
            change = round(totals.get(c, 0.0) - last_totals.get(c, 0.0), 2)
            if abs(change) >= MIN_SWING:
                swings.append({"category": c, "this_month": totals.get(c, 0.0),
                               "last_month": last_totals.get(c, 0.0), "change": change, "against": "last month"})
    elif money_map:
        for c, planned in sorted(money_map.items()):
            change = round(totals.get(c, 0.0) - planned, 2)
            if change >= MIN_SWING:
                swings.append({"category": c, "this_month": totals.get(c, 0.0),
                               "planned": planned, "change": change, "against": "money map"})
    swings.sort(key=lambda s: -abs(s["change"]))

    return {
        "ok": True, "month": month, "receipts": len(txs), "skipped_other_months": skipped,
        "total": round(sum(totals.values()), 2),
        "totals": dict(sorted(totals.items(), key=lambda kv: -kv[1])),
        "delivery": {"orders": len(delivery), "spent": round(sum(t["amount"] for t in delivery), 2),
                     "average": round(sum(t["amount"] for t in delivery) / len(delivery), 2) if delivery else None,
                     "late_night_orders": len(late), "late_night_spent": round(sum(t["amount"] for t in late), 2),
                     "orders_without_time": no_time},
        "last_month": last.get("month") if last_totals else None,
        "money_map": money_map or None,
        "swings": swings[:3],
        "save": {"month": month, "totals": totals},
    }


def render_text(r):
    lines = [f"Money check for {month_label(r['month'])}: {plural(r['receipts'], 'receipt')}, total {money(r['total'])}.",
             "Only what the receipts show; anything paid without a receipt is missing."]
    if r["skipped_other_months"]:
        lines.append(f"Skipped {plural(r['skipped_other_months'], 'receipt')} from other months.")
    lines.append("By category:")
    items = list(r["totals"].items())
    for c, v in items[:MAX_CATEGORIES]:
        extra = ""
        if r["money_map"] and c in r["money_map"]:
            extra = f" (money map {money(r['money_map'][c])})"
        lines.append(f"- {c}: {money(v)}{extra}")
    if len(items) > MAX_CATEGORIES:
        rest = sum(v for _, v in items[MAX_CATEGORIES:])
        lines.append(f"- {len(items) - MAX_CATEGORIES} more categories: {money(rest)}")
    d = r["delivery"]
    if d["orders"]:
        lines.append(f"Delivery: {plural(d['orders'], 'order')}, {money(d['spent'])}, average {money(d['average'])}.")
        lines.append(f"Late-night delivery (10 pm to 4 am): {plural(d['late_night_orders'], 'order')}, {money(d['late_night_spent'])}.")
        if d["orders_without_time"]:
            lines.append(f"{plural(d['orders_without_time'], 'delivery receipt')} had no time, so not in the late-night count.")
    else:
        lines.append("Delivery: no orders found.")
    if r["swings"]:
        against = r["swings"][0]["against"]
        head = f"Biggest changes vs {month_label(r['last_month'])}:" if against == "last month" else "Over the money map:"
        lines.append(head)
        for s in r["swings"]:
            base = s.get("last_month", s.get("planned"))
            lines.append(f"- {s['category']}: {money(s['this_month'])} vs {money(base)} ({'+' if s['change'] > 0 else ''}{money(s['change'])})")
    elif r["last_month"]:
        lines.append(f"No category changed by {money(MIN_SWING)} or more vs {month_label(r['last_month'])}.")
    else:
        lines.append("No last-month totals given, so there is nothing to compare yet.")
    lines.append("SAVE (Stretch monthly totals): " + json.dumps(r["save"], separators=(",", ":")))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Monthly spending tally (Stretch M5).")
    ap.add_argument("--receipts", help="JSON file Cubbie wrote from the receipts it read")
    ap.add_argument("--json", action="store_true", help="print full details as JSON")
    ap.add_argument("--sample", action="store_true", help="use bundled fake data; writes nothing")
    args = ap.parse_args()
    try:
        if args.sample:
            args.receipts = args.receipts or str(ASSETS / "sample_transactions.json")
        if not args.receipts:
            raise TallyError("Pass --receipts receipts.json (or --sample to try it).")
        r = tally(load(args.receipts))
    except TallyError as e:
        print(f"ERROR: {e}")
        return 2
    out = json.dumps(r, indent=1, default=str) if args.json else render_text(r)
    if len(out) > 7500:
        out = out[:7500] + "\n(cut to stay under Cubbie's 8,000-character read limit)"
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
