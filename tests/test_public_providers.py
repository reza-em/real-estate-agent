import json

from app.models.category import CAR, PROPERTY
from app.providers.hamrah_mechanic import HamrahMechanicProvider
from app.providers.iranfile import IranFileProvider
from app.providers.kilid import KilidProvider
from app.providers.sheypoor import SheypoorProvider


def test_sheypoor_extracts_public_listing_anchor():
    html = """
    <a href="/v/apartment-123456.html">
      فروش آپارتمان ۸۵ متر، ۸٬۵۰۰٬۰۰۰٬۰۰۰ تومان، تهران پونک
    </a>
    """
    items = SheypoorProvider._extract(html, "تهران", PROPERTY)
    assert len(items) == 1
    assert items[0].external_id == "sheypoor:123456"
    assert items[0].price == 8_500_000_000
    assert items[0].area == 85


def test_kilid_extracts_json_ld_events():
    payload = [
        {
            "@type": "Event",
            "name": "آپارتمان ۱۲۰ متر",
            "location": {"geo": {"latitude": 35.7, "longitude": 51.4}},
            "offers": {
                "price": 12_000_000_000,
                "url": "https://kilid.com/buy/detail/987",
            },
        }
    ]
    html = f'<script type="application/ld+json">{json.dumps(payload)}</script>'
    items = KilidProvider._extract(html, "تهران")
    assert items[0].external_id == "kilid:987"
    assert items[0].area == 120
    assert items[0].has_coordinates


def test_hamrah_mechanic_extracts_next_data_and_filters_city():
    payload = {
        "props": {
            "pageProps": {
                "cars": {
                    "list": [
                        {
                            "orderId": 42,
                            "carNamePersian": "پژو ۲۰۷ مدل ۱۴۰۲",
                            "price": 1_200_000_000,
                            "km": 25000,
                            "gearBoxPersian": "اتومات",
                            "carTypeName": "پانوراما",
                            "cityNamePersian": "تهران",
                            "neighborhood": "اکباتان",
                            "exhibitionDetailUrl": "/cars-for-sale/peugeot/207/42/",
                        },
                        {
                            "orderId": 43,
                            "carNamePersian": "خودرو شهر دیگر",
                            "price": 1,
                            "cityNamePersian": "شیراز",
                            "exhibitionDetailUrl": "/cars-for-sale/test/test/43/",
                        },
                    ]
                }
            }
        }
    }
    html = f'<script id="__NEXT_DATA__">{json.dumps(payload)}</script>'
    items = HamrahMechanicProvider._extract(html, "تهران")
    assert len(items) == 1
    assert items[0].external_id == "hamrah-mechanic:42"
    assert items[0].category == CAR
    assert "25,000 کیلومتر" in items[0].description


def test_iranfile_groups_public_table_cells_by_detail_url():
    href = "/FileDetail/107/فروش_آپارتمان_80_متری"
    html = "".join(
        f'<a href="{href}">{value}</a>'
        for value in (
            "107",
            "آپارتمان",
            "تهران پونک",
            "خرید",
            "8,000,000,000",
        )
    )
    items = IranFileProvider._extract(html, "تهران")
    assert len(items) == 1
    assert items[0].external_id == "iranfile:107"
    assert items[0].price == 8_000_000_000
    assert items[0].area == 80
