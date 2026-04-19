"""
In-memory rate limiter for case submissions.
Limits each IP address to a fixed number of submissions per rolling time window.
No external dependencies — uses a simple dict with timestamp lists.

In a multi-worker production deployment, replace this with a Redis-backed counter.
For the Render free tier (single worker), this is sufficient.
"""

import hashlib
from collections import defaultdict
from time import time
from fastapi import HTTPException, Request

from guardrails.audit_logger import log_rate_limit_hit

RATE_LIMIT = 20          # max submissions per IP per window
WINDOW_SECONDS = 3600    # rolling 1-hour window

_request_log: dict[str, list[float]] = defaultdict(list)


def _hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()[:10]


def check_rate_limit(request: Request) -> None:
    """
    Raises HTTP 429 if the requesting IP has exceeded the rate limit.
    Call this as the first check in any route that triggers the AI pipeline.
    """
    ip = request.client.host if request.client else "unknown"
    now = time()
    window_start = now - WINDOW_SECONDS

    # Purge timestamps outside the rolling window
    _request_log[ip] = [ts for ts in _request_log[ip] if ts > window_start]

    if len(_request_log[ip]) >= RATE_LIMIT:
        log_rate_limit_hit(_hash_ip(ip))
        raise HTTPException(
            status_code=429,
            detail=(
                f"Rate limit exceeded. "
                f"Maximum {RATE_LIMIT} case submissions per hour per IP. "
                "Please try again later."
            ),
        )

    _request_log[ip].append(now)
