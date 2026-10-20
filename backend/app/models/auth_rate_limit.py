from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Index

from ..database.base import Base


class AuthRateLimit(Base):
    __tablename__ = "auth_rate_limits"
    __table_args__ = (Index("ix_auth_rate_limit_lookup", "action", "key_hash", "created_at"),)

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(40), nullable=False)
    key_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
