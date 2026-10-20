import hashlib
import hmac
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth_rate_limit import AuthRateLimit


def enforce_rate_limit(
    db: Session,
    *,
    action: str,
    key: str,
    limit: int,
    window_seconds: int,
) -> None:
    now = datetime.utcnow()
    cutoff = now - timedelta(seconds=window_seconds)
    key_hash = hmac.new(
        settings.secret_key.encode("utf-8"),
        key.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    attempts = (
        db.query(func.count(AuthRateLimit.id))
        .filter(
            AuthRateLimit.action == action,
            AuthRateLimit.key_hash == key_hash,
            AuthRateLimit.created_at >= cutoff,
        )
        .scalar()
        or 0
    )
    if attempts >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again later.",
            headers={"Retry-After": str(window_seconds)},
        )

    db.add(AuthRateLimit(action=action, key_hash=key_hash, created_at=now))
    db.query(AuthRateLimit).filter(AuthRateLimit.created_at < now - timedelta(days=1)).delete()
    db.commit()
