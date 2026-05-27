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

        # Update status
        cert.status = CertificateStatus.PROCESSING
        db.commit()

        logger.info(f"Processing certificate {certificate_id}: {cert.original_filename}")

        # Generate preview (sync)
        file_svc = FileService()
        preview_path = file_svc.generate_preview(cert.file_path)
        if preview_path:
            cert.preview_path = preview_path

        # OCR extraction (run sync wrapper)
        import asyncio
        ocr_svc = OCRService()

        loop = asyncio.new_event_loop()
        try:
            text, confidence = loop.run_until_complete(ocr_svc.extract_text(cert.file_path))
        finally:
            loop.close()

        cert.extracted_text = text
        cert.ocr_confidence = confidence

        # Parse extracted text
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

        # Determine final status
        if not text or confidence < 0.3:
            cert.status = CertificateStatus.NEEDS_REVIEW
        elif not cert.normalized_product_name:
            cert.status = CertificateStatus.NEEDS_REVIEW
        else:
            cert.status = CertificateStatus.PARSED

        db.commit()
        logger.info(f"Certificate {certificate_id} processed: status={cert.status.value}")
        return {"status": cert.status.value, "confidence": confidence}

    except Exception as exc:
        logger.exception(f"Failed to process certificate {certificate_id}: {exc}")
        try:
            cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
            if cert:
                cert.status = CertificateStatus.FAILED
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc)
    finally:
        db.close()
        engine.dispose()
