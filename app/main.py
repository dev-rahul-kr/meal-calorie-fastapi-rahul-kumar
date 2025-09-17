from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.controllers.health import router as health_router
from app.controllers.calories import router as calories_router
from app.controllers.auth import router as auth_router

settings = get_settings()

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Meal Calorie Count API — USDA-backed calorie estimates",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Controllers
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(calories_router)

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    # For reliable reload, pass the import string (not the object)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

