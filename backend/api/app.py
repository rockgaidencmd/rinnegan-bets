"""FastAPI application factory.

Run dev server:
    cd backend && source venv/bin/activate
    uvicorn api.app:app --reload --port 8000

Then visit http://localhost:8000/docs for the interactive Swagger UI.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.errors import register_exception_handlers
from api.routes import admin, bankroll, fixtures, health, leagues, predictions, teams


# Frontend Vite dev server typically runs on these origins.
DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# LAN ranges for the Expo Go mobile app: 192.168.x.x, 10.x.x.x, 172.16-31.x.x.
LAN_ORIGIN_REGEX = (
    r"http://("
    r"localhost|127\.0\.0\.1|"
    r"192\.168\.\d+\.\d+|"
    r"10\.\d+\.\d+\.\d+|"
    r"172\.(1[6-9]|2\d|3[01])\.\d+\.\d+"
    r"):\d+"
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Rinnegan Bets API",
        version="0.1.0",
        description=(
            "HTTP API for the Rinnegan Bets prediction engine. "
            "Currently supports the 1X2 → Victoria Local market."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=DEV_ORIGINS,
        allow_origin_regex=LAN_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(teams.router)
    app.include_router(leagues.router)
    app.include_router(fixtures.router)
    app.include_router(predictions.router)
    app.include_router(bankroll.router)
    app.include_router(admin.router)

    return app


app = create_app()
