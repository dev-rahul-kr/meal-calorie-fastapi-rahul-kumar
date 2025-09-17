from typing import Any, List, Mapping
from app.core.config import get_settings
from app.schemas.calories import CaloriesEstimate
from app.ports.food_search import FoodSearchClient
from app.utils.calorie_estimation_utils import (normalize, tokens,
                                                composite_score, find_energy_kcal, serving_grams)


class CalorieService:
    """Calculate calorie estimate using a FoodSearchClient."""

    def __init__(self, food_client: FoodSearchClient):
        self._client = food_client
        s = get_settings()
        self._threshold = s.FUZZ_THRESHOLD

    async def calculate(self, *, dish_name: str, servings: float) -> CaloriesEstimate:
        data = await self._client.search(dish_name)
        foods: List[Mapping[str, Any]] = list(data.get("foods") or [])
        if not foods:
            raise LookupError("No matches")

        normalized_dish_name = normalize(dish_name)
        dish_tokens = set(tokens(dish_name))

        def _score(f: Mapping[str, Any]) -> float:
            desc = str(f.get("description") or "")
            normalize_desc = normalize(desc)
            base = composite_score(normalize_desc, normalized_dish_name)
            # token coverage bonus
            d_tokens = set(normalize_desc.split())
            coverage = (len(dish_tokens & d_tokens) / len(dish_tokens)) if dish_tokens else 0.0
            bonus_cov = 10.0 * coverage
            return base + bonus_cov

        best = max(foods, key=_score)
        best_score = _score(best)
        if best_score < self._threshold:
            raise LookupError("Low confidence match")

        kcal, basis = find_energy_kcal(best)
        if kcal is None:
            raise LookupError("Energy not found")

        grams = serving_grams(best)
        if basis.startswith("per serving"):
            calories_per_serving = kcal
            final_basis = basis
        elif grams:
            calories_per_serving = kcal * (grams / 100.0)
            final_basis = "per serving (derived from per 100 g)"
        else:
            calories_per_serving = kcal
            final_basis = basis or "per 100 g"

        total = calories_per_serving * float(servings)

        # Ingredients if it exists
        ingredients = None
        ing = best.get("ingredients")
        if isinstance(ing, str) and ing.strip():
            parts = [p.strip() for p in ing.split(",")]
            ingredients = [p for p in parts if p][:20]  # cap list length

        return CaloriesEstimate(
            dish_name=dish_name,
            servings=float(servings),
            calories_per_serving=round(calories_per_serving, 2),
            total_calories=round(total, 2),
            source="USDA FoodData Central",
            basis=final_basis,
            ingredients=ingredients,
        )
