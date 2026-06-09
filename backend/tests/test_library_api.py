import os
import unittest


os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main as backend_main
from app.core.security import get_password_hash
from app.db.base import Base
from app.modules.auth.models import Role, User, UserRole
from app.modules.paper.models import Paper
from app.modules.practice.models import PaperPracticeSession
from app.modules.question.models import Question
from app.shared.deps import get_db


class LibraryApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

        @event.listens_for(cls.engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(bind=cls.engine)

        with cls.SessionLocal() as db:
            learner_role = Role(name="learner", display_name="学员", description="核心训练用户")
            admin_role = Role(name="admin", display_name="管理员", description="系统维护用户")
            learner = User(
                username="library_learner",
                email="library_learner@example.com",
                password_hash=get_password_hash("test123456"),
                status="active",
            )
            other = User(
                username="library_other",
                email="library_other@example.com",
                password_hash=get_password_hash("test123456"),
                status="active",
            )
            admin = User(
                username="library_admin",
                email="library_admin@example.com",
                password_hash=get_password_hash("test123456"),
                status="active",
            )
            db.add_all([learner_role, admin_role, learner, other, admin])
            db.flush()
            db.add_all([
                UserRole(user_id=learner.id, role_id=learner_role.id),
                UserRole(user_id=other.id, role_id=learner_role.id),
                UserRole(user_id=admin.id, role_id=admin_role.id),
            ])
            db.commit()

        backend_main.init_database = lambda: None
        cls.client = TestClient(backend_main.app)

        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        backend_main.app.dependency_overrides[get_db] = override_get_db

    @classmethod
    def tearDownClass(cls):
        backend_main.app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()

    def setUp(self):
        with self.SessionLocal() as db:
            db.query(PaperPracticeSession).delete()
            db.query(Question).delete()
            db.query(Paper).delete()
            db.commit()

    def _headers(self, username: str = "library_learner") -> dict:
        response = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": "test123456"},
        )
        self.assertEqual(response.status_code, 200)
        token = response.json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def _seed_library_items(self):
        with self.SessionLocal() as db:
            learner = db.query(User).filter(User.username == "library_learner").one()
            other = db.query(User).filter(User.username == "library_other").one()

            paper = Paper(
                user_id=learner.id,
                scope="system",
                title="2024 国考副省申论卷",
                category="真题",
                region="全国",
                difficulty="中等",
                year=2024,
                question_count=2,
            )
            user_paper = Paper(
                user_id=learner.id,
                scope="user",
                title="我的专项套卷",
                category="专项训练",
                region="华东",
                difficulty="进阶",
                year=2025,
                question_count=1,
            )
            db.add_all([paper, user_paper])
            db.flush()

            independent_question = Question(
                user_id=learner.id,
                scope="system",
                paper_id=None,
                title="基层治理独立单题",
                content="请概括基层治理中的主要问题。",
                question_type="概括题",
                tags="基层治理,概括归纳",
                source="专项训练",
                region="全国",
                difficulty="进阶",
                year=2025,
                suggested_minutes=45,
            )
            paper_child_question = Question(
                user_id=learner.id,
                scope="system",
                paper_id=paper.id,
                title="套卷内小题不应单独出现",
                content="请作答套卷内小题。",
                question_type="对策题",
                region="全国",
                difficulty="中等",
                year=2024,
            )
            other_private_question = Question(
                user_id=other.id,
                scope="user",
                paper_id=None,
                title="他人个人题目不可见",
                content="这道题不应被普通用户看到。",
                question_type="作文题",
            )
            db.add_all([independent_question, paper_child_question, other_private_question])
            db.add(
                PaperPracticeSession(
                    user_id=learner.id,
                    paper_id=paper.id,
                    answers_json='{"1":"已有草稿"}',
                    current_index=0,
                    timer_seconds=120,
                    status="drafting",
                )
            )
            db.commit()

    def test_library_items_mix_papers_and_independent_questions(self):
        self._seed_library_items()
        response = self.client.get("/api/library/items?page_size=20&sort_by=title&sort_order=asc", headers=self._headers())
        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]
        item_keys = {item["item_key"] for item in data["items"]}
        titles = {item["title"] for item in data["items"]}

        self.assertEqual(data["total"], 3)
        self.assertIn("2024 国考副省申论卷", titles)
        self.assertIn("我的专项套卷", titles)
        self.assertIn("基层治理独立单题", titles)
        self.assertNotIn("套卷内小题不应单独出现", titles)
        self.assertFalse(any(key.startswith("question:") and "套卷内" in key for key in item_keys))

        paper_item = next(item for item in data["items"] if item["title"] == "2024 国考副省申论卷")
        question_item = next(item for item in data["items"] if item["title"] == "基层治理独立单题")
        self.assertEqual(paper_item["item_type"], "paper")
        self.assertTrue(paper_item["has_draft"])
        self.assertEqual(paper_item["primary_action"]["path"], f"/practice/paper/{paper_item['resource_id']}?resume=1")
        self.assertEqual(question_item["item_type"], "question")
        self.assertEqual(question_item["primary_action"]["path"], f"/practice/{question_item['resource_id']}")

    def test_library_items_can_filter_by_type_and_scope(self):
        self._seed_library_items()

        question_response = self.client.get("/api/library/items?item_type=question&page_size=20", headers=self._headers())
        self.assertEqual(question_response.status_code, 200)
        question_items = question_response.json()["data"]["items"]
        self.assertEqual(len(question_items), 1)
        self.assertEqual(question_items[0]["item_type"], "question")
        self.assertEqual(question_items[0]["title"], "基层治理独立单题")

        user_scope_response = self.client.get("/api/library/items?scope=user&page_size=20", headers=self._headers())
        self.assertEqual(user_scope_response.status_code, 200)
        user_scope_titles = {item["title"] for item in user_scope_response.json()["data"]["items"]}
        self.assertEqual(user_scope_titles, {"我的专项套卷"})

    def test_admin_user_scope_only_returns_own_user_library(self):
        self._seed_library_items()
        response = self.client.get("/api/library/items?scope=user&page_size=20", headers=self._headers("library_admin"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["items"], [])

    def test_library_filters_merge_papers_and_independent_questions(self):
        self._seed_library_items()
        response = self.client.get("/api/library/filters", headers=self._headers())
        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]
        self.assertIn("paper", data["item_types"])
        self.assertIn("question", data["item_types"])
        self.assertIn("全国", data["regions"])
        self.assertIn("华东", data["regions"])
        self.assertIn(2024, data["years"])
        self.assertIn(2025, data["years"])
        self.assertIn("概括题", data["question_types"])


if __name__ == "__main__":
    unittest.main()
