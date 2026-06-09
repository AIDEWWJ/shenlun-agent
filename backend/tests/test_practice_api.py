import os
import unittest
import uuid
from datetime import date
from unittest.mock import patch


os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main as backend_main
import app.modules.email.service as email_service
import app.modules.practice.service as practice_service
from app.core.security import get_password_hash
from app.db.base import Base
from app.modules.auth.models import Role, User, UserRole
from app.modules.email.models import EmailConfig, EmailTemplate
from app.shared.deps import get_db
from app.workflows.review.dto import ReviewAnalysis, ReviewDimension, ReviewLLMConfig, ReviewStep
from app.workflows.review.orchestrator import ReviewResult


class PracticeApiTestCase(unittest.TestCase):
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
            admin_user = User(
                username="admin",
                email="admin@example.com",
                password_hash=get_password_hash("Admin123456"),
                status="active",
            )
            db.add_all(
                [
                    Role(name="visitor", display_name="访客", description="只读浏览用户"),
                    Role(name="learner", display_name="学员", description="核心训练用户"),
                    Role(name="admin", display_name="管理员", description="系统维护用户"),
                    EmailConfig(
                        name="default",
                        smtp_host="smtp.example.com",
                        smtp_port=587,
                        smtp_username="noreply@example.com",
                        smtp_password="password",
                        sender_email="noreply@example.com",
                        sender_name="申论 Agent",
                        use_tls=True,
                        use_ssl=False,
                        enabled=True,
                    ),
                    EmailTemplate(
                        template_key="register_verify",
                        template_name="注册验证码",
                        subject="{app_name} 注册验证码",
                        body_text="您好，{username}。你的注册验证码是：{code}。有效期 {expires_minutes} 分钟。",
                        body_html="<p>您好，{username}。</p><p>你的注册验证码是：<strong>{code}</strong></p><p>有效期 {expires_minutes} 分钟。</p>",
                        enabled=True,
                    ),
                    EmailTemplate(
                        template_key="forgot_password_verify",
                        template_name="找回密码验证码",
                        subject="{app_name} 找回密码验证码",
                        body_text="您好，{username}。你的找回密码验证码是：{code}。有效期 {expires_minutes} 分钟。",
                        body_html="<p>您好，{username}。</p><p>你的找回密码验证码是：<strong>{code}</strong></p><p>有效期 {expires_minutes} 分钟。</p>",
                        enabled=True,
                    ),
                ]
            )
            db.flush()
            db.add(admin_user)
            db.flush()
            admin_role = db.query(Role).filter(Role.name == "admin").first()
            db.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))
            db.commit()

        backend_main.init_database = lambda: None
        email_service._generate_code = lambda: "123456"
        email_service._send_smtp_email = lambda *args, **kwargs: True

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

    def _register_and_login(self, prefix: str = "practice") -> dict:
        suffix = uuid.uuid4().hex[:8]
        username = f"{prefix}_{suffix}"
        email = f"{username}@example.com"

        code_resp = self.client.post(
            "/api/auth/register/send-code",
            json={"username": username, "email": email},
        )
        self.assertEqual(code_resp.status_code, 200)

        register_resp = self.client.post(
            "/api/auth/register",
            json={
                "username": username,
                "password": "test123456",
                "email": email,
                "verification_code": "123456",
            },
        )
        self.assertEqual(register_resp.status_code, 200)

        login_resp = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": "test123456"},
        )
        self.assertEqual(login_resp.status_code, 200)
        token = login_resp.json()["data"]["access_token"]
        return {"username": username, "email": email, "headers": {"Authorization": f"Bearer {token}"}}

    def _create_question(
        self,
        headers: dict,
        *,
        title: str = "基层治理如何提效",
        content: str = "请围绕基层治理提效提出对策。",
        **extra_payload,
    ) -> int:
        payload = {
            "title": title,
            "content": content,
            "question_type": "对策题",
            "tags": ["治理", "基层"],
            "source": "单元测试",
        }
        payload.update(extra_payload)
        resp = self.client.post(
            "/api/questions",
            headers=headers,
            json=payload,
        )
        self.assertEqual(resp.status_code, 201)
        return resp.json()["data"]["id"]

    def _review_from_content(self, headers: dict, *, question_id: int, answer_content: str):
        dummy_llm = ReviewLLMConfig(
            provider="openai",
            model_name="gpt-4.1-mini",
            api_key="sk-test",
            base_url="https://example.com/v1",
            temperature=0.3,
            system_prompt="你是申论批改助手。",
        )
        with patch.object(practice_service.PracticeService, "_build_llm_config", return_value=dummy_llm), patch.object(
            practice_service.ReviewService,
            "review",
            return_value=self._fake_review_result(answer_content),
        ):
            return self.client.post(
                "/api/review/from-content",
                headers=headers,
                json={
                    "question_id": question_id,
                    "answer_content": answer_content,
                    "reference_points": ["协同机制", "监督反馈"],
                    "use_llm": True,
                },
            )

    def _fake_review_result(self, answer_content: str) -> ReviewResult:
        analysis = ReviewAnalysis(
            score=86,
            dimensions=[ReviewDimension(name="审题与回应", score=22, comment="回应较完整", suggestions=[])],
            strengths=["命中关键方向"],
            issues=["论证还可展开"],
            suggestions=["补充执行层举措"],
            summary="整体方向正确，细节仍可加强。",
            analysis_explanation="已完成审题。",
            outline_explanation="建议按问题、原因、对策展开。",
            keyword_hits=["基层治理", "协同机制"],
            keyword_misses=["监督反馈"],
            answer_length=len(answer_content),
            question_type="对策题",
            question_analysis={"question_type": "对策题", "note": "完成审题"},
            reference_point_analysis=[{"text": "完善协同机制"}],
            user_point_analysis=[{"text": "强化协同机制"}],
            comparison_analysis={"matched_points": ["协同机制"], "missing_points": ["监督反馈"]},
            structure_analysis={"score": 18, "issues": [], "suggestions": ["分层展开"]},
            language_analysis={"score": 17, "issues": [], "suggestions": ["减少重复表述"]},
            rule_analysis={"penalty": 0, "violations": [], "warnings": []},
            score_breakdown={"question_score": 22, "content_score": 20, "structure_score": 18, "language_score": 17, "rule_score": 9, "total_score": 86},
            review_steps=[{"step_key": "question_analysis"}],
            report_json={"outline": "问题-原因-对策"},
        )
        steps = [
            ReviewStep(
                step_key="question_analysis",
                step_name="题目解析",
                order_no=1,
                output_data={"question_type": "对策题"},
            )
        ]
        return ReviewResult(analysis=analysis, steps=steps, persist_payload={})

    def test_answer_draft_crud_and_versioning(self):
        session = self._register_and_login("answer")
        headers = session["headers"]
        question_id = self._create_question(headers)

        create_resp = self.client.post(
            "/api/answers",
            headers=headers,
            json={"question_id": question_id, "content": "第一版答案草稿。"},
        )
        self.assertEqual(create_resp.status_code, 201)
        create_data = create_resp.json()["data"]
        self.assertEqual(create_data["version_no"], 1)
        self.assertFalse(create_data["reviewed"])
        answer_id = create_data["id"]

        list_resp = self.client.get(f"/api/questions/{question_id}/answers", headers=headers)
        self.assertEqual(list_resp.status_code, 200)
        list_data = list_resp.json()["data"]
        self.assertEqual(list_data["total"], 1)
        self.assertEqual(list_data["items"][0]["id"], answer_id)

        get_resp = self.client.get(f"/api/answers/{answer_id}", headers=headers)
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()["data"]["content"], "第一版答案草稿。")

        update_resp = self.client.put(
            f"/api/answers/{answer_id}",
            headers=headers,
            json={"content": "第一版答案草稿，已补充对策细节。"},
        )
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(update_resp.json()["data"]["content"], "第一版答案草稿，已补充对策细节。")

        second_resp = self.client.post(
            "/api/answers",
            headers=headers,
            json={"question_id": question_id, "content": "第二版答案草稿。"},
        )
        self.assertEqual(second_resp.status_code, 201)
        self.assertEqual(second_resp.json()["data"]["version_no"], 2)

        filters_resp = self.client.get("/api/questions/filters", headers=headers)
        self.assertEqual(filters_resp.status_code, 200)
        filters_data = filters_resp.json()["data"]
        self.assertIn("对策题", filters_data["question_types"])
        self.assertIn("治理", filters_data["tags"])
        self.assertIn("单元测试", filters_data["sources"])

    def test_workspace_and_practice_session_flow(self):
        session = self._register_and_login("workspace")
        headers = session["headers"]
        question_id = self._create_question(
            headers,
            title="基层治理中的协同堵点",
            content="请根据材料概括堵点并提出优化方向。",
            category="真题",
            year=2024,
            region="全国",
            difficulty="进阶",
            theme="基层治理",
            suggested_minutes=45,
            cover_note="训练概括与对策",
            intro="聚焦基层协同堵点",
            overview="适合训练结构化作答",
            tasks=["概括堵点", "提出优化方向"],
            instructions=["先概括问题，再提措施"],
            notices=["建议先列提纲再作答"],
            materials=[
                {
                    "id": "m1",
                    "title": "材料一",
                    "summary": "存在信息断点",
                    "content": "社区治理中存在信息重复采集问题。",
                }
            ],
            answer_sections=[
                {
                    "id": "a1",
                    "title": "问题概括",
                    "prompt": "请概括主要堵点",
                    "word_limit_label": "建议 250-350 字",
                    "min_words": 200,
                    "placeholder": "先概括问题类型",
                },
                {
                    "id": "a2",
                    "title": "优化方向",
                    "prompt": "请提出优化方向",
                    "word_limit_label": "建议 250-350 字",
                    "min_words": 200,
                    "placeholder": "围绕流程、协同、反馈展开",
                },
            ],
            reference_answer="应围绕信息共享、流程协同和反馈闭环作答。",
            optimized_example="可以按问题、原因、对策三层展开。",
        )

        workspace_resp = self.client.get(f"/api/questions/{question_id}/workspace", headers=headers)
        self.assertEqual(workspace_resp.status_code, 200)
        workspace_data = workspace_resp.json()["data"]
        self.assertEqual(workspace_data["question"]["suggested_minutes"], 45)
        self.assertEqual(len(workspace_data["materials"]), 1)
        self.assertEqual(len(workspace_data["answer_sections"]), 2)
        self.assertIsNone(workspace_data["latest_draft"])
        self.assertIsNone(workspace_data["latest_review"])

        create_session_resp = self.client.post(
            "/api/practice-sessions",
            headers=headers,
            json={"question_id": question_id},
        )
        self.assertEqual(create_session_resp.status_code, 201)
        session_data = create_session_resp.json()["data"]
        session_id = session_data["id"]
        self.assertEqual(session_data["status"], "drafting")
        self.assertEqual(session_data["answers"], {"a1": "", "a2": ""})

        update_session_resp = self.client.patch(
            f"/api/practice-sessions/{session_id}",
            headers=headers,
            json={
                "answers": {
                    "a1": "主要堵点在于信息重复采集、平台不互通。",
                    "a2": "应统一入口、强化协同、完善反馈闭环。",
                },
                "elapsed_seconds": 900,
            },
        )
        self.assertEqual(update_session_resp.status_code, 200)
        updated_session = update_session_resp.json()["data"]
        self.assertEqual(updated_session["elapsed_seconds"], 900)
        self.assertIn("平台不互通", updated_session["answers"]["a1"])

        current_session_resp = self.client.get(
            f"/api/practice-sessions/current?question_id={question_id}",
            headers=headers,
        )
        self.assertEqual(current_session_resp.status_code, 200)
        current_session = current_session_resp.json()["data"]
        self.assertEqual(current_session["id"], session_id)

        workspace_with_draft_resp = self.client.get(f"/api/questions/{question_id}/workspace", headers=headers)
        self.assertEqual(workspace_with_draft_resp.status_code, 200)
        workspace_with_draft = workspace_with_draft_resp.json()["data"]
        self.assertEqual(workspace_with_draft["latest_draft"]["session_id"], session_id)
        self.assertIn("统一入口", workspace_with_draft["latest_draft"]["answers"]["a2"])

        dummy_llm = ReviewLLMConfig(
            provider="openai",
            model_name="gpt-4.1-mini",
            api_key="sk-test",
            base_url="https://example.com/v1",
            temperature=0.3,
            system_prompt="你是申论批改助手。",
        )
        with patch.object(practice_service.PracticeService, "_build_llm_config", return_value=dummy_llm), patch.object(
            practice_service.ReviewService,
            "review",
            return_value=self._fake_review_result("会话提交流程生成的答案内容。"),
        ):
            submit_resp = self.client.post(
                f"/api/practice-sessions/{session_id}/submit",
                headers=headers,
                json={"use_llm": True, "reference_points": ["信息共享", "反馈闭环"]},
            )
        self.assertEqual(submit_resp.status_code, 200)
        submit_data = submit_resp.json()["data"]
        self.assertEqual(submit_data["session_id"], session_id)
        self.assertEqual(submit_data["status"], "completed")
        self.assertIsNotNone(submit_data["review_id"])

        current_after_submit_resp = self.client.get(
            f"/api/practice-sessions/current?question_id={question_id}",
            headers=headers,
        )
        self.assertEqual(current_after_submit_resp.status_code, 200)
        self.assertIsNone(current_after_submit_resp.json()["data"])

        workspace_after_submit_resp = self.client.get(f"/api/questions/{question_id}/workspace", headers=headers)
        self.assertEqual(workspace_after_submit_resp.status_code, 200)
        workspace_after_submit = workspace_after_submit_resp.json()["data"]
        self.assertIsNone(workspace_after_submit["latest_draft"])
        self.assertEqual(workspace_after_submit["latest_review"]["review_id"], submit_data["review_id"])

    def test_review_from_content_creates_review_and_practice_record(self):
        session = self._register_and_login("review")
        headers = session["headers"]
        question_id = self._create_question(headers)
        review_resp = self._review_from_content(
            headers,
            question_id=question_id,
            answer_content="围绕基层治理提出协同与反馈机制。",
        )

        self.assertEqual(review_resp.status_code, 200)
        review_data = review_resp.json()["data"]
        answer_id = review_data["answer_id"]
        review_id = review_data["review_id"]
        self.assertEqual(review_data["analysis"]["score"], 86)

        records_resp = self.client.get("/api/practice-records", headers=headers)
        self.assertEqual(records_resp.status_code, 200)
        records_data = records_resp.json()["data"]
        self.assertEqual(records_data["total"], 1)
        record_id = records_data["items"][0]["id"]
        self.assertEqual(records_data["items"][0]["answer_id"], answer_id)
        self.assertEqual(records_data["items"][0]["review_id"], review_id)

        record_detail_resp = self.client.get(f"/api/practice-records/{record_id}", headers=headers)
        self.assertEqual(record_detail_resp.status_code, 200)
        self.assertEqual(record_detail_resp.json()["data"]["answer_content"], "围绕基层治理提出协同与反馈机制。")

        report_resp = self.client.get(f"/api/reviews/{review_id}", headers=headers)
        self.assertEqual(report_resp.status_code, 200)
        report_data = report_resp.json()["data"]
        self.assertEqual(report_data["score"], 86)
        self.assertEqual(report_data["reference_point_analysis"][0]["text"], "完善协同机制")
        self.assertEqual(report_data["steps"][0]["step_key"], "question_analysis")

        review_list_resp = self.client.get("/api/reviews?page=1&page_size=10", headers=headers)
        self.assertEqual(review_list_resp.status_code, 200)
        review_list_data = review_list_resp.json()["data"]
        self.assertEqual(review_list_data["total"], 1)
        self.assertEqual(review_list_data["page"], 1)
        self.assertEqual(review_list_data["page_size"], 10)
        self.assertEqual(len(review_list_data["items"]), 1)
        self.assertEqual(review_list_data["items"][0]["id"], review_id)

        favorite_resp = self.client.patch(
            f"/api/practice-records/{record_id}/favorite",
            headers=headers,
            json={"is_favorite": True},
        )
        self.assertEqual(favorite_resp.status_code, 200)
        self.assertTrue(favorite_resp.json()["data"]["is_favorite"])

        favorite_list_resp = self.client.get("/api/practice-records?is_favorite=true", headers=headers)
        self.assertEqual(favorite_list_resp.status_code, 200)
        favorite_list_data = favorite_list_resp.json()["data"]
        self.assertEqual(favorite_list_data["total"], 1)
        self.assertEqual(favorite_list_data["items"][0]["id"], record_id)

        review_filter_resp = self.client.get(f"/api/practice-records?review_id={review_id}", headers=headers)
        self.assertEqual(review_filter_resp.status_code, 200)
        review_filter_data = review_filter_resp.json()["data"]
        self.assertEqual(review_filter_data["total"], 1)
        self.assertEqual(review_filter_data["items"][0]["review_id"], review_id)

        score_filter_resp = self.client.get("/api/practice-records?score_min=80&score_max=90", headers=headers)
        self.assertEqual(score_filter_resp.status_code, 200)
        score_filter_data = score_filter_resp.json()["data"]
        self.assertEqual(score_filter_data["total"], 1)
        self.assertEqual(score_filter_data["items"][0]["id"], record_id)

        model_filter_resp = self.client.get("/api/practice-records?model_provider=openai&model_name=gpt-4.1-mini", headers=headers)
        self.assertEqual(model_filter_resp.status_code, 200)
        model_filter_data = model_filter_resp.json()["data"]
        self.assertEqual(model_filter_data["total"], 1)
        self.assertEqual(model_filter_data["items"][0]["id"], record_id)

        version_filter_resp = self.client.get("/api/practice-records?answer_version_no=1", headers=headers)
        self.assertEqual(version_filter_resp.status_code, 200)
        version_filter_data = version_filter_resp.json()["data"]
        self.assertEqual(version_filter_data["total"], 1)
        self.assertEqual(version_filter_data["items"][0]["answer_version_no"], 1)

        type_filter_resp = self.client.get("/api/practice-records?question_type=对策题", headers=headers)
        self.assertEqual(type_filter_resp.status_code, 200)
        type_filter_data = type_filter_resp.json()["data"]
        self.assertEqual(type_filter_data["total"], 1)
        self.assertEqual(type_filter_data["items"][0]["id"], record_id)

        date_filter_resp = self.client.get(
            f"/api/practice-records?date_from={date.today().isoformat()}&date_to={date.today().isoformat()}",
            headers=headers,
        )
        self.assertEqual(date_filter_resp.status_code, 200)
        date_filter_data = date_filter_resp.json()["data"]
        self.assertEqual(date_filter_data["total"], 1)
        self.assertEqual(date_filter_data["items"][0]["id"], record_id)

    def test_reviewed_answer_is_locked_and_re_review_creates_new_version(self):
        session = self._register_and_login("version")
        headers = session["headers"]
        question_id = self._create_question(headers)
        draft_resp = self.client.post(
            "/api/answers",
            headers=headers,
            json={"question_id": question_id, "content": "初始草稿。"},
        )
        self.assertEqual(draft_resp.status_code, 201)
        answer_id = draft_resp.json()["data"]["id"]

        dummy_llm = ReviewLLMConfig(
            provider="openai",
            model_name="gpt-4.1-mini",
            api_key="sk-test",
            base_url="https://example.com/v1",
            temperature=0.3,
            system_prompt="你是申论批改助手。",
        )

        with patch.object(practice_service.PracticeService, "_build_llm_config", return_value=dummy_llm), patch.object(
            practice_service.ReviewService,
            "review",
            return_value=self._fake_review_result("已提交批改的第一版。"),
        ):
            review_resp = self.client.post(
                "/api/review/from-content",
                headers=headers,
                json={
                    "question_id": question_id,
                    "answer_id": answer_id,
                    "answer_content": "已提交批改的第一版。",
                    "use_llm": True,
                },
            )
        self.assertEqual(review_resp.status_code, 200)
        self.assertEqual(review_resp.json()["data"]["answer_id"], answer_id)

        locked_resp = self.client.put(
            f"/api/answers/{answer_id}",
            headers=headers,
            json={"content": "试图直接修改已批改答案。"},
        )
        self.assertEqual(locked_resp.status_code, 400)
        self.assertEqual(locked_resp.json()["message"], "该答案已批改，不能直接修改，请创建新版本")

        with patch.object(practice_service.PracticeService, "_build_llm_config", return_value=dummy_llm), patch.object(
            practice_service.ReviewService,
            "review",
            return_value=self._fake_review_result("第二版重新作答内容。"),
        ):
            second_review_resp = self.client.post(
                "/api/review/from-content",
                headers=headers,
                json={
                    "question_id": question_id,
                    "answer_id": answer_id,
                    "answer_content": "第二版重新作答内容。",
                    "use_llm": True,
                },
            )
        self.assertEqual(second_review_resp.status_code, 200)
        second_answer_id = second_review_resp.json()["data"]["answer_id"]
        self.assertNotEqual(second_answer_id, answer_id)

        answers_resp = self.client.get(f"/api/questions/{question_id}/answers", headers=headers)
        self.assertEqual(answers_resp.status_code, 200)
        answers_data = answers_resp.json()["data"]["items"]
        self.assertEqual(len(answers_data), 2)
        self.assertEqual(answers_data[0]["version_no"], 2)
        self.assertTrue(answers_data[0]["reviewed"])

    def test_review_list_can_filter_by_question(self):
        session = self._register_and_login("review_filter")
        headers = session["headers"]
        question_id_a = self._create_question(headers, title="题目A", content="内容A")
        question_id_b = self._create_question(headers, title="题目B", content="内容B")

        resp_a = self._review_from_content(headers, question_id=question_id_a, answer_content="题目A的作答。")
        self.assertEqual(resp_a.status_code, 200)
        review_id_a = resp_a.json()["data"]["review_id"]

        resp_b = self._review_from_content(headers, question_id=question_id_b, answer_content="题目B的作答。")
        self.assertEqual(resp_b.status_code, 200)

        filtered = self.client.get(f"/api/reviews?page=1&page_size=10&question_id={question_id_a}", headers=headers)
        self.assertEqual(filtered.status_code, 200)
        data = filtered.json()["data"]
        self.assertEqual(data["total"], 1)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["id"], review_id_a)
        self.assertEqual(data["items"][0]["question_id"], question_id_a)

        type_filtered = self.client.get("/api/reviews?page=1&page_size=10&question_type=对策题", headers=headers)
        self.assertEqual(type_filtered.status_code, 200)
        type_data = type_filtered.json()["data"]
        self.assertEqual(type_data["total"], 2)

        qa_resp = self.client.post(
            f"/api/reviews/{review_id_a}/qa",
            headers=headers,
            json={"question": "为什么这次会扣分？", "use_llm": False},
        )
        self.assertEqual(qa_resp.status_code, 200)
        qa_data = qa_resp.json()["data"]
        self.assertEqual(qa_data["review_id"], review_id_a)
        self.assertEqual(qa_data["question_category"], "score_explanation")
        self.assertIn("总分", qa_data["answer_text"])
        self.assertIn("score_breakdown", qa_data["evidence_refs"])
        self.assertIsNotNone(qa_data["conversation_id"])
        self.assertEqual(qa_data["round_no"], 1)

        followup_resp = self.client.post(
            f"/api/reviews/{review_id_a}/qa",
            headers=headers,
            json={
                "question": "那我下一版应该优先改什么？",
                "use_llm": False,
                "conversation_id": qa_data["conversation_id"],
                "parent_message_id": qa_data["id"],
            },
        )
        self.assertEqual(followup_resp.status_code, 200)
        followup_data = followup_resp.json()["data"]
        self.assertEqual(followup_data["conversation_id"], qa_data["conversation_id"])
        self.assertEqual(followup_data["parent_message_id"], qa_data["id"])
        self.assertEqual(followup_data["round_no"], 2)

        qa_list_resp = self.client.get(
            f"/api/reviews/{review_id_a}/qa?page=1&page_size=10&conversation_id={qa_data['conversation_id']}",
            headers=headers,
        )
        self.assertEqual(qa_list_resp.status_code, 200)
        qa_list_data = qa_list_resp.json()["data"]
        self.assertEqual(qa_list_data["total"], 2)
        self.assertEqual(len(qa_list_data["items"]), 2)
        self.assertEqual(qa_list_data["items"][0]["review_id"], review_id_a)
        self.assertEqual(qa_list_data["items"][0]["question_text"], "为什么这次会扣分？")
        self.assertEqual(qa_list_data["items"][0]["question_category"], "score_explanation")
        self.assertEqual(qa_list_data["items"][1]["question_text"], "那我下一版应该优先改什么？")
        self.assertEqual(qa_list_data["items"][1]["round_no"], 2)


if __name__ == "__main__":
    unittest.main()
