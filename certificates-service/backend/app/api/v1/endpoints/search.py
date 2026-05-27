from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, or_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.certificate import Certificate, CertificateStatus
from app.schemas.certificate import CertificateListResponse

router = APIRouter()


@router.get("", response_model=CertificateListResponse)
async def search_certificates(
    q: Optional[str] = Query(None, description="Search query"),
    product_type: Optional[str] = None,
    material: Optional[str] = None,
    gost: Optional[str] = None,
    manufacturer: Optional[str] = None,
    dimensions: Optional[str] = None,
    status: Optional[CertificateStatus] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Certificate)

    if q and q.strip():
        q_clean = q.strip()
        # Full-text search using PostgreSQL tsvector
        fts_condition = text(
            "to_tsvector('russian', COALESCE(normalized_product_name, '') || ' ' || "
            "COALESCE(extracted_text, '') || ' ' || COALESCE(manufacturer, '') || ' ' || "
            "COALESCE(gost, '') || ' ' || COALESCE(material, '') || ' ' || "
            "COALESCE(certificate_number, '') || ' ' || COALESCE(dimensions, '')) "
            "@@ plainto_tsquery('russian', :query)"
        ).bindparams(query=q_clean)

        # Also do ILIKE for partial matches (handles short queries, codes)
        like_condition = or_(
            Certificate.normalized_product_name.ilike(f"%{q_clean}%"),
            Certificate.material.ilike(f"%{q_clean}%"),
            Certificate.gost.ilike(f"%{q_clean}%"),
            Certificate.dimensions.ilike(f"%{q_clean}%"),
            Certificate.certificate_number.ilike(f"%{q_clean}%"),
            Certificate.manufacturer.ilike(f"%{q_clean}%"),
            Certificate.batch_number.ilike(f"%{q_clean}%"),
            Certificate.extracted_text.ilike(f"%{q_clean}%"),
        )

        query = query.where(or_(fts_condition, like_condition))

    # Apply filters
    if product_type:
        query = query.where(Certificate.product_type.ilike(f"%{product_type}%"))
    if material:
        query = query.where(Certificate.material.ilike(f"%{material}%"))
    if gost:
        query = query.where(Certificate.gost.ilike(f"%{gost}%"))
    if manufacturer:
        query = query.where(Certificate.manufacturer.ilike(f"%{manufacturer}%"))
    if dimensions:
        query = query.where(Certificate.dimensions.ilike(f"%{dimensions}%"))
    if status:
        query = query.where(Certificate.status == status)
    if date_from:
        query = query.where(Certificate.certificate_date >= date_from)
    if date_to:
        query = query.where(Certificate.certificate_date <= date_to)

    query = query.order_by(Certificate.created_at.desc())

    # Count
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    # Paginate
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    items = result.scalars().all()

    return CertificateListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )
