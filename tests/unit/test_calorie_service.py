import pytest
from app.services.calorie_service import CalorieService
from tests.factories import FakeUSDAClient, usda_food
from app.adapters.http.usda_client import USDAError

@pytest.mark.anyio
async def test_calorie_estimate_with_grilled_chicken_salad():
    foods = {"foods":[usda_food(description="Grilled Chicken Salad")]}
    svc = CalorieService(FakeUSDAClient(foods))
    out = await svc.calculate(dish_name="griled chiken salad", servings=2)
    assert out.total_calories >= 400

@pytest.mark.anyio
async def test_low_confidence_return_lookup_error():
    svc = CalorieService(FakeUSDAClient({"foods":[{"description":"zzz"}]}))
    with pytest.raises(LookupError):
        await svc.calculate(dish_name="chicken", servings=1)

@pytest.mark.anyio
async def test_usda_error():
    svc = CalorieService(FakeUSDAClient(err=USDAError("boom")))
    with pytest.raises(USDAError):
        await svc.calculate(dish_name="x", servings=1)
