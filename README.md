
# Meal Calorie Count API (FastAPI + Postgres)

USDA-backed calorie estimation service with user auth.
Enter a dish name and servings → get calories per serving, total calories, and (when available) ingredient list.

* **Backend:** FastAPI, SQLAlchemy, Alembic
* **DB:** PostgreSQL (SQLite works too; used in tests)
* **Auth:** Register/Login with bcrypt + JWT
* **USDA:** FoodData Central (search endpoint)
* **Extras:** Rate limiting, fuzzy matching, caching, typed config

---

## Table of Contents

* [Quickstart](#quickstart)
* [API Overview](#api-overview)
* [Project Structure](#project-structure)
* [Design Notes](#design-notes-what-reviewers-care-about)
* [Testing](#testing)
* [Configuration (env variables)](#configuration-env-variables)
* [Troubleshooting](#troubleshooting)
* [License](#license)
* [Credits](#credits)

---

## Quickstart

### 1) Prereqs

* Python **3.11+**
* [Poetry](https://python-poetry.org/docs/#installation)
* PostgreSQL 14+ (optional; you can also use SQLite)

### 2) Clone & install

```bash
git clone <your-repo-url> meal-calorie-api
cd meal-calorie-api
poetry install
```

### 3) Configure environment

Copy the example file and fill in values:

```bash
cp .env.example .env
```

`.env.example` (included in repo) looks like:

```dotenv
# ======= App =======
ENV=dev
APP_NAME="Meal Calorie Count API"
LOG_LEVEL=INFO

# ======= Database =======
# Postgres example:
DATABASE_URL=postgresql+psycopg://app_user:app_pass@localhost:5432/meal_calorie_db

# ======= Auth / JWT =======
JWT_SECRET=replace-me
JWT_ALGO=HS256
JWT_EXPIRES_MIN=60

# ======= Rate limiting =======
RATE_LIMIT_PER_MIN=60
LOGIN_RATE_LIMIT_PER_MIN=20

# ======= USDA API =======
USDA_BASE_URL=https://api.nal.usda.gov/fdc/v1/foods/search
USDA_API_KEY=replace-me
USDA_PAGE_SIZE=25
USDA_TIMEOUT_S=10
USDA_RETRIES=3
FUZZ_THRESHOLD=55

# ======= Caching (USDA search) =======
CACHE_TTL_S=600
CACHE_MAXSIZE=512

# ======= CORS =======
# Example for local frontend: http://localhost:3000
CORS_ORIGINS=
CORS_ALLOW_CREDENTIALS=true

# ======= Feature flags =======
QUERY_LOG_ENABLED=false
```

> **USDA API key:** get one from [https://fdc.nal.usda.gov/api-key-signup.html](https://fdc.nal.usda.gov/api-key-signup.html) and put it in `USDA_API_KEY`.
> **No Postgres?** Use SQLite by setting `DATABASE_URL=sqlite:///./app.db`.

### 4) Create database & run migrations

**If using Postgres**

```bash
createdb meal_calorie_db  # or create via any Postgres GUI
```

**Run migrations (both Postgres or SQLite):**

```bash
poetry run alembic upgrade head
```

### 5) Run the app

```bash
poetry run uvicorn app.main:app --reload
```

* Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
* Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## API Overview

### Auth

**POST `/auth/register`**
Request:

```json
{
  "first_name": "Jane",
  "last_name": "Doe",
  "email": "jane@example.com",
  "password": "Secret123!"
}
```

Responses:

* **201 Created** → user snapshot (no password)
* **409 Conflict** → email already registered
* **422 Unprocessable Entity** → validation errors

**POST `/auth/login`**
Request:

```json
{ "email": "jane@example.com", "password": "Secret123!" }
```

Responses:

* **200 OK** → `{ "access_token": "...", "user": { ... } }`
* **401 Unauthorized** → invalid credentials
* **429 Too Many Requests** → login rate limited (env-tunable)

### Calories

**POST `/get-calories`**
Request:

```json
{ "dish_name": "grilled salmon", "servings": 2 }
```

Response (example):

```json
{
  "dish_name": "grilled salmon",
  "servings": 2.0,
  "calories_per_serving": 234.0,
  "total_calories": 468.0,
  "source": "USDA FoodData Central",
  "basis": "per serving (label)",
  "ingredients": ["salmon", "salt", "pepper"],
  "macros": { "protein": 25.1, "fat": 14.2, "carbs": 0.0 }
}
```

Errors:

* **404 Not Found** → dish not found / low match confidence
* **503 Service Unavailable** → USDA API failure
* **422 Unprocessable Entity** → invalid input (e.g., servings ≤ 0)

**Curl examples**

```bash
# register
curl -X POST http://127.0.0.1:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Jane","last_name":"Doe","email":"jane@example.com","password":"Secret123!"}'

# login
curl -X POST http://127.0.0.1:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"jane@example.com","password":"Secret123!"}'

# get calories
curl -X POST http://127.0.0.1:8000/get-calories \
  -H 'Content-Type: application/json' \
  -d '{"dish_name":"paneer butter masala","servings":1.5}'
```

---

## Project Structure

```
app/
  adapters/                           # concrete implementations (outside world)
    db/
      sqlalchemy_user_repository.py   # SQLAlchemy impl of UserRepository
    http/
      usda_client.py                  # httpx client to USDA (retries + TTL cache)
  controllers/                        # FastAPI routers
    auth.py
    calories.py
    health.py
  core/                               # cross-cutting: config, security, rate limit, constants
    config.py
    constants.py
    rate_limit.py
    security.py
  db/
    base.py                           # Declarative Base / metadata
    session.py                        # engine + SessionLocal + get_db()
  models/
    user.py                           # ORM User
    __init__.py                       # import models for Alembic autogenerate
  ports/                              # Protocol interfaces (no deps)
    food_search.py                    # FoodSearchClient
    user_repository.py                # UserRepository
  schemas/
    auth.py                           # RegisterIn, LoginIn/Out, UserOut
    calories.py                       # CaloriesIn/Out
  services/
    auth_service.py                   # register/login logic
    calorie_service.py                # USDA search → normalize/score → kcal math
  utils/
    calorie_estimation_utils.py       # normalization, RapidFuzz scoring, kcal helpers
main.py                               # app wiring (routers, middleware, DI)
```

* **Controllers** → only HTTP concerns and mapping to services
* **Services** → business logic (auth rules, calorie estimation)
* **Adapters** → talk to DB/HTTP (SQLAlchemy repo, USDA client)
* **Ports** → interfaces the services depend on (easy to mock)
* **Schemas** → Pydantic v2 DTOs (request/response)
* **Core/DB** → settings, security, rate limits, session management

---

## Design Notes (what reviewers care about)

* **Ports & Adapters**
  Controllers → Services → Ports, with Adapters at the edges. This keeps tests simple and swapping implementations possible.

* **Pydantic v2**
  Clean validation, faster runtime. Response models use `ConfigDict(from_attributes=True)` + `model_validate()` to map ORM.

* **SQLAlchemy 2.x (sync)**
  Straightforward per-request session; `flush()` assigns PKs before commit. Async DB can be added later if needed.

* **JWT (HS256)**
  Minimal access token approach for simplicity. Add refresh/rotation if the product needs it.

* **USDA client (httpx) with retries + TTL cache**
  Smooths flaky network and reduces API calls. TTL means a small staleness window—fine for this use.

* **Fuzzy matching**
  Normalize text, apply small alias map, and use RapidFuzz blend (WRatio + token\_set + partial) with a token-coverage nudge. Tuned via `FUZZ_THRESHOLD`.

* **Rate limiting**
  SlowAPI middleware; global limit and a tighter login limit—both configurable.

---

## Testing

Install (already handled by Poetry), then:

```bash
poetry run pytest -q
# or with coverage:
poetry run pytest --cov=app --cov-report=term-missing -q
```

What’s covered:

* **Unit**: security (hash/verify, JWT), calorie utils (normalize/score/kJ→kcal), calorie service (with fake USDA), SQLAlchemy repo.
* **Integration**: `/auth/register`, `/auth/login`, `/get-calories`, `/health` using dependency overrides and a temp SQLite DB.

---

## Configuration (env variables)

* **Database**
  `DATABASE_URL` — e.g., `sqlite:///./app.db` (quick) or `postgresql+psycopg://user:pass@localhost:5432/meal_calorie_db`

* **JWT**
  `JWT_SECRET`, `JWT_ALGO=HS256`, `JWT_EXPIRES_MIN=60`

* **USDA**
  `USDA_API_KEY`, `USDA_BASE_URL`, `USDA_PAGE_SIZE`, `USDA_TIMEOUT_S`, `USDA_RETRIES`, `FUZZ_THRESHOLD`

* **Caching**
  `CACHE_TTL_S` (0 disables), `CACHE_MAXSIZE`

* **Rate Limiting**
  `RATE_LIMIT_PER_MIN`, `LOGIN_RATE_LIMIT_PER_MIN`

* **CORS**
  `CORS_ORIGINS` (comma-separated), `CORS_ALLOW_CREDENTIALS`

---

## Troubleshooting

* **“Field required” (DATABASE\_URL/JWT\_SECRET/USDA\_API\_KEY) on startup**
  Your `.env` isn’t being read or you’re running from the wrong folder. Keep `.env` in repo root and run commands from there.

* **Login returns 401**
  Wrong password or wrong request shape. Send **JSON** `{ "email": "...", "password": "..." }`.

* **Calories endpoint returns 503**
  USDA key missing/invalid or upstream down. Check `.env` and network.

* **Port already in use**
  `pkill -f "uvicorn app.main:app" || true` and re-run with `--port 8001`.

---

## License

MIT (or your organization’s standard choice)

---

## Credits

Built with FastAPI, SQLAlchemy, Alembic, httpx, RapidFuzz, Passlib, PyJWT, SlowAPI.
USDA FoodData Central is the nutrition data source.
