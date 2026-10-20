from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from ..database.base import Base


class EmailOtpChallenge(Base):
    __tablename__ = "email_otp_challenges"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    code_salt = Column(String(32), nullable=False)
    code_hash = Column(String(64), nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    expires_at = Column(DateTime, nullable=False, index=True)
    consumed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
