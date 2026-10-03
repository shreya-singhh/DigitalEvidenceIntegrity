from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from ..database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    @property
    def password_hash(self) -> str:
        return self.hashed_password

    @password_hash.setter
    def password_hash(self, value: str) -> None:
        self.hashed_password = value

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    cases_created = relationship(
        "Case",
        foreign_keys="Case.created_by",
        back_populates="creator",
        cascade="all, delete-orphan",
    )
    evidence_owned = relationship(
        "Evidence",
        foreign_keys="Evidence.owner_id",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    verification_logs = relationship(
        "VerificationLog",
        foreign_keys="VerificationLog.verified_by",
        back_populates="verifier",
        cascade="all, delete-orphan",
    )
    chain_of_custody_entries = relationship(
        "ChainOfCustody",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    reports_generated = relationship(
        "Report",
        foreign_keys="Report.generated_by",
        back_populates="generator",
        cascade="all, delete-orphan",
    )
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
