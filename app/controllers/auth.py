from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.adapters.db.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.schemas.auth import Register, LoginIn, User, LoginOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

_settings = get_settings()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    repo = SqlAlchemyUserRepository(db)
    return AuthService(repo)


@router.post(
    "/register",
    response_model=User,
    status_code=201,
    summary="Register a new user"
)
@limiter.limit(f"{_settings.RATE_LIMIT_PER_MIN}/minute")
def register(payload: Register, request: Request, svc: AuthService = Depends(get_auth_service)) -> User:
    try:
        user = svc.register(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            raw_password=payload.password,
        )
        return user
    except ValueError as e:
        if "already registered" in str(e).lower():
            raise HTTPException(status_code=409, detail="Email already registered")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/login",
    response_model=LoginOut,
    summary="Login and receive a JWT"
)
@limiter.limit(f"{_settings.LOGIN_RATE_LIMIT_PER_MIN}/minute")
def login(payload: LoginIn, request: Request, svc: AuthService = Depends(get_auth_service)) -> LoginOut:
    try:
        token, user = svc.login(email=payload.email, raw_password=payload.password)
        return LoginOut(access_token=token, user=user)
    except ValueError:
        raise HTTPException(status_code=401, detail="Incorrect credentials")
