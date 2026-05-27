from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from app.models.certificate import CertificateStatus


class CertificateCreate(BaseModel):
    original_filename: Optional[str]
    file_path: Optional[str]
    file_type: Optional[str]
    file_size: Optional[int] = None
    file_hash: Optional[str] = None


class CertificateUpdate(BaseModel):
    certificate_number: Optional[str] = None
    certificate_date: Optional[date] = None
    manufacturer: Optional[str] = None
    supplier: Optional[str] = None
    product_name: Optional[str] = None
    normalized_product_name: Optional[str] = None
    product_type: Optional[str] = None
    material: Optional[str] = None
    gost: Optional[str] = None
    dimensions: Optional[str] = None
    batch_number: Optional[str] = None
    heat_number: Optional[str] = None
    status: Optional[CertificateStatus] = None
    extra_data: Optional[dict[str, Any]] = None


class CertificateResponse(BaseModel):
    id: int
    original_filename: Optional[str]
    file_path: Optional[str]
    preview_path: Optional[str]
    file_type: Optional[str]
    file_size: Optional[int]
    file_hash: Optional[str]
    extracted_text: Optional[str]
    ocr_confidence: Optional[float]
    certificate_number: Optional[str]
    certificate_date: Optional[date]
    manufacturer: Optional[str]
    supplier: Optional[str]
    product_name: Optional[str]
    normalized_product_name: Optional[str]
    product_type: Optional[str]
    material: Optional[str]
    gost: Optional[str]
    dimensions: Optional[str]
    batch_number: Optional[str]
    heat_number: Optional[str]
    status: CertificateStatus
    error_message: Optional[str]
    extra_data: Optional[dict[str, Any]]
    uploaded_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CertificateListResponse(BaseModel):
    items: List[CertificateResponse]
    total: int
    page: int
    page_size: int
    pages: int


class SearchParams(BaseModel):
    q: Optional[str] = Field(None, description="Full-text search query")
    status: Optional[CertificateStatus] = None
    product_type: Optional[str] = None
    material: Optional[str] = None
    gost: Optional[str] = None
    manufacturer: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at", pattern="^(created_at|certificate_date|product_type|material|manufacturer)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


class SearchResult(BaseModel):
    items: List[CertificateResponse]
    total: int
    page: int
    page_size: int
    pages: int
    query: Optional[str] = None
    highlight: Optional[dict[int, str]] = None

