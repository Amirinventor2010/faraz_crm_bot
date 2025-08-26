from __future__ import annotations

_PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
_ARABIC_DIGITS  = "٠١٢٣٤٥٦٧٨٩"
_EN_DIGITS      = "0123456789"

_TRANS = {}
for fa, en in zip(_PERSIAN_DIGITS, _EN_DIGITS):
    _TRANS[ord(fa)] = en
for ar, en in zip(_ARABIC_DIGITS, _EN_DIGITS):
    _TRANS[ord(ar)] = en

def normalize_digits(s: str) -> str:
    """فارسی/عربی → انگلیسی؛ حذف فاصله‌های غیرضروری."""
    return (s or "").translate(_TRANS).strip()

def parse_numeric(text: str) -> float:
    """
    "12", "12.5", "12,345", "۱۲٫۵", "7%" → float
    """
    raw = normalize_digits(text).replace(",", "")
    if raw.endswith("%"):
        raw = raw[:-1]
    return float(raw)

def is_positive_number(text: str) -> bool:
    try:
        return parse_numeric(text) >= 0
    except Exception:
        return False
