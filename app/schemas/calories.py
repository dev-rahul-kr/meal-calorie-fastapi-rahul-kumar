from typing import Optional, List
from pydantic import BaseModel, Field

class CaloriesIn(BaseModel):
    dish_name: str = Field(..., min_length=1)
    servings: float = Field(..., gt=0, description="Must be > 0")


class CaloriesEstimate(BaseModel):
    dish_name: str
    servings: float
    calories_per_serving: float
    total_calories: float
    source: str = "USDA FoodData Central"
    basis: Optional[str] = None
    ingredients: Optional[List[str]] = None