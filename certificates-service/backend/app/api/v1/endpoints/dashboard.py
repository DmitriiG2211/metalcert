from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.certificate import Certificate, CertificateStatus

router = APIRouter()


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Total certificates
    total_result = await db.execute(select(func.count(Certificate.id)))
    total = total_result.scalar_one()

    # By status
    status_result = await db.execute(
        select(Certificate.status, func.count(Certificate.id))
        .group_by(Certificate.status)
    )
    by_status = {row[0].value: row[1] for row in status_result.all()}

    # By product type (top 10)
    type_result = await db.execute(
        select(Certificate.product_type, func.count(Certificate.id))
        .where(Certificate.product_type.isnot(None))
        .group_by(Certificate.product_type)
        .order_by(func.count(Certificate.id).desc())
        .limit(10)
    )
    by_product_type = [
        {"product_type": row[0], "count": row[1]} for row in type_result.all()
    ]

    # By manufacturer (top 10)
    mfr_result = await db.execute(
        select(Certificate.manufacturer, func.count(Certificate.id))
        .where(Certificate.manufacturer.isnot(None))
        .group_by(Certificate.manufacturer)
        .order_by(func.count(Certificate.id).desc())
        .limit(10)
    )
    by_manufacturer = [
        {"manufacturer": row[0], "count": row[1]} for row in mfr_result.all()
    ]

    # By GOST (top 10)
    gost_result = await db.execute(
        select(Certificate.gost, func.count(Certificate.id))
        .where(Certificate.gost.isnot(None))
        .group_by(Certificate.gost)
        .order_by(func.count(Certificate.id).desc())
        .limit(10)
    )
    by_gost = [{"gost": row[0], "count": row[1]} for row in gost_result.all()]

    # Recent uploads (last 10)
    recent_result = await db.execute(
        select(Certificate).order_by(Certificate.created_at.desc()).limit(10)
    )
    recent = recent_result.scalars().all()

    return {
        "total": total,
        "by_status": by_status,
        "needs_review": by_status.get(CertificateStatus.NEEDS_REVIEW.value, 0),
        "failed": by_status.get(CertificateStatus.FAILED.value, 0),
        "by_product_type": by_product_type,
        "by_manufacturer": by_manufacturer,
        "by_gost": by_gost,
        "recent_uploads": [
            {
                "id": c.id,
                "original_filename": c.original_filename,
                "product_name": c.normalized_product_name or c.product_name,
                "status": c.status.value,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in recent
        ],
    }
