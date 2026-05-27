import logging
import os
from typing import Optional
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, status, Query

logger = logging.getLogger(__name__)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.models.certificate import Certificate, CertificateStatus
from app.models.audit_log import AuditLog
from app.schemas.certificate import (
    CertificateResponse,
    CertificateListResponse,
    CertificateUpdate,
)
from app.services.file_service import FileService
from app.workers.tasks import process_certificate, process_certificate_bg

router = APIRouter()
file_service = FileService()


@router.post("/upload", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
async def upload_certificate(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [UserRole.admin, UserRole.manager]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    # Validate file
    await file_service.validate_file(file)

    # Save file to disk
    file_path, file_hash = await file_service.save_upload(file)

    # Check for duplicate
    duplicate = await file_service.check_duplicate(file_hash, db)
    if duplicate:
        return duplicate

    # Create certificate record
    cert = Certificate(
        original_filename=file.filename,
        file_path=file_path,
        file_type=file.content_type or "application/octet-stream",
        file_hash=file_hash,
        status=CertificateStatus.uploaded,
    )
    db.add(cert)
    await db.commit()
    await db.refresh(cert)

    background_tasks.add_task(process_certificate_bg, cert.id)

    return cert


@router.get("", response_model=CertificateListResponse)
async def list_certificates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[CertificateStatus] = None,
    product_type: Optional[str] = None,
    material: Optional[str] = None,
    gost: Optional[str] = None,
    manufacturer: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    sort_by: str = Query("created_at", regex="^(created_at|certificate_date|product_name|manufacturer)$"),
    sort_desc: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Certificate)

    if status:
        query = query.where(Certificate.status == status)
    if product_type:
        query = query.where(Certificate.product_type.ilike(f"%{product_type}%"))
    if material:
        query = query.where(Certificate.material.ilike(f"%{material}%"))
    if gost:
        query = query.where(Certificate.gost.ilike(f"%{gost}%"))
    if manufacturer:
        query = query.where(Certificate.manufacturer.ilike(f"%{manufacturer}%"))
    if date_from:
        query = query.where(Certificate.certificate_date >= date_from)
    if date_to:
        query = query.where(Certificate.certificate_date <= date_to)

    sort_col = getattr(Certificate, sort_by)
    query = query.order_by(sort_col.desc() if sort_desc else sort_col.asc())

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return CertificateListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/{cert_id}", response_model=CertificateResponse)
async def get_certificate(
    cert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Certificate).where(Certificate.id == cert_id))
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="Сертификат не найден")
    return cert


@router.patch("/{cert_id}", response_model=CertificateResponse)
async def update_certificate(
    cert_id: int,
    update_data: CertificateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [UserRole.admin, UserRole.manager]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    result = await db.execute(select(Certificate).where(Certificate.id == cert_id))
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="Сертификат не найден")

    changes = {}
    for field, value in update_data.model_dump(exclude_unset=True).items():
        old_value = getattr(cert, field)
        if old_value != value:
            changes[field] = {"old": str(old_value), "new": str(value)}
            setattr(cert, field, value)

    if changes:
        log = AuditLog(
            user_id=current_user.id,
            action="update",
            entity_type="certificate",
            entity_id=cert_id,
            extra_data={"changes": changes},
        )
        db.add(log)

    await db.commit()
    await db.refresh(cert)
    return cert


@router.delete("/{cert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certificate(
    cert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только администратор может удалять")

    result = await db.execute(select(Certificate).where(Certificate.id == cert_id))
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="Сертификат не найден")

    # Delete files
    for path in [cert.file_path, cert.preview_path]:
        if path and os.path.exists(path):
            os.remove(path)

    log = AuditLog(
        user_id=current_user.id,
        action="delete",
        entity_type="certificate",
        entity_id=cert_id,
        extra_data={"filename": cert.original_filename},
    )
    db.add(log)

    await db.delete(cert)
    await db.commit()


@router.get("/{cert_id}/file")
async def get_certificate_file(
    cert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Certificate).where(Certificate.id == cert_id))
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="Сертификат не найден")
    if not cert.file_path or not os.path.exists(cert.file_path):
        raise HTTPException(status_code=404, detail="Файл не найден")

    return FileResponse(
        cert.file_path,
        filename=cert.original_filename,
        media_type=cert.file_type,
    )


@router.post("/{cert_id}/reprocess", response_model=CertificateResponse)
async def reprocess_certificate(
    cert_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [UserRole.admin, UserRole.manager]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    result = await db.execute(select(Certificate).where(Certificate.id == cert_id))
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="Сертификат не найден")

    cert.status = CertificateStatus.uploaded
    await db.commit()
    await db.refresh(cert)

    background_tasks.add_task(process_certificate_bg, cert_id)
    return cert
