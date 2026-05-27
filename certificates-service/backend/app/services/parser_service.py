import re
import logging
from typing import Optional, Dict, Any
from datetime import date, datetime

from rapidfuzz import fuzz, process as fuzz_process

logger = logging.getLogger(__name__)


class MetalProductParser:
    """
    Parser engine for metal product certificates.
    Extracts structured data from raw OCR text using regex + fuzzy matching.
    """

    PRODUCT_TYPES: Dict[str, list] = {
        "труба профильная": ["труба проф", "профтруба", "профильная труба"],
        "труба круглая": ["труба к/с", "труба круглая"],
        "труба вгп": ["труба водогазопроводная", "вгп", "водогазопроводная"],
        "труба электросварная": ["труба эс", "эсв", "труба эсв", "электросварная"],
        "труба бесшовная": ["бесшовная", "г/д труба", "х/д труба"],
        "лист": ["листовой прокат", "лист г/к", "лист х/к", "листовой"],
        "арматура": ["арм", "арматурный прокат", "стержень"],
        "швеллер": ["швеллер"],
        "уголок": ["уголок равнополочный", "уголок неравнополочный"],
        "круг": ["пруток", "круг стальной"],
        "балка": ["двутавр", "двутавровая балка"],
        "полоса": ["полосовая сталь", "полосовой прокат"],
        "квадрат": ["квадрат стальной"],
        "шестигранник": ["шестигранник стальной"],
        "сетка": ["сетка сварная", "сетка арматурная"],
    }

    STEEL_GRADES = [
        "ст3", "ст3сп", "ст3пс", "ст3кп", "ст3гсп",
        "09г2с", "09г2", "с255", "с345", "с390", "с440",
        "ст45", "ст20", "ст10", "ст40х",
        "а500с", "в500с", "а240", "а300", "а400",
        "12хн3а", "40хн", "30хгса", "65г",
        "aisi 304", "aisi 316", "aisi 430",
    ]

    MONTH_RU = {
        "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
        "мая": 5, "июня": 6, "июля": 7, "августа": 8,
        "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
        "январь": 1, "февраль": 2, "март": 3, "апрель": 4,
        "май": 5, "июнь": 6, "июль": 7, "август": 8,
        "сентябрь": 9, "октябрь": 10, "ноябрь": 11, "декабрь": 12,
    }

    ORGANIZATION_PREFIXES = [
        "ооо", "оао", "зао", "пао", "ао", "фгуп", "гуп", "нпп", "нпо", "мз",
        "завод", "комбинат", "металлургический", "меткомбинат",
    ]

    def parse_certificate(self, text: str) -> Dict[str, Any]:
        """Parse raw OCR text and return structured certificate data."""
        if not text:
            return {}

        text_lower = text.lower()

        result = {
            "product_type": self.extract_product_type(text),
            "dimensions": self.extract_dimensions(text),
            "material": self.extract_steel_grade(text),
            "gost": self.extract_gost(text),
            "certificate_number": self.extract_certificate_number(text),
            "certificate_date": self.extract_certificate_date(text),
            "manufacturer": self.extract_manufacturer(text),
            "batch_number": self.extract_batch_number(text),
            "heat_number": self.extract_heat_number(text),
        }

        # Build normalized product name
        result["normalized_product_name"] = self.normalize_product_name(result)
        result["product_name"] = result["normalized_product_name"]

        return result

    def extract_product_type(self, text: str) -> Optional[str]:
        text_lower = text.lower()

        # Direct match first
        for product_type, aliases in self.PRODUCT_TYPES.items():
            all_names = [product_type] + aliases
            for name in all_names:
                if name in text_lower:
                    return product_type.title()

        # Fuzzy match on first 500 chars (product name usually near top)
        excerpt = text_lower[:500]
        words = excerpt.split()
        for i in range(len(words)):
            phrase = " ".join(words[i:i+3])
            match = fuzz_process.extractOne(
                phrase,
                list(self.PRODUCT_TYPES.keys()),
                scorer=fuzz.partial_ratio,
                score_cutoff=80,
            )
            if match:
                return match[0].title()

        return None

    def extract_dimensions(self, text: str) -> Optional[str]:
        # Pattern: 120х120х4 or 50x50x5 or 12 мм or 3,5 мм
        patterns = [
            r'\d+[хx×]\d+[хx×]\d+(?:[,\.]\d+)?',    # 120х120х4
            r'\d+(?:[,\.]\d+)?[хx×]\d+(?:[,\.]\d+)?', # 76x3.5
            r'\d+(?:[,\.]\d+)?\s*мм',                  # 12 мм
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                dim = m.group(0).strip()
                # Normalize x separators
                dim = re.sub(r'[xX×]', 'х', dim)
                return dim
        return None

    def extract_steel_grade(self, text: str) -> Optional[str]:
        # Try direct regex patterns for common grades
        grade_pattern = re.compile(
            r'\b('
            r'ст\s*3(?:сп|пс|кп|гсп)?|'
            r'\d{2}г\d?с?|'
            r'с\d{3}|'
            r'[аА][45]00[сС]?|'
            r'[вВ]500[сС]?|'
            r'[аА][2-4]\d{2}|'
            r'ст\s*\d{1,2}(?:х|г|мн|с)?|'
            r'aisi\s*\d{3}'
            r')',
            re.IGNORECASE
        )
        matches = grade_pattern.findall(text)
        if matches:
            # Return the first one, normalized
            grade = matches[0].strip()
            grade = re.sub(r'\s+', '', grade)
            return grade.upper() if len(grade) <= 5 else grade.title()

        # Fuzzy fallback
        text_lower = text.lower()
        match = fuzz_process.extractOne(
            text_lower,
            self.STEEL_GRADES,
            scorer=fuzz.partial_ratio,
            score_cutoff=90,
        )
        if match:
            return match[0].upper()

        return None

    def extract_gost(self, text: str) -> Optional[str]:
        # ГОСТ NNNN-NN or ТУ patterns
        patterns = [
            r'ГОСТ\s+Р?\s*\d{4,6}(?:[–\-]\d{2,4})?',
            r'ТУ\s+\d{1,2}[–\-]\d{3,6}(?:[–\-]\d{3,6})?(?:[–\-]\d{2,4})?',
            r'ДСТУ\s+\d{4,6}',
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return m.group(0).strip()
        return None

    def extract_certificate_number(self, text: str) -> Optional[str]:
        patterns = [
            r'(?:сертификат|свидетельство|удостоверение)\s*(?:качества|соответствия)?\s*[№#N]\s*([\w\-/]+)',
            r'[№#]\s*([\w\-/]{3,20})',
            r'(?:номер|N|No\.?)\s*:?\s*([\w\-/]{3,20})',
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    def extract_certificate_date(self, text: str) -> Optional[date]:
        # DD.MM.YYYY or DD/MM/YYYY
        m = re.search(r'(\d{1,2})[./](\d{1,2})[./](\d{4})', text)
        if m:
            try:
                return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            except ValueError:
                pass

        # "15 января 2023" style
        ru_date = re.search(
            r'(\d{1,2})\s+(' + '|'.join(self.MONTH_RU.keys()) + r')\s+(\d{4})',
            text, re.IGNORECASE
        )
        if ru_date:
            try:
                day = int(ru_date.group(1))
                month = self.MONTH_RU.get(ru_date.group(2).lower(), 0)
                year = int(ru_date.group(3))
                if month:
                    return date(year, month, day)
            except ValueError:
                pass

        # YYYY-MM-DD (ISO)
        m2 = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
        if m2:
            try:
                return date(int(m2.group(1)), int(m2.group(2)), int(m2.group(3)))
            except ValueError:
                pass

        return None

    def extract_manufacturer(self, text: str) -> Optional[str]:
        # Look for organization indicators
        patterns = [
            r'(?:производитель|изготовитель|завод|поставщик)\s*:?\s*([А-ЯA-Z][^\n,]{3,50})',
            r'\b(?:ООО|ОАО|ЗАО|ПАО|АО)\s+[«"]([^»"]{3,50})[»"]',
            r'\b(?:ООО|ОАО|ЗАО|ПАО|АО)\s+"([^"]{3,50})"',
            r'\b(?:ООО|ОАО|ЗАО|ПАО|АО)\s+([А-ЯA-Z][а-яА-Яa-zA-Z\s]{2,40})',
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                name = m.group(1).strip().rstrip('.,;')
                if len(name) > 3:
                    return name
        return None

    def extract_batch_number(self, text: str) -> Optional[str]:
        m = re.search(
            r'(?:партия|лот|batch|п/п)\s*[№#:]\s*([\w\-/]+)',
            text, re.IGNORECASE
        )
        return m.group(1).strip() if m else None

    def extract_heat_number(self, text: str) -> Optional[str]:
        m = re.search(
            r'(?:плавка|heat)\s*[№#:]\s*([\w\-/]+)',
            text, re.IGNORECASE
        )
        return m.group(1).strip() if m else None

    def normalize_product_name(self, data: Dict[str, Any]) -> str:
        parts = []
        if data.get("product_type"):
            parts.append(data["product_type"])
        if data.get("dimensions"):
            parts.append(data["dimensions"])
        if data.get("material"):
            parts.append(data["material"])
        if data.get("gost"):
            parts.append(data["gost"])
        return " ".join(parts) if parts else ""


parser_service = MetalProductParser()
