import tempfile
import unittest
import uuid
from pathlib import Path
from urllib.parse import quote
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.modules.models import Day, Meal, MealAttachment, MealIngredient, MealPlan, User, Week
from app.modules.tracking.storage import LocalMediaStorage


def sample_preview_payload() -> dict:
    return {
        "name": "Integration Sample Plan",
        "weeks": [
            {
                "week_index": 1,
                "days": [
                    {
                        "day": "Monday",
                        "meals": [
                            {
                                "meal_type": "breakfast",
                                "title": "Oats",
                                "ingredients": [
                                    {"name": "oats", "quantity": "80", "unit": "g", "category": "grains"},
                                    {"name": "milk", "quantity": "250", "unit": "ml", "category": "dairy"},
                                ],
                            },
                            {
                                "meal_type": "lunch",
                                "title": "Chicken Salad",
                                "ingredients": [
                                    {"name": "chicken breast", "quantity": "1.5", "unit": "kg", "category": "meats"},
                                    {"name": "lettuce", "quantity": "1", "unit": "pcs", "category": "vegetables"},
                                ],
                            },
                        ],
                    },
                    {
                        "day": "Tuesday",
                        "meals": [
                            {
                                "meal_type": "dinner",
                                "title": "Lentil Soup",
                                "ingredients": [
                                    {"name": "lentils", "quantity": "400", "unit": "g", "category": "grains"},
                                    {"name": "onion", "quantity": "1", "unit": "pcs", "category": "vegetables"},
                                ],
                            }
                        ],
                    },
                ],
            }
        ],
    }


class ApiIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tempdir.name) / "integration_test.db"
        cls.media_root = Path(cls.tempdir.name) / "test_uploads"

        cls.engine = create_engine(
            f"sqlite:///{cls.db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        cls.SessionLocal = sessionmaker(bind=cls.engine, autoflush=False, autocommit=False, future=True)
        Base.metadata.create_all(bind=cls.engine)

        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

        from app.modules.tracking import router as tracking_router_module

        tracking_router_module.service.storage = LocalMediaStorage(str(cls.media_root))
        cls.client = TestClient(app)

        with cls.SessionLocal() as db:
            if db.scalar(select(User).where(User.id == 1)) is None:
                db.add(User(id=1, email="integration@dietapp.local"))
                db.commit()

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()
        cls.tempdir.cleanup()

    def commit_sample_plan(self) -> int:
        response = self.client.post("/api/v1/imports/commit", json=sample_preview_payload())
        self.assertEqual(response.status_code, 200)
        return response.json()["meal_plan_id"]

    def test_import_preview_and_commit(self):
        from app.modules.imports import router as imports_router_module

        payload = sample_preview_payload()
        with (
            patch.object(imports_router_module.pdf_extractor, "extract_text", new=AsyncMock(return_value="text")),
            patch.object(imports_router_module.import_service, "parse_pdf_text", new=AsyncMock(return_value=payload)),
        ):
            preview = self.client.post(
                "/api/v1/imports/preview",
                files={"file": ("meal-plan.pdf", b"%PDF-1.4 fake", "application/pdf")},
            )

        self.assertEqual(preview.status_code, 200)
        self.assertEqual(preview.json()["name"], payload["name"])

        commit = self.client.post("/api/v1/imports/commit", json=payload)
        self.assertEqual(commit.status_code, 200)
        self.assertIsInstance(commit.json()["meal_plan_id"], int)

        with self.SessionLocal() as db:
            self.assertIsNotNone(db.scalar(select(MealPlan).where(MealPlan.id == commit.json()["meal_plan_id"])))
            meals_count = len(db.scalars(select(Meal)).all())
            self.assertGreaterEqual(meals_count, 3)

    def test_import_commit_invalid_payload(self):
        response = self.client.post("/api/v1/imports/commit", json={"name": "bad"})
        self.assertEqual(response.status_code, 422)

    def test_tracking_list_status_and_attachment_flow(self):
        self.commit_sample_plan()

        list_response = self.client.get("/api/v1/tracking/meals")
        self.assertEqual(list_response.status_code, 200)
        items = list_response.json()
        self.assertGreaterEqual(len(items), 1)
        self.assertIn("ingredients", items[0])
        self.assertIsInstance(items[0]["ingredients"], list)

        meal_id = items[0]["meal_id"]
        patch_response = self.client.patch(
            f"/api/v1/tracking/meals/{meal_id}",
            json={"status": "eaten", "notes": "integration"},
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.json()["status"], "eaten")

        attach_response = self.client.post(
            f"/api/v1/tracking/meals/{meal_id}/attachments",
            files={"file": ("meal.png", b"not-a-real-png", "image/png")},
            data={"note": "after meal"},
        )
        self.assertEqual(attach_response.status_code, 200)
        self.assertTrue(attach_response.json()["storage_key"].startswith("meal-images/"))

        bad_attach = self.client.post(
            f"/api/v1/tracking/meals/{meal_id}/attachments",
            files={"file": ("note.txt", b"hello", "text/plain")},
        )
        self.assertEqual(bad_attach.status_code, 400)

        with self.SessionLocal() as db:
            attachments = db.scalars(select(MealAttachment)).all()
            self.assertGreaterEqual(len(attachments), 1)

    def test_tracking_is_user_scoped_via_header(self):
        self.commit_sample_plan()

        baseline = self.client.get("/api/v1/tracking/meals").json()
        self.assertGreaterEqual(len(baseline), 1)
        meal_id = baseline[0]["meal_id"]

        user2_patch = self.client.patch(
            f"/api/v1/tracking/meals/{meal_id}",
            headers={"X-User-Id": "2"},
            json={"status": "skipped", "notes": "user2"},
        )
        self.assertEqual(user2_patch.status_code, 200)
        self.assertEqual(user2_patch.json()["user_id"], 2)
        self.assertEqual(user2_patch.json()["status"], "skipped")

        user1_items = self.client.get("/api/v1/tracking/meals", headers={"X-User-Id": "1"}).json()
        user2_items = self.client.get("/api/v1/tracking/meals", headers={"X-User-Id": "2"}).json()

        user1_status = next(item["status"] for item in user1_items if item["meal_id"] == meal_id)
        user2_status = next(item["status"] for item in user2_items if item["meal_id"] == meal_id)
        self.assertNotEqual(user1_status, user2_status)
        self.assertEqual(user1_status, "planned")
        self.assertEqual(user2_status, "skipped")

    def test_shopping_list_endpoint(self):
        meal_plan_id = self.commit_sample_plan()

        response = self.client.get("/api/v1/shopping/list")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertGreaterEqual(len(body["items"]), 1)

        filtered = self.client.get(f"/api/v1/shopping/list?meal_plan_id={meal_plan_id}")
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(filtered.json()["meal_plan_id"], meal_plan_id)
        self.assertTrue(all(item["quantity"] and item["unit"] and item["category"] for item in filtered.json()["items"]))
        self.assertGreaterEqual(len(filtered.json()["items"]), 1)

        missing = self.client.get("/api/v1/shopping/list?meal_plan_id=999999")
        self.assertEqual(missing.status_code, 404)

    def test_shopping_list_sorts_categories(self):
        payload = {
            "name": "Category Sort Plan",
            "weeks": [
                {
                    "week_index": 1,
                    "days": [
                        {
                            "day": "Monday",
                            "meals": [
                                {
                                    "meal_type": "lunch",
                                    "title": "Mix",
                                    "ingredients": [
                                        {"name": "tomato", "quantity": "1", "unit": "pcs", "category": "vegetables"},
                                        {"name": "apple", "quantity": "1", "unit": "pcs", "category": "fruits"},
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        commit = self.client.post("/api/v1/imports/commit", json=payload)
        self.assertEqual(commit.status_code, 200)
        meal_plan_id = commit.json()["meal_plan_id"]
        response = self.client.get(f"/api/v1/shopping/list?meal_plan_id={meal_plan_id}")
        self.assertEqual(response.status_code, 200)
        items = response.json()["items"]
        cats = [item["category"] for item in items]
        self.assertIn("fruits", cats)
        self.assertIn("vegetables", cats)
        self.assertLess(cats.index("fruits"), cats.index("vegetables"))

    def test_shopping_patch_invalid_item_key(self):
        meal_plan_id = self.commit_sample_plan()
        response = self.client.patch(
            "/api/v1/shopping/items/bad-key",
            json={"meal_plan_id": meal_plan_id, "checked": True},
        )
        self.assertEqual(response.status_code, 400)

    def test_import_normalizes_legacy_category_strings(self):
        payload = sample_preview_payload()
        payload["weeks"][0]["days"][0]["meals"][0]["ingredients"][0]["category"] = "protein"
        commit = self.client.post("/api/v1/imports/commit", json=payload)
        self.assertEqual(commit.status_code, 200)
        meal_plan_id = commit.json()["meal_plan_id"]
        with self.SessionLocal() as db:
            ing = db.scalar(
                select(MealIngredient)
                .join(Meal, MealIngredient.meal_id == Meal.id)
                .join(Day, Meal.day_id == Day.id)
                .join(Week, Day.week_id == Week.id)
                .where(Week.meal_plan_id == meal_plan_id)
                .order_by(MealIngredient.id.asc())
                .limit(1)
            )
            self.assertIsNotNone(ing)
            self.assertEqual(ing.category, "meats")

    def test_auth_register_login_cookie_and_me(self):
        email = f"auth_{uuid.uuid4().hex}@example.com"
        reg = self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "longpassword1"},
        )
        self.assertEqual(reg.status_code, 200)
        dup = self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "otherpassword2"},
        )
        self.assertEqual(dup.status_code, 409)

        login = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "longpassword1", "remember_me": True},
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.json()["email"], email)
        self.assertIn("access_token", login.cookies)
        bad = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "wrongpassword"},
        )
        self.assertEqual(bad.status_code, 401)

        me = self.client.get("/api/v1/auth/me")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["email"], email)

        tracked = self.client.get("/api/v1/tracking/meals")
        self.assertEqual(tracked.status_code, 200)

        logout = self.client.post("/api/v1/auth/logout")
        self.assertEqual(logout.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 401)

    def test_shopping_list_is_user_scoped_via_header(self):
        self.commit_sample_plan()

        user1_before = self.client.get("/api/v1/shopping/list", headers={"X-User-Id": "1"})
        user2_before = self.client.get("/api/v1/shopping/list", headers={"X-User-Id": "2"})
        self.assertEqual(user1_before.status_code, 200)
        self.assertEqual(user2_before.status_code, 200)
        self.assertGreaterEqual(len(user1_before.json()["items"]), 1)

        first_item_id = user2_before.json()["items"][0]["id"]
        meal_plan_id = user2_before.json()["meal_plan_id"]
        patch = self.client.patch(
            f"/api/v1/shopping/items/{quote(first_item_id, safe='')}",
            headers={"X-User-Id": "2"},
            json={"meal_plan_id": meal_plan_id, "checked": True},
        )
        self.assertEqual(patch.status_code, 200)

        user1_after = self.client.get("/api/v1/shopping/list", headers={"X-User-Id": "1"}).json()
        user2_after = self.client.get("/api/v1/shopping/list", headers={"X-User-Id": "2"}).json()
        self.assertEqual(len(user1_before.json()["items"]), len(user1_after["items"]))
        user1_item = next(item for item in user1_after["items"] if item["id"] == first_item_id)
        user2_item = next(item for item in user2_after["items"] if item["id"] == first_item_id)
        self.assertFalse(user1_item["checked"])
        self.assertTrue(user2_item["checked"])

    def test_meal_plans_list_and_delete(self):
        meal_plan_id = self.commit_sample_plan()

        listed = self.client.get("/api/v1/meal-plans")
        self.assertEqual(listed.status_code, 200)
        body = listed.json()
        self.assertGreaterEqual(len(body), 1)
        ids = {row["id"] for row in body}
        self.assertIn(meal_plan_id, ids)

        deleted = self.client.delete(f"/api/v1/meal-plans/{meal_plan_id}")
        self.assertEqual(deleted.status_code, 200)
        self.assertTrue(deleted.json().get("ok"))

        after = self.client.get("/api/v1/meal-plans").json()
        self.assertNotIn(meal_plan_id, {row["id"] for row in after})

        missing = self.client.get(f"/api/v1/shopping/list?meal_plan_id={meal_plan_id}")
        self.assertEqual(missing.status_code, 404)

    def test_meal_plan_delete_removes_attachment_files(self):
        self.commit_sample_plan()
        items = self.client.get("/api/v1/tracking/meals").json()
        self.assertGreaterEqual(len(items), 1)
        meal_id = items[0]["meal_id"]
        meal_plan_id = items[0]["meal_plan_id"]
        attach = self.client.post(
            f"/api/v1/tracking/meals/{meal_id}/attachments",
            files={"file": ("meal.png", b"fake-bytes", "image/png")},
        )
        self.assertEqual(attach.status_code, 200)
        storage_key = attach.json()["storage_key"]
        path = self.media_root / storage_key
        self.assertTrue(path.is_file())

        prev_media_root = settings.media_local_root
        settings.media_local_root = str(self.media_root)
        try:
            deleted = self.client.delete(f"/api/v1/meal-plans/{meal_plan_id}")
        finally:
            settings.media_local_root = prev_media_root
        self.assertEqual(deleted.status_code, 200)
        self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
