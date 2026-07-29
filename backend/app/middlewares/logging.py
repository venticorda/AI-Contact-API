from __future__ import annotations

import time

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        endpoint = request.url.path
        method = request.method

        response = await call_next(request)

        process_time = time.time() - start_time

        logger.bind(
            ip=client_ip,
            endpoint=endpoint,
            method=method,
            status=response.status_code,
        ).info(
            f"{method} {endpoint} → {response.status_code} ({process_time:.3f}с)"
        )

        return response
