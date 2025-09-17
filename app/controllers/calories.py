from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.rate_limit import limiter
from app.core.config import get_settings
from app.schemas.calories import CaloriesIn, CaloriesEstimate
from app.services.calorie_service import CalorieService
from app.adapters.http.usda_client import get_usda_client, USDAError

router = APIRouter()
_settings = get_settings()

def get_service() -> CalorieService:
    return CalorieService(get_usda_client())

response_dict = {
    200: {"description": "Calories calculated"},
    404: {"description": "Dish not found"},
    503: {"description": "USDA service unavailable"}
}

@router.post(
    "/get-calories",
    response_model=CaloriesEstimate,
    summary="Estimate calories for a dish using USDA data",
    responses=response_dict,
)
@limiter.limit(f"{_settings.RATE_LIMIT_PER_MIN}/minute")
async def get_calories(payload: CaloriesIn, request: Request, svc: CalorieService = Depends(get_service))->CaloriesEstimate:
    try:
        result = await svc.calculate(dish_name=payload.dish_name, servings=payload.servings)
        return result
    except LookupError:
        raise HTTPException(status_code=404, detail="Dish not found")
    except USDAError:
        raise HTTPException(status_code=503, detail="USDA service unavailable")
