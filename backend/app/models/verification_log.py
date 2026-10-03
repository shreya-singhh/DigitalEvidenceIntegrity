from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database.base import Base


class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False, index=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    original_hash = Column(String(64), nullable=False)
    calculated_hash = Column(String(64), nullable=False)
    status = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    evidence = relationship("Evidence", back_populates="verification_logs")
    verifier = relationship("User", foreign_keys=[verified_by], back_populates="verification_logs")
