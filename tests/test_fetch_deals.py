"""Offline checks for fetch_deals.py parsing (no network). Run: python3 tests/test_fetch_deals.py"""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import fetch_deals as f  # noqa: E402
from stretchlib import ASSETS, load_json  # noqa: E402

RICE = f.ITEMS["rice"]
TYPICAL = load_json(ASSETS / "typical_prices.json", "prices")
TODAY = date(2026, 10, 25)


def hit(name, price, post="ea", merchant="Safeway"):
    return {"merchant_name": merchant, "name": name, "current_price": price, "post_price_text": post,
            "valid_to": "2026-10-28T06:59:59+00:00"}


class MultiProductSize(unittest.TestCase):
    def test_one_matching_part_is_read(self):
        name = "signature select tomatoes 14.5-15 oz., rice 16 oz. or beans 15-15.5 oz."
        self.assertEqual(f.read_size(name, RICE), (16.0, "oz"))

    def test_two_matching_parts_rejected(self):
        self.assertIsNone(f.read_size("mahatma rice 2 lb or jasmine rice 5 lb", RICE))

    def test_range_inside_matching_part_rejected(self):
        self.assertIsNone(f.read_size("tomatoes 14.5 oz., rice 16-32 oz. or beans 15 oz.", RICE))

    def test_no_matching_part_rejected(self):
        self.assertIsNone(f.read_size("tomatoes 14.5 oz. or beans 15 oz.", RICE))

    def test_row_from_multi_product_ad(self):
        rows = f.deals_from_items("rice", [hit("Signature SELECT Tomatoes 14.5-15 oz., Rice 16 oz. or Beans 15-15.5 oz.",
                                               0.69, "ea With Coupon")], [], TODAY, -7, TYPICAL)
        self.assertEqual([(r["price"], r["size"], r["unit"], r.get("condition")) for r in rows],
                         [(0.69, 16.0, "oz", "ea with coupon")])

    def test_sample_two_part_rice_row_dropped(self):
        sample = load_json(f.SAMPLE_FILE, "sample")
        rows = f.deals_from_items("rice", sample["rice"], ["safeway"], TODAY, -7, TYPICAL)
        self.assertEqual(rows, [])


class OtherRules(unittest.TestCase):
    def test_case_only_price_rejected(self):
        rows = f.deals_from_items("canned tuna", [hit("Celebrity TUNA Chunk White, Solid White", 84.95, "cs")],
                                  [], TODAY, -7, TYPICAL)
        self.assertEqual(rows, [])

    def test_pasta_sides_rejected(self):
        self.assertFalse(f.matches("knorr pasta or rice sides", f.ITEMS["pasta"]))

    def test_chicken_without_per_pound_price_rejected(self):
        rows = f.deals_from_items("chicken thighs", [hit("Fresh Chicken Drumsticks", 5, "With Card")],
                                  [], TODAY, -7, TYPICAL)
        self.assertEqual(rows, [])


class PrintedLines(unittest.TestCase):
    def row(self, store, ad_text, condition=None):
        d = {"store": store, "item": "chicken thighs", "price": 0.99, "size": 1.0, "unit": "lb",
             "valid_until": "2026-10-27", "ad_text": ad_text}
        if condition:
            d["condition"] = condition
        return d

    def test_drumsticks_label(self):
        self.assertEqual(f.deal_line(self.row("ALDI", "Fresh Family Pack Chicken Drumsticks")),
                         "- chicken, drumsticks: $0.99 for 1 lb at ALDI, ends 2026-10-27")

    def test_mixed_cuts_label(self):
        d = self.row("Fry's Food Stores", "Fresh Foster Farms Whole Chicken, Drumsticks or Thighs", "lb with card")
        self.assertEqual(f.deal_line(d), "- chicken, drumsticks or thighs: $0.99 for 1 lb at Fry's Food Stores "
                                         "(lb with card), ends 2026-10-27")

    def test_thighs_and_no_ad_text_keep_the_name(self):
        self.assertEqual(f.deal_line(self.row("Wild Fork", "Chicken Thighs 5 LB Bag")),
                         "- chicken thighs: $0.99 for 1 lb at Wild Fork, ends 2026-10-27")
        self.assertTrue(f.deal_line(self.row("ALDI", None)).startswith("- chicken thighs: "))

    def test_same_helper_as_plan_meals(self):
        import plan_meals
        self.assertIs(f.ad_label, plan_meals.ad_label)


if __name__ == "__main__":
    unittest.main()
