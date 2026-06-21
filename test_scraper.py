from scraper import DivarProvider, parse_price


def test_parse_price_with_persian_digits():
    assert parse_price("۸٬۵۰۰٬۰۰۰٬۰۰۰ تومان") == 8_500_000_000


def test_parse_price_with_unit():
    assert parse_price("قیمت: ۸.۵ میلیارد تومان") == 8_500_000_000


def test_extract_post_rows_only():
    payload = {
        "list_widgets": [
            {
                "widget_type": "POST_ROW",
                "data": {
                    "token": "abc",
                    "title": "آپارتمان ۸۰ متری",
                    "middle_description_text": "۷٬۰۰۰٬۰۰۰٬۰۰۰ تومان",
                    "action": {
                        "payload": {
                            "web_info": {
                                "city_persian": "تهران",
                                "district_persian": "پونک",
                            }
                        }
                    },
                },
            },
            {"widget_type": "BANNER", "data": {}},
        ]
    }
    result = DivarProvider._extract(payload)
    assert len(result) == 1
    assert result[0].price == 7_000_000_000
    assert result[0].location == "تهران، پونک"


def test_payload_uses_current_category():
    payload = DivarProvider._payload("1", 1)
    category = payload["search_data"]["form_data"]["data"]["category"]
    assert category["str"]["value"] == "apartment-sell"
