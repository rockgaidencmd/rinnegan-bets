"""Health check endpoint — verifies API is up and DB is reachable."""

from fastapi import APIRouter
from sqlalchemy import text

from api.deps import DbSession


router = APIRouter(tags=["health"])


@router.get("/health")
def healthcheck(db: DbSession) -> dict:
    """Returns 200 if API is alive and DB connection works."""
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
