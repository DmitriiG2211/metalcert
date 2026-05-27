import enum
from datetime import datetime, timezone, date
from sqlalchemy import (
    String, Text, Float, DateTime, Date, Enum as SAEnum,
    Integer, ForeignKey, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base


class CertificateStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    parsed = "parsed"
    needs_review = "needs_review"
    failed = "failed"


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # File metadata
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    preview_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # OCR output
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Parsed certificate fields
    certificate_number: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    certificate_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    supplier: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Product info
    product_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    normalized_product_name: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    product_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    material: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    gost: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    dimensions: Mapped[str | None] = mapped_column(String(200), nullable=True)
    batch_number: Mapped[str | None] = mapped_column(String(200), nullable=True)
    heat_number: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Additional parsed metadata (stored as JSONB)
    extra_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Processing status
    status: Mapped[CertificateStatus] = mapped_column(
        SAEnum(CertificateStatus, name="certificate_status"),
        nullable=False,
        default=CertificateStatus.uploaded,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Uploaded by
    uploaded_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_certificates_status_created", "status", "created_at"),
        Index("ix_certificates_product_material", "product_type", "material"),
    )

    def __repr__(self) -> str:
        return f"<Certificate id={self.id} num={self.certificate_number} status={self.status}>"
