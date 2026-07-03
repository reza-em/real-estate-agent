PROPERTY = "property"
CAR = "car"
MOTORCYCLE = "motorcycle"

CATEGORIES = (PROPERTY, CAR, MOTORCYCLE)
CATEGORY_LABELS = {
    PROPERTY: "ملک",
    CAR: "خودرو",
    MOTORCYCLE: "موتورسیکلت",
}


def category_label(category: str) -> str:
    return CATEGORY_LABELS.get(category, category)
