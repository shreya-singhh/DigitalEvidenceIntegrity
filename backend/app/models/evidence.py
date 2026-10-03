from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database.base import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="uploaded", nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    case = relationship("Case", back_populates="evidence")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="evidence_owned")
    metadata_entries = relationship("Metadata", back_populates="evidence", cascade="all, delete-orphan")
    verification_logs = relationship("VerificationLog", back_populates="evidence", cascade="all, delete-orphan")
    chain_of_custody_entries = relationship("ChainOfCustody", back_populates="evidence", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="evidence", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="evidence", cascade="all, delete-orphan")
