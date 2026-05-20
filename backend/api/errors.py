"""Centralized exception → HTTP code mapping.

Routes never catch domain exceptions — they bubble here and become
consistent JSON responses with the right status code.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.bankroll.tracker import BankrollError
from data.team_search import TeamSearchError


logger = logging.getLogger(__name__)


def _problem(status: int, title: str, detail: str) -> JSONResponse:
    """RFC 7807-ish error body. Consistent shape."""
    return JSONResponse(
        status_code=status,
        content={"title": title, "detail": detail, "status": status},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BankrollError)
    async def _bankroll_error(_: Request, exc: BankrollError) -> JSONResponse:
        msg = str(exc)
        if "not found" in msg.lower():
            return _problem(404, "Not Found", msg)
        if "already settled" in msg.lower():
            return _problem(409, "Conflict", msg)
        return _problem(422, "Unprocessable Entity", msg)

    @app.exception_handler(TeamSearchError)
    async def _team_search_error(_: Request, exc: TeamSearchError) -> JSONResponse:
        return _problem(404, "Team Not Found", str(exc))

    @app.exception_handler(ValueError)
    async def _value_error(_: Request, exc: ValueError) -> JSONResponse:
        return _problem(422, "Validation Error", str(exc))

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception", exc_info=exc)
        return _problem(500, "Internal Server Error", "An unexpected error occurred")
