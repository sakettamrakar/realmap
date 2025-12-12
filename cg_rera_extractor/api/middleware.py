"""
API Middleware for Rate Limiting and Authentication.

Point 30 Implementation: API Governance (Throttling)
- Rate limiting middleware for FastAPI
- x-api-key authentication for third-party consumers
- Tiered limits (internal vs third-party)
- Rate limit headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
"""
from __future__ import annotations

import hashlib
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

import os

# Environment variable to disable rate limiting (defaults to OFF for local development)
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"


# =============================================================================
# POINT 30: Rate Limiting Configuration
# =============================================================================


class ClientTier(str, Enum):
    """Client tier for rate limiting."""
    INTERNAL = "internal"      # Internal services, high limits
    PREMIUM = "premium"        # Paid API access
    STANDARD = "standard"      # Authenticated third-party
    ANONYMOUS = "anonymous"    # No API key


@dataclass
class RateLimitConfig:
    """Rate limit configuration per tier."""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int  # Max concurrent requests


# Tier-based rate limits
RATE_LIMITS: dict[ClientTier, RateLimitConfig] = {
    ClientTier.INTERNAL: RateLimitConfig(
        requests_per_minute=1000,
        requests_per_hour=50000,
        requests_per_day=500000,
        burst_limit=100,
    ),
    ClientTier.PREMIUM: RateLimitConfig(
        requests_per_minute=500,
        requests_per_hour=20000,
        requests_per_day=200000,
        burst_limit=50,
    ),
    ClientTier.STANDARD: RateLimitConfig(
        requests_per_minute=100,
        requests_per_hour=5000,
        requests_per_day=50000,
        burst_limit=20,
    ),
    ClientTier.ANONYMOUS: RateLimitConfig(
        requests_per_minute=500,
        requests_per_hour=10000,
        requests_per_day=50000,
        burst_limit=50,
    ),
}


# =============================================================================
# POINT 30: API Key Management
# =============================================================================


@dataclass
class APIKeyInfo:
    """Information about an API key."""
    key_hash: str
    tier: ClientTier
    client_name: str
    created_at: datetime
    expires_at: datetime | None = None
    is_active: bool = True
    rate_limit_override: RateLimitConfig | None = None
    allowed_endpoints: list[str] | None = None  # None = all allowed


# In-memory API key store (replace with database in production)
# Keys are stored as SHA256 hashes for security
API_KEYS: dict[str, APIKeyInfo] = {}


def register_api_key(
    api_key: str,
    tier: ClientTier,
    client_name: str,
    expires_at: datetime | None = None,
) -> APIKeyInfo:
    """Register a new API key."""
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    info = APIKeyInfo(
        key_hash=key_hash,
        tier=tier,
        client_name=client_name,
        created_at=datetime.now(timezone.utc),
        expires_at=expires_at,
    )
    API_KEYS[key_hash] = info
    return info


def validate_api_key(api_key: str) -> APIKeyInfo | None:
    """Validate an API key and return its info."""
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    info = API_KEYS.get(key_hash)
    
    if not info:
        return None
    
    if not info.is_active:
        return None
    
    if info.expires_at and info.expires_at < datetime.now(timezone.utc):
        return None
    
    return info


# =============================================================================
# POINT 30: Rate Limiter Implementation
# =============================================================================


@dataclass
class RateLimitBucket:
    """Token bucket for rate limiting."""
    tokens: float
    last_update: float
    window_requests: dict[str, int] = field(default_factory=lambda: defaultdict(int))


class RateLimiter:
    """
    Token bucket rate limiter with sliding window.
    
    Point 30: Implements tiered rate limiting with multiple time windows.
    """
    
    def __init__(self) -> None:
        self._buckets: dict[str, RateLimitBucket] = {}
        self._lock_time = 0.0  # Simple lock mechanism
    
    def _get_bucket(self, client_id: str, config: RateLimitConfig) -> RateLimitBucket:
        """Get or create a rate limit bucket for a client."""
        if client_id not in self._buckets:
            self._buckets[client_id] = RateLimitBucket(
                tokens=float(config.burst_limit),
                last_update=time.time(),
            )
        return self._buckets[client_id]
    
    def _refill_tokens(
        self,
        bucket: RateLimitBucket,
        config: RateLimitConfig,
    ) -> None:
        """Refill tokens based on time elapsed."""
        now = time.time()
        elapsed = now - bucket.last_update
        
        # Calculate token refill rate (tokens per second)
        refill_rate = config.requests_per_minute / 60.0
        tokens_to_add = elapsed * refill_rate
        
        bucket.tokens = min(
            float(config.burst_limit),
            bucket.tokens + tokens_to_add,
        )
        bucket.last_update = now
    
    def _clean_old_windows(self, bucket: RateLimitBucket) -> None:
        """Remove old window data."""
        now = time.time()
        hour_ago = now - 3600
        day_ago = now - 86400
        
        # Clean minute windows older than 1 hour
        keys_to_remove = [
            k for k in bucket.window_requests
            if k.startswith("min_") and float(k.split("_")[1]) < hour_ago
        ]
        for k in keys_to_remove:
            del bucket.window_requests[k]
    
    def check_rate_limit(
        self,
        client_id: str,
        config: RateLimitConfig,
    ) -> tuple[bool, dict[str, int]]:
        """
        Check if request is allowed under rate limit.
        
        Returns:
            Tuple of (is_allowed, headers_dict)
        """
        bucket = self._get_bucket(client_id, config)
        self._refill_tokens(bucket, config)
        self._clean_old_windows(bucket)
        
        now = time.time()
        current_minute = f"min_{int(now // 60)}"
        current_hour = f"hour_{int(now // 3600)}"
        current_day = f"day_{int(now // 86400)}"
        
        # Check minute limit
        minute_count = bucket.window_requests.get(current_minute, 0)
        if minute_count >= config.requests_per_minute:
            reset_time = int((int(now // 60) + 1) * 60)
            return False, {
                "X-RateLimit-Limit": str(config.requests_per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time),
                "X-RateLimit-Window": "minute",
            }
        
        # Check hour limit
        hour_count = sum(
            v for k, v in bucket.window_requests.items()
            if k.startswith("hour_") and k == current_hour
        )
        if hour_count >= config.requests_per_hour:
            reset_time = int((int(now // 3600) + 1) * 3600)
            return False, {
                "X-RateLimit-Limit": str(config.requests_per_hour),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time),
                "X-RateLimit-Window": "hour",
            }
        
        # Check burst limit (token bucket)
        if bucket.tokens < 1:
            return False, {
                "X-RateLimit-Limit": str(config.burst_limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(now + 1)),
                "X-RateLimit-Window": "burst",
            }
        
        # Allow request, consume token and update counters
        bucket.tokens -= 1
        bucket.window_requests[current_minute] = minute_count + 1
        bucket.window_requests[current_hour] = hour_count + 1
        bucket.window_requests[current_day] = bucket.window_requests.get(current_day, 0) + 1
        
        remaining = min(
            config.requests_per_minute - minute_count - 1,
            int(bucket.tokens),
        )
        
        return True, {
            "X-RateLimit-Limit": str(config.requests_per_minute),
            "X-RateLimit-Remaining": str(max(0, remaining)),
            "X-RateLimit-Reset": str(int((int(now // 60) + 1) * 60)),
            "X-RateLimit-Window": "minute",
        }


# Global rate limiter instance
_rate_limiter = RateLimiter()


# =============================================================================
# POINT 30: FastAPI Middleware
# =============================================================================


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    
    Point 30: API Governance implementation.
    
    Features:
    - x-api-key authentication
    - Tiered rate limits
    - Rate limit headers in response
    - Exempt paths (health checks, etc.)
    """
    
    EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request with rate limiting."""
        
        # Skip rate limiting entirely if disabled via environment variable
        if not RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Skip rate limiting for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)
        
        # Extract API key and determine tier
        api_key = request.headers.get("x-api-key")
        client_tier = ClientTier.ANONYMOUS
        client_id = self._get_client_id(request)
        
        if api_key:
            key_info = validate_api_key(api_key)
            if key_info:
                client_tier = key_info.tier
                client_id = key_info.key_hash[:16]  # Use key hash prefix as client ID
            else:
                # Invalid API key
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "invalid_api_key",
                        "message": "The provided API key is invalid or expired.",
                    },
                    headers={"WWW-Authenticate": "API-Key"},
                )
        
        # Get rate limit config for tier
        config = RATE_LIMITS[client_tier]
        
        # Check rate limit
        allowed, headers = _rate_limiter.check_rate_limit(client_id, config)
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Please retry after {headers.get('X-RateLimit-Reset', 'a moment')}.",
                    "tier": client_tier.value,
                },
                headers=headers,
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value
        
        # Add tier header for debugging
        response.headers["X-RateLimit-Tier"] = client_tier.value
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Try X-Forwarded-For header first (for proxied requests)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Fall back to client host
        if request.client:
            return request.client.host
        
        return "unknown"


# =============================================================================
# POINT 30: Authentication Dependency
# =============================================================================


async def require_api_key(request: Request) -> APIKeyInfo:
    """
    FastAPI dependency that requires a valid API key.
    
    Usage:
        @app.get("/protected")
        def protected_route(key_info: APIKeyInfo = Depends(require_api_key)):
            ...
    """
    api_key = request.headers.get("x-api-key")
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide x-api-key header.",
            headers={"WWW-Authenticate": "API-Key"},
        )
    
    key_info = validate_api_key(api_key)
    
    if not key_info:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key.",
            headers={"WWW-Authenticate": "API-Key"},
        )
    
    return key_info


async def require_tier(
    minimum_tier: ClientTier,
) -> Callable[[Request], APIKeyInfo]:
    """
    Factory for tier-based authorization.
    
    Usage:
        @app.get("/premium-only")
        def premium_route(key_info: APIKeyInfo = Depends(require_tier(ClientTier.PREMIUM))):
            ...
    """
    async def dependency(request: Request) -> APIKeyInfo:
        key_info = await require_api_key(request)
        
        tier_order = [ClientTier.ANONYMOUS, ClientTier.STANDARD, ClientTier.PREMIUM, ClientTier.INTERNAL]
        
        if tier_order.index(key_info.tier) < tier_order.index(minimum_tier):
            raise HTTPException(
                status_code=403,
                detail=f"This endpoint requires {minimum_tier.value} tier or higher.",
            )
        
        return key_info
    
    return dependency


# =============================================================================
# POINT 30: Usage Tracking
# =============================================================================


@dataclass
class UsageRecord:
    """Record of API usage for analytics."""
    client_id: str
    tier: ClientTier
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    timestamp: datetime


class UsageTracker:
    """
    Track API usage for analytics and billing.
    
    Point 30: Usage tracking for API governance.
    """
    
    def __init__(self, max_records: int = 10000) -> None:
        self._records: list[UsageRecord] = []
        self._max_records = max_records
    
    def record(
        self,
        client_id: str,
        tier: ClientTier,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
    ) -> None:
        """Record an API request."""
        record = UsageRecord(
            client_id=client_id,
            tier=tier,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            timestamp=datetime.now(timezone.utc),
        )
        
        self._records.append(record)
        
        # Trim old records if needed
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records:]
    
    def get_summary(
        self,
        client_id: str | None = None,
        since: datetime | None = None,
    ) -> dict:
        """Get usage summary."""
        records = self._records
        
        if client_id:
            records = [r for r in records if r.client_id == client_id]
        
        if since:
            records = [r for r in records if r.timestamp >= since]
        
        if not records:
            return {"total_requests": 0}
        
        total = len(records)
        by_tier = defaultdict(int)
        by_endpoint = defaultdict(int)
        avg_response_time = sum(r.response_time_ms for r in records) / total
        error_count = sum(1 for r in records if r.status_code >= 400)
        
        for r in records:
            by_tier[r.tier.value] += 1
            by_endpoint[r.endpoint] += 1
        
        return {
            "total_requests": total,
            "by_tier": dict(by_tier),
            "by_endpoint": dict(by_endpoint),
            "avg_response_time_ms": round(avg_response_time, 2),
            "error_count": error_count,
            "error_rate": round(error_count / total * 100, 2) if total else 0,
        }


# Global usage tracker instance
_usage_tracker = UsageTracker()


__all__ = [
    # Rate limiting
    "RateLimitMiddleware",
    "RateLimiter",
    "RateLimitConfig",
    "RATE_LIMITS",
    # API keys
    "ClientTier",
    "APIKeyInfo",
    "register_api_key",
    "validate_api_key",
    # Dependencies
    "require_api_key",
    "require_tier",
    # Usage tracking
    "UsageTracker",
    "UsageRecord",
]
