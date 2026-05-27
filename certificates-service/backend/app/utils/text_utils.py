import re
import unicodedata
from typing import List


# Common OCR substitution errors in Cyrillic text
_OCR_SUBSTITUTIONS = [
    # Latin look-alikes confused for Cyrillic
    (r"(?<=[А-ЯЁа-яё\d])0(?=[А-ЯЁа-яё\d])", "О"),  # digit 0 -> Cyrillic О
    (r"(?<=[А-ЯЁа-яё])0(?=[А-ЯЁа-яё])", "О"),
    (r"\bO(?=[А-ЯЁа-яё])", "О"),  # Latin O before Cyrillic
    (r"(?<=[А-ЯЁа-яё])O\b", "О"),
    (r"\bC(?=[А-ЯЁа-яё])", "С"),  # Latin C -> Cyrillic С
    (r"(?<=[А-ЯЁа-яё])C\b", "С"),
    (r"\bP(?=[А-ЯЁа-яё])", "Р"),  # Latin P -> Cyrillic Р
    (r"\bA(?=[А-ЯЁа-яё])", "А"),  # Latin A -> Cyrillic А
    (r"\bE(?=[А-ЯЁа-яё])", "Е"),  # Latin E -> Cyrillic Е
    (r"\bH(?=[А-ЯЁа-яё])", "Н"),  # Latin H -> Cyrillic Н
    (r"\bM(?=[А-ЯЁа-яё])", "М"),  # Latin M -> Cyrillic М
    (r"\bT(?=[А-ЯЁа-яё])", "Т"),  # Latin T -> Cyrillic Т
    (r"\bB(?=[А-ЯЁа-яё])", "В"),  # Latin B -> Cyrillic В
    (r"\bK(?=[А-ЯЁа-яё])", "К"),  # Latin K -> Cyrillic К
    (r"\bX(?=[А-ЯЁа-яё])", "Х"),  # Latin X -> Cyrillic Х
    # Digit in Cyrillic word context
    (r"(?<=[А-ЯЁа-яё])1(?=[А-ЯЁа-яё])", "І"),
    # Fix ё/е confusion (normalize)
    (r"ё", "е"),  # normalize ё -> е for matching purposes
]

_COMPILED_SUBSTITUTIONS = [
    (re.compile(pattern), replacement)
    for pattern, replacement in _OCR_SUBSTITUTIONS
]

# Russian month names for date parsing
RUSSIAN_MONTHS = {
    "января": "January",
    "февраля": "February",
    "марта": "March",
    "апреля": "April",
    "мая": "May",
    "июня": "June",
    "июля": "July",
    "августа": "August",
    "сентября": "September",
    "октября": "October",
    "ноября": "November",
    "декабря": "December",
    "январь": "January",
    "февраль": "February",
    "март": "March",
    "апрель": "April",
    "май": "May",
    "июнь": "June",
    "июль": "July",
    "август": "August",
    "сентябрь": "September",
    "октябрь": "October",
    "ноябрь": "November",
    "декабрь": "December",
}


def fix_ocr_artifacts(text: str) -> str:
    """Apply common OCR substitutions for mixed Latin/Cyrillic text."""
    for pattern, replacement in _COMPILED_SUBSTITUTIONS:
        text = pattern.sub(replacement, text)
    return text


def normalize_russian_text(text: str) -> str:
    """Normalize Russian text: fix encoding issues, whitespace, common OCR errors."""
    if not text:
        return ""

    # Normalize unicode
    text = unicodedata.normalize("NFC", text)

    # Fix OCR artifacts
    text = fix_ocr_artifacts(text)

    # Collapse multiple spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize line endings
    text = re.sub(r"\r\n?", "\n", text)

    # Remove excessive blank lines (more than 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


def transliterate(text: str) -> str:
    """Transliterate Russian text to Latin."""
    mapping = {
        "А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D",
        "Е": "E", "Ё": "Yo", "Ж": "Zh", "З": "Z", "И": "I",
        "Й": "Y", "К": "K", "Л": "L", "М": "M", "Н": "N",
        "О": "O", "П": "P", "Р": "R", "С": "S", "Т": "T",
        "У": "U", "Ф": "F", "Х": "Kh", "Ц": "Ts", "Ч": "Ch",
        "Ш": "Sh", "Щ": "Shch", "Ъ": "", "Ы": "Y", "Ь": "",
        "Э": "E", "Ю": "Yu", "Я": "Ya",
    }
    mapping.update({k.lower(): v.lower() for k, v in mapping.items()})

    result = []
    for char in text:
        result.append(mapping.get(char, char))
    return "".join(result)


def extract_numbers(text: str) -> List[str]:
    """Extract all numeric values (integers and floats) from text."""
    pattern = r"\b\d+(?:[.,]\d+)?\b"
    return re.findall(pattern, text)


def clean_extra_spaces(text: str) -> str:
    """Remove extra whitespace."""
    return re.sub(r"\s+", " ", text).strip()


def replace_russian_months(text: str) -> str:
    """Replace Russian month names with English equivalents for dateutil parsing."""
    text_lower = text.lower()
    for ru_month, en_month in RUSSIAN_MONTHS.items():
        text_lower = text_lower.replace(ru_month, en_month)
    return text_lower


def normalize_gost(gost: str) -> str:
    """Normalize GOST string: uppercase, fix spaces."""
    if not gost:
        return gost
    gost = gost.upper().strip()
    # Ensure proper spacing: ГОСТ NNNN-NN
    gost = re.sub(r"\s+", " ", gost)
    # Fix common OCR: ГОСТ8639 -> ГОСТ 8639
    gost = re.sub(r"(ГОСТ|ТУ)(\d)", r"\1 \2", gost)
    return gost


def normalize_steel_grade(grade: str) -> str:
    """Normalize steel grade: handle case, spaces."""
    if not grade:
        return grade
    # Remove extra spaces
    grade = re.sub(r"\s+", "", grade)
    # Capitalize properly: ст3 -> Ст3
    grade = re.sub(r"(?i)^ст(\w+)", lambda m: "Ст" + m.group(1), grade)
    return grade
