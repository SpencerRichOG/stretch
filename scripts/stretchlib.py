"""Shared helpers for Stretch's scripts. Python 3.9+, standard library only.

The scripts are stateless: Cubbie fetches everything (memory, deals) first and passes
it in as JSON files, because scripts cannot call Cubbie's abilities.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# unit -> (family, size relative to the family's reference unit)
FAMILY = {
    "lb": ("mass", 1.0), "oz": ("mass", 1 / 16), "g": ("mass", 1 / 453.592), "kg": ("mass", 2.20462),
    "each": ("count", 1.0), "ct": ("count", 1.0), "dozen": ("count", 12.0),
    "can": ("can", 1.0),
    "gal": ("volume", 128.0), "qt": ("volume", 32.0), "pt": ("volume", 16.0),
    "floz": ("volume", 1.0), "l": ("volume", 33.814), "ml": ("volume", 0.033814),
}

EQUIPMENT_ALIASES = {
    "frying pan": "pan", "skillet": "pan", "fry pan": "pan", "saucepan": "pot", "sauce pan": "pot",
    "stovetop": "stove", "stove top": "stove", "range": "stove", "cooktop": "stove",
    "airfryer": "air_fryer", "air fryer": "air_fryer", "ricecooker": "rice_cooker", "rice cooker": "rice_cooker",
    "cutting board": "cutting_board", "chopping board": "cutting_board", "chef's knife": "knife",
    "chefs knife": "knife", "sheet pan": "sheet_pan", "baking sheet": "sheet_pan", "microwave oven": "microwave",
    "toaster oven": "oven",
}

# a recipe's diet_level must be <= the student's allowed level
DIET_RANK = {"vegan": 0, "vegetarian": 1, "pescatarian": 2, "fish": 2, "none": 3, "": 3, "omnivore": 3, "meat": 3}
SKILL_RANK = {"none": 1, "beginner": 1, "basic": 2, "some": 2, "comfortable": 3, "confident": 3}


class StretchError(Exception):
    """A student-safe, one-line input problem. Scripts exit with code 2."""


def load_json(path, label):
    p = Path(path)
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise StretchError(f"Missing {label} file: {p}")
    except json.JSONDecodeError as e:
        raise StretchError(f"The {label} file is not valid JSON ({e.msg}, line {e.lineno}): {p}")


def norm_equipment(name):
    n = " ".join(str(name).strip().lower().replace("-", " ").replace("_", " ").split())
    if n in EQUIPMENT_ALIASES:
        return EQUIPMENT_ALIASES[n]
    return n.replace(" ", "_")


def convert(amount, from_unit, to_unit):
    fu, tu = str(from_unit).lower(), str(to_unit).lower()
    if fu not in FAMILY:
        raise StretchError(f"Unknown unit '{from_unit}'. Use one of: {', '.join(sorted(FAMILY))}.")
    if tu not in FAMILY:
        raise StretchError(f"Unknown unit '{to_unit}'.")
    ff, fs = FAMILY[fu]
    tf, ts = FAMILY[tu]
    if ff != tf:
        raise StretchError(f"Cannot convert '{from_unit}' to '{to_unit}' (different kinds of units).")
    return amount * fs / ts


def equipment_ok(recipe, kitchen):
    """True if the kitchen has every item of at least one of the recipe's equipment options."""
    options = recipe.get("needs") or [[]]
    return any(set(opt) <= kitchen for opt in options)


def avoid_hit(recipe, avoid_terms):
    if not avoid_terms:
        return False
    hay = " ".join([recipe["name"].lower()] + [i["item"].lower() for i in recipe["ingredients"]]
                   + [str(c).lower() for c in recipe.get("contains", [])])
    return any(t in hay for t in avoid_terms)


def student_filters(profile):
    diet = str(profile.get("diet", "none")).strip().lower()
    if diet not in DIET_RANK:
        raise StretchError(f"Unknown diet '{diet}'. Use none, vegetarian, vegan or pescatarian.")
    skill = str(profile.get("cooking_skill", "basic")).strip().lower()
    if skill not in SKILL_RANK:
        raise StretchError(f"Unknown cooking_skill '{skill}'. Use none, basic or comfortable.")
    avoid = [str(a).strip().lower() for a in profile.get("avoid", []) if str(a).strip()]
    kitchen = {norm_equipment(k) for k in profile.get("kitchen", [])}
    return DIET_RANK[diet], SKILL_RANK[skill], avoid, kitchen


def feasible_recipes(recipes, profile, extra_equipment=()):
    """Recipes this student can make, optionally pretending they own extra_equipment."""
    diet_rank, skill_rank, avoid, kitchen = student_filters(profile)
    kitchen = set(kitchen) | {norm_equipment(e) for e in extra_equipment}
    out = []
    for r in recipes:
        if DIET_RANK[r["diet_level"]] > diet_rank:
            continue
        if r.get("skill", 1) > skill_rank:
            continue
        if avoid_hit(r, avoid):
            continue
        if not equipment_ok(r, kitchen):
            continue
        out.append(r)
    return out


def fail(message, code=2):
    print(f"ERROR: {message}")
    sys.exit(code)
