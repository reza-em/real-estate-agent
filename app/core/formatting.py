from __future__ import annotations


def format_toman(price: int | None) -> str:
    if price is None:
        return "قیمت توافقی"
    if price >= 1_000_000_000:
        value = price / 1_000_000_000
        formatted = f"{value:,.1f}".rstrip("0").rstrip(".")
        return f"{formatted} میلیارد تومان"
    return f"{price:,} تومان"
