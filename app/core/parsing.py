from __future__ import annotations

import re


PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_digits(value: str) -> str:
    return value.translate(PERSIAN_DIGITS)


def parse_price(value: str | None) -> int | None:
    if not value or any(word in value for word in ("توافق", "تماس")):
        return None
    normalized = normalize_digits(value).replace("٬", "").replace(",", "")
    numbers = re.findall(r"\d+(?:\.\d+)?", normalized)
    if not numbers:
        return None
    price = max(float(number) for number in numbers)
    if "میلیارد" in value:
        price *= 1_000_000_000
    elif "میلیون" in value:
        price *= 1_000_000
    return int(price)


def parse_area(title: str) -> int | None:
    normalized = normalize_digits(title).replace("٬", "").replace(",", "")
    patterns = (
        r"(?<!\d)(\d{2,4})\s*(?:متر|متری)",
        r"(?:متر|متراژ)\s*[:：-]?\s*(\d{2,4})(?!\d)",
    )
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            area = int(match.group(1))
            if 10 <= area <= 10_000:
                return area
    return None
