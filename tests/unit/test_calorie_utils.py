import math
from app.utils import calorie_estimation_utils as util


def test_normalize_basic_and_aliases():
    s = util.normalize("  Griled !!! chiken  ")
    assert s == "grilled chicken"

def test_normalize_removes_accents():
    s = util.normalize("Café crème")
    assert s == "cafe creme"

def test_tokens_splits_normalized():
    t = util.tokens("Griled,   chiken!!!")
    assert t == ["grilled", "chicken"]


def test_find_energy_kcal_from_label_per_serving():
    food = {"labelNutrients": {"calories": {"value": 270}}}
    kcal, basis = util.find_energy_kcal(food)
    assert kcal == 270.0
    assert basis.startswith("per serving")

def test_find_energy_kcal_from_foodnutrients_kcal_per_100g():
    food = {"foodNutrients": [{"nutrientName": "Energy", "unitName": "kcal", "value": 150}]}
    kcal, basis = util.find_energy_kcal(food)
    assert kcal == 150.0
    assert basis == "per 100 g"

def test_find_energy_kcal_from_kj_converted():
    food = {"foodNutrients": [{"nutrientName": "Energy", "unitName": "kJ", "value": 418.4}]}
    kcal, basis = util.find_energy_kcal(food)
    assert math.isclose(kcal, 100.0, rel_tol=1e-3)
    assert "converted from kJ" in basis


def test_serving_grams_variants_and_none():
    assert util.serving_grams({"servingSize": 85, "servingSizeUnit": "g"}) == 85.0
    assert util.serving_grams({"servingSize": 100, "servingSizeUnit": "grams"}) == 100.0
    assert util.serving_grams({"servingSize": 1, "servingSizeUnit": "cup"}) is None
    assert util.serving_grams({"servingSize": None, "servingSizeUnit": "g"}) is None


def test_composite_score_prefers_better_match():
    qn = util.normalize("grilled chicken salad")
    exact = util.normalize("Grilled Chicken Salad")
    weak = util.normalize("Chicken Tikka Masala")
    s_exact = util.composite_score(exact, qn)
    s_weak = util.composite_score(weak, qn)
    assert s_exact > s_weak
