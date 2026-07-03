CITY_SLUGS = {
    "اراک": "arak",
    "اردبیل": "ardabil",
    "ارومیه": "urmia",
    "اصفهان": "isfahan",
    "اهواز": "ahvaz",
    "ایلام": "ilam",
    "بجنورد": "bojnurd",
    "بندرعباس": "bandar-abbas",
    "بوشهر": "bushehr",
    "بیرجند": "birjand",
    "تبریز": "tabriz",
    "تهران": "tehran",
    "خرم‌آباد": "khorramabad",
    "رشت": "rasht",
    "زاهدان": "zahedan",
    "زنجان": "zanjan",
    "ساری": "sari",
    "سمنان": "semnan",
    "سنندج": "sanandaj",
    "شهرکرد": "shahrekord",
    "شیراز": "shiraz",
    "قزوین": "qazvin",
    "قم": "qom",
    "کرج": "karaj",
    "کرمان": "kerman",
    "کرمانشاه": "kermanshah",
    "گرگان": "gorgan",
    "مشهد": "mashhad",
    "همدان": "hamedan",
    "یاسوج": "yasuj",
    "یزد": "yazd",
}


def city_slug(city: str) -> str:
    try:
        return CITY_SLUGS[city]
    except KeyError as exc:
        raise ValueError(f"این منبع هنوز از شهر {city} پشتیبانی نمی‌کند") from exc
