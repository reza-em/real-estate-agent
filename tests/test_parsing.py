from app.core.parsing import parse_area, parse_price


def test_parse_price_with_persian_digits():
    assert parse_price("۸٬۵۰۰٬۰۰۰٬۰۰۰ تومان") == 8_500_000_000


def test_parse_price_with_unit():
    assert parse_price("قیمت: ۸.۵ میلیارد تومان") == 8_500_000_000


def test_parse_area_from_persian_title():
    assert parse_area("آپارتمان ۸۰ متری دو خوابه") == 80
