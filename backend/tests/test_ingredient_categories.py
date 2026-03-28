import unittest

from app.modules.imports.ingredient_categories import normalize_category


class IngredientCategoryTests(unittest.TestCase):
    def test_canonical_passthrough(self) -> None:
        self.assertEqual(normalize_category("meats"), "meats")
        self.assertEqual(normalize_category("Vegetables"), "vegetables")

    def test_legacy_protein_to_meats(self) -> None:
        self.assertEqual(normalize_category("protein"), "meats")

    def test_unknown_to_other(self) -> None:
        self.assertEqual(normalize_category("xyz_unknown"), "other")
        self.assertEqual(normalize_category(None), "other")
        self.assertEqual(normalize_category("   "), "other")


if __name__ == "__main__":
    unittest.main()
