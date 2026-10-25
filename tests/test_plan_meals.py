"""Offline checks for plan_meals.py labels (no network). Run: python3 tests/test_plan_meals.py"""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import plan_meals as p  # noqa: E402
from stretchlib import ASSETS, load_json  # noqa: E402

TODAY = date(2026, 10, 24)
PROFILE = {"weekly_food_budget": 41, "kitchen": ["microwave", "stove", "pan", "pot"], "days": 5, "meals_per_day": 2}
ALDI = {"store": "ALDI", "item": "chicken thighs", "price": 0.99, "size": 1, "unit": "lb", "valid_until": "2026-10-27",
        "ad_text": "Fresh Family Pack Chicken Drumsticks"}
FRYS = {"store": "Fry's Food Stores", "item": "chicken thighs", "price": 0.99, "size": 1, "unit": "lb",
        "valid_until": "2026-10-27", "ad_text": "Fresh Foster Farms Whole Chicken, Drumsticks or Thighs",
        "condition": "lb with card"}


def chicken_line(deal):
    result, _ = p.build_result(PROFILE, [deal], TODAY, load_json(ASSETS / "recipes.json", "recipes"),
                               load_json(ASSETS / "typical_prices.json", "prices"))
    return next(line for line in p.render_text(result).splitlines() if "chicken" in line and line.startswith("- "))


class ChickenCutLabels(unittest.TestCase):
    def test_drumsticks_only(self):
        self.assertEqual(p.ad_label("chicken thighs", ALDI["ad_text"]), "chicken, drumsticks")

    def test_several_cuts(self):
        self.assertEqual(p.ad_label("chicken thighs", FRYS["ad_text"]), "chicken, drumsticks or thighs")

    def test_thighs_or_leg_quarters_keep_the_name(self):
        self.assertEqual(p.ad_label("chicken thighs", "Chicken Thighs 5 LB Bag"), "chicken thighs")
        self.assertEqual(p.ad_label("chicken thighs", "Chicken Leg Quarters"), "chicken thighs")
        self.assertEqual(p.ad_label("chicken thighs", None), "chicken thighs")

    def test_plan_lines(self):
        self.assertEqual(chicken_line(ALDI), "- 2 lb chicken, drumsticks: $1.98 (ad deal at ALDI)")
        self.assertEqual(chicken_line(FRYS),
                         "- 2 lb chicken, drumsticks or thighs: $1.98 (ad deal at Fry's Food Stores, with card)")


if __name__ == "__main__":
    unittest.main()
