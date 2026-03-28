"""Canonical shopping/ingredient categories and normalization for persistence."""

CANONICAL_CATEGORIES = frozenset(
    {
        "meats",
        "dairy",
        "bread",
        "grains",
        "fruits",
        "vegetables",
        "fats",
        "spices",
        "nuts",
        "other",
    }
)

# Map common model synonyms and legacy values to canonical slugs.
_CATEGORY_ALIASES: dict[str, str] = {
    "protein": "meats",
    "poultry": "meats",
    "meat": "meats",
    "seafood": "meats",
    "fish": "meats",
    "egg": "meats",
    "eggs": "meats",
    "legumes": "grains",
    "beans": "grains",
    "pasta": "grains",
    "rice": "grains",
    "herbs": "spices",
    "condiments": "spices",
    "beverages": "other",
    "drinks": "other",
    "frozen": "other",
    "canned": "other",
    "pantry": "other",
}


def normalize_category(raw: str | None) -> str:
    """Return a canonical category slug; unknown values become ``other``."""
    if raw is None:
        return "other"
    key = raw.strip().lower()
    if not key:
        return "other"
    if key in CANONICAL_CATEGORIES:
        return key
    if key in _CATEGORY_ALIASES:
        return _CATEGORY_ALIASES[key]
    return "other"
