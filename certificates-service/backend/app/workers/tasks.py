import logging

from celery import shared_task
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks.process_certificate", max_retries=3, default_retry_delay=30)
def process_certificate(self, certificate_id: int) -> dict:
    """
    Background task: OCR + parse a certificate.
    Uses sync DB session since Celery workers are synchronous.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    from app.models.certificate import Certificate, CertificateStatus
    from app.services.ocr_service import OCRService
    from app.services.parser_service import parser_service
    from app.services.file_service import FileService

    engine = create_engine(settings.DATABASE_URL_SYNC, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)
    db: Session = SessionLocal()

    try:
        cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
        if not cert:
            logger.error(f"Certificate {certificate_id} not found")
            return {"error": "not_found"}

        cert.status = CertificateStatus.processing
        db.commit()

        logger.info(f"Processing certificate {certificate_id}: {cert.original_filename}")

        file_svc = FileService()
        preview_path = file_svc.generate_preview(cert.file_path)
        if preview_path:
            cert.preview_path = preview_path

        import asyncio
        ocr_svc = OCRService()

        loop = asyncio.new_event_loop()
        try:
            text, confidence = loop.run_until_complete(ocr_svc.extract_text(cert.file_path))
        finally:
            loop.close()

        cert.extracted_text = text
        cert.ocr_confidence = confidence

        if text:
            parsed = parser_service.parse_certificate(text)
            cert.product_name = parsed.get("product_name")
            cert.normalized_product_name = parsed.get("normalized_product_name")
            cert.product_type = parsed.get("product_type")
            cert.material = parsed.get("material")
            cert.gost = parsed.get("gost")
            cert.dimensions = parsed.get("dimensions")
            cert.certificate_number = parsed.get("certificate_number")
            cert.certificate_date = parsed.get("certificate_date")
            cert.manufacturer = parsed.get("manufacturer")
            cert.batch_number = parsed.get("batch_number")
            cert.heat_number = parsed.get("heat_number")

        if not text or confidence < 0.3:
            cert.status = CertificateStatus.needs_review
        elif not cert.normalized_product_name:
            cert.status = CertificateStatus.needs_review
        else:
            cert.status = CertificateStatus.parsed

        db.commit()
        logger.info(f"Certificate {certificate_id} processed: status={cert.status.value}")
        return {"status": cert.status.value, "confidence": confidence}

    except Exception as exc:
        logger.exception(f"Failed to process certificate {certificate_id}: {exc}")
        try:
            cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
            if cert:
                cert.status = CertificateStatus.failed
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc)
    finally:
        db.close()
        engine.dispose()


async def process_certificate_bg(certificate_id: int) -> None:
    """Async processing via FastAPI BackgroundTasks (no Celery/Redis required)."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    from app.core.config import settings
    from app.models.certificate import Certificate, CertificateStatus
    from app.services.ocr_service import OCRService
    from app.services.parser_service import parser_service
    from app.services.file_service import FileService

    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            result = await db.execute(select(Certificate).where(Certificate.id == certificate_id))
            cert = result.scalar_one_or_none()
            if not cert:
                logger.error(f"Certificate {certificate_id} not found")
                return

            cert.status = CertificateStatus.processing
            await db.commit()

            logger.info(f"[bg] Processing certificate {certificate_id}: {cert.original_filename}")

            file_svc = FileService()
            preview_path = file_svc.generate_preview(cert.file_path)
            if preview_path:
                cert.preview_path = preview_path

            ocr_svc = OCRService()
            text, confidence = await ocr_svc.extract_text(cert.file_path)
            cert.extracted_text = text
            cert.ocr_confidence = confidence

            if text:
                parsed = parser_service.parse_certificate(text)
                cert.product_name = parsed.get("product_name")
                cert.normalized_product_name = parsed.get("normalized_product_name")
                cert.product_type = parsed.get("product_type")
                cert.material = parsed.get("material")
                cert.gost = parsed.get("gost")
                cert.dimensions = parsed.get("dimensions")
                cert.certificate_number = parsed.get("certificate_number")
                cert.certificate_date = parsed.get("certificate_date")
                cert.manufacturer = parsed.get("manufacturer")
                cert.batch_number = parsed.get("batch_number")
                cert.heat_number = parsed.get("heat_number")

            if not text or confidence < 0.3:
                cert.status = CertificateStatus.needs_review
            elif not cert.normalized_product_name:
                cert.status = CertificateStatus.needs_review
            else:
                cert.status = CertificateStatus.parsed

            await db.commit()
            logger.info(f"[bg] Certificate {certificate_id} done: status={cert.status.value}, conf={confidence:.2f}")

        except Exception as exc:
            logger.exception(f"[bg] Failed to process certificate {certificate_id}: {exc}")
            try:
                result = await db.execute(select(Certificate).where(Certificate.id == certificate_id))
                cert = result.scalar_one_or_none()
                if cert:
                    cert.status = CertificateStatus.failed
                    cert.error_message = str(exc)[:500]
                    await db.commit()
            except Exception:
                pass
        finally:
            await engine.dispose()
