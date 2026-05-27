import io
import logging
import re
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class OCRService:
    """Service for extracting text from PDF and image files."""

    SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif"}
    SUPPORTED_PDF_EXTENSIONS = {".pdf"}

    def __init__(self) -> None:
        self._tesseract_available: Optional[bool] = None

    def _check_tesseract(self) -> bool:
        if self._tesseract_available is None:
            try:
                import pytesseract
                pytesseract.get_tesseract_version()
                self._tesseract_available = True
            except Exception:
                self._tesseract_available = False
                logger.warning("Tesseract not available; OCR on images will be limited.")
        return self._tesseract_available

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def extract_text(self, file_path: str) -> Tuple[str, float]:
        """Extract text from a file. Returns (text, confidence_score)."""
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext in self.SUPPORTED_PDF_EXTENSIONS:
            return await self.extract_text_from_pdf(file_path)
        elif ext in self.SUPPORTED_IMAGE_EXTENSIONS:
            return await self.extract_text_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    async def extract_text_from_pdf(self, file_path: str) -> Tuple[str, float]:
        """
        Try pdfplumber first (native text layer).
        Fallback to PyMuPDF.
        Fallback to image-based OCR page by page.
        """
        text = ""
        confidence = 0.0

        # --- Attempt 1: pdfplumber (best for PDFs with text layer) ---
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                pages_text = []
                for page in pdf.pages:
                    page_text = page.extract_text(x_tolerance=3, y_tolerance=3)
                    if page_text:
                        pages_text.append(page_text)
                if pages_text:
                    text = "\n\n".join(pages_text)
                    confidence = self.calculate_confidence(text)
                    if confidence > 0.3 and len(text.strip()) > 50:
                        logger.info(f"pdfplumber extracted {len(text)} chars, confidence={confidence:.2f}")
                        return self.clean_text(text), confidence
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}")

        # --- Attempt 2: PyMuPDF (fitz) ---
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            pages_text = []
            for page in doc:
                page_text = page.get_text("text")
                if page_text.strip():
                    pages_text.append(page_text)
            doc.close()
            if pages_text:
                text = "\n\n".join(pages_text)
                confidence = self.calculate_confidence(text)
                if confidence > 0.3 and len(text.strip()) > 50:
                    logger.info(f"PyMuPDF extracted {len(text)} chars, confidence={confidence:.2f}")
                    return self.clean_text(text), confidence
        except Exception as e:
            logger.warning(f"PyMuPDF text extraction failed: {e}")

        # --- Attempt 3: OCR via rendering pages as images ---
        logger.info("Falling back to image-based OCR for PDF")
        text, confidence = await self._ocr_pdf_as_images(file_path)
        return self.clean_text(text), confidence

    async def _ocr_pdf_as_images(self, file_path: str) -> Tuple[str, float]:
        """Render PDF pages as images and run OCR."""
        try:
            import fitz
            from PIL import Image

            doc = fitz.open(file_path)
            pages_text = []
            confidences = []

            for page_num in range(min(len(doc), 10)):  # limit to 10 pages
                page = doc[page_num]
                # Render at 200 DPI
                mat = fitz.Matrix(200 / 72, 200 / 72)
                pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
                img_bytes = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_bytes))
                page_text, conf = await self._run_tesseract(img)
                if page_text.strip():
                    pages_text.append(page_text)
                    confidences.append(conf)

            doc.close()
            combined_text = "\n\n".join(pages_text)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            return combined_text, avg_confidence

        except Exception as e:
            logger.error(f"OCR PDF as images failed: {e}")
            return "", 0.0

    async def extract_text_from_image(self, file_path: str) -> Tuple[str, float]:
        """Extract text from an image file using pytesseract."""
        try:
            from PIL import Image
            img = Image.open(file_path)
            preprocessed = self.preprocess_image(img)
            text, confidence = await self._run_tesseract(preprocessed)
            return self.clean_text(text), confidence
        except Exception as e:
            logger.error(f"Image OCR failed for {file_path}: {e}")
            return "", 0.0

    def preprocess_image(self, img):
        """
        Preprocess image with OpenCV for better OCR accuracy:
        grayscale -> denoise -> adaptive threshold.
        """
        try:
            import cv2
            import numpy as np
            from PIL import Image

            # Convert PIL to numpy
            img_array = np.array(img.convert("RGB"))
            # BGR -> Gray
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            # Denoise
            denoised = cv2.fastNlMeansDenoising(gray, h=10)
            # Adaptive threshold (handles uneven lighting)
            thresh = cv2.adaptiveThreshold(
                denoised,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                blockSize=31,
                C=10,
            )
            # Deskew if needed (simple rotation correction via Hough lines)
            # Morph open to remove noise
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            return Image.fromarray(cleaned)
        except ImportError:
            logger.warning("OpenCV not available, using raw image")
            return img
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}; using raw image")
            return img

    async def _run_tesseract(self, img) -> Tuple[str, float]:
        """Run pytesseract on a PIL image and return (text, confidence)."""
        if not self._check_tesseract():
            return "", 0.0
        try:
            import pytesseract
            from app.core.config import settings

            config = f"--oem 3 --psm 6 -l {settings.TESSERACT_LANG}"
            # Get detailed output with confidence scores
            data = pytesseract.image_to_data(
                img, config=config, output_type=pytesseract.Output.DICT
            )
            text = pytesseract.image_to_string(img, config=config)

            # Calculate confidence from word-level scores
            confidences = [
                int(c)
                for c in data["conf"]
                if str(c).lstrip("-").isdigit() and int(c) >= 0
            ]
            avg_conf = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            return text, avg_conf
        except Exception as e:
            logger.error(f"Tesseract error: {e}")
            return "", 0.0

    def clean_text(self, text: str) -> str:
        """Normalize OCR output: fix whitespace, remove junk characters."""
        if not text:
            return ""
        from app.utils.text_utils import normalize_russian_text

        text = normalize_russian_text(text)
        # Remove non-printable characters except newline/tab
        text = re.sub(r"[^\x09\x0A\x0D\x20-\x7EЀ-ӿÀ-ɏ]", "", text)
        # Collapse excessive whitespace
        text = re.sub(r" {3,}", "  ", text)
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        return text.strip()

    def calculate_confidence(self, text: str) -> float:
        """
        Heuristic confidence score for extracted text quality.
        Based on ratio of Cyrillic+Latin+digits to total printable chars,
        and presence of expected certificate keywords.
        """
        if not text or len(text.strip()) < 10:
            return 0.0

        printable = [c for c in text if c.isprintable()]
        if not printable:
            return 0.0

        cyrillic = sum(1 for c in printable if "Ѐ" <= c <= "ӿ")
        latin = sum(1 for c in printable if c.isalpha() and c.isascii())
        digits = sum(1 for c in printable if c.isdigit())
        useful = cyrillic + latin + digits
        ratio = useful / len(printable) if printable else 0.0

        # Bonus for certificate-specific keywords
        keywords = [
            "сертификат", "гост", "марка", "сталь", "плавка", "партия",
            "завод", "труба", "лист", "арматура", "размер", "мм",
        ]
        keyword_hits = sum(
            1 for kw in keywords if kw.lower() in text.lower()
        )
        keyword_bonus = min(keyword_hits * 0.05, 0.3)

        score = min(ratio * 0.7 + keyword_bonus, 1.0)
        return round(score, 4)
