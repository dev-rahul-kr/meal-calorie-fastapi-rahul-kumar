from app.main import app
from app.controllers.calories import get_service
from app.services.calorie_service import CalorieService
from app.adapters.http.usda_client import USDAError
from tests.factories import FakeUSDAClient, usda_food


def _use_fake_service(data=None, err: Exception | None = None):
    fake = FakeUSDAClient(data or {"foods": []}, err)
    app.dependency_overrides[get_service] = lambda: CalorieService(fake)


def _clear_overrides():
    app.dependency_overrides.pop(get_service, None)


def test_mac_and_cheese_return_200(client):
    try:
        foods = {"foods": [usda_food(description="Macaroni and Cheese",
                                     labelNutrients={"calories": {"value": 270}})]}
        _use_fake_service(foods)
        resp = client.post("/get-calories", json={"dish_name": "macaroni and cheese", "servings": 2})
        assert resp.status_code == 200
        body = resp.json()
        assert body["dish_name"] == "macaroni and cheese"
        assert body["servings"] == 2
        assert body["total_calories"] >= 500
    finally:
        _clear_overrides()


def test_grilled_salmon_return_success(client):
    try:
        foods = {"foods": [usda_food(description="Grilled Salmon",
                                     labelNutrients={"calories": {"value": 233}})]}
        _use_fake_service(foods)
        resp = client.post("/get-calories", json={"dish_name": "grilled salmon", "servings": 1.5})
        assert resp.status_code == 200
        body = resp.json()
        assert body["dish_name"] == "grilled salmon"
        assert body["servings"] == 1.5
        assert body["calories_per_serving"] > 0
        assert body["total_calories"] > body["calories_per_serving"]
    finally:
        _clear_overrides()


def test_paneer_butter_masala_return_success(client):
    try:
        foods = {"foods": [usda_food(description="Paneer Butter Masala",
                                     labelNutrients={"calories": {"value": 350}})]}
        _use_fake_service(foods)
        resp = client.post("/get-calories", json={"dish_name": "paneer butter masala", "servings": 1})
        assert resp.status_code == 200
        body = resp.json()
        assert body["dish_name"] == "paneer butter masala"
        assert body["total_calories"] >= 300
    finally:
        _clear_overrides()


def test_non_existent_dish_returns_404(client):
    try:
        _use_fake_service({"foods": []})
        resp = client.post("/get-calories", json={"dish_name": "non-existing-dish", "servings": 1})
        assert resp.status_code == 404
    finally:
        _clear_overrides()


def test_zero_servings_is_422(client):
    try:
        foods = {"foods": [usda_food(description="Chicken Salad")]}
        _use_fake_service(foods)
        resp = client.post("/get-calories", json={"dish_name": "chicken salad", "servings": 0})
        assert resp.status_code == 422
    finally:
        _clear_overrides()


def test_negative_servings_is_422(client):
    try:
        foods = {"foods": [usda_food(description="Chicken Salad")]}
        _use_fake_service(foods)
        resp = client.post("/get-calories", json={"dish_name": "chicken salad", "servings": -1})
        assert resp.status_code == 422
    finally:
        _clear_overrides()


def test_multiple_similar_matches_picks_best(client):
    try:
        foods = {
            "foods": [
                usda_food(description="Grilled Salmon", labelNutrients={"calories": {"value": 123}}),
                usda_food(description="Salmon, grilled with sauce", labelNutrients={"calories": {"value": 210}},
                          servingSize=None, servingSizeUnit=""),
                usda_food(description="Salmon Sashimi", labelNutrients={"calories": {"value": 90}})
            ]
        }
        _use_fake_service(foods)
        resp = client.post("/get-calories", json={"dish_name": "grilled salmon", "servings": 1})
        assert resp.status_code == 200
        body = resp.json()
        assert 120 <= body["calories_per_serving"] <= 126
    finally:
        _clear_overrides()


def test_get_calories_usda_error_with_status_503(client):
    try:
        _use_fake_service(err=USDAError("boom"))
        resp = client.post("/get-calories", json={"dish_name": "x", "servings": 1})
        assert resp.status_code == 503
    finally:
        _clear_overrides()
