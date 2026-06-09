import os
import unittest
import uuid
from unittest.mock import patch


os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main as backend_main
from app.shared.deps import get_db
from app.core.security import get_password_hash
from app.db.base import Base
from app.modules.auth.models import Role, User, UserRole
from app.modules.email.models import EmailConfig, EmailTemplate, EmailVerificationCode
import app.modules.email.service as email_service
import app.modules.question.service as question_service


class AuthApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """初始化测试数据库和测试客户端。"""

        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

        # 让 SQLite 在测试中也尽量表现得接近线上行为。
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

        # 避免测试时触发 MySQL 初始化。
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

    def _request_register_code(self, username: str, email: str):
        return self.client.post(
            "/api/auth/register/send-code",
            json={"username": username, "email": email},
        )

    def _register_verified_user(self, username: str, password: str, email: str):
        code_resp = self._request_register_code(username, email)
        self.assertEqual(code_resp.status_code, 200)
        register_resp = self._confirm_register(username, password, email)
        self.assertEqual(register_resp.status_code, 200)
        return register_resp

    def _confirm_register(self, username: str, password: str, email: str):
        return self.client.post(
            "/api/auth/register",
            json={
                "username": username,
                "password": password,
                "email": email,
                "verification_code": "123456",
            },
        )

    def _request_forgot_code(self, username: str, email: str):
        return self.client.post(
            "/api/auth/forgot-password/send-code",
            json={"username": username, "email": email},
        )

    def _forgot_password_verified(self, username: str, email: str, new_password: str):
        code_resp = self._request_forgot_code(username, email)
        self.assertEqual(code_resp.status_code, 200)
        reset_resp = self._confirm_forgot_password(username, email, new_password)
        self.assertEqual(reset_resp.status_code, 200)
        return reset_resp

    def _confirm_forgot_password(self, username: str, email: str, new_password: str):
        return self.client.post(
            "/api/auth/forgot-password",
            json={
                "username": username,
                "email": email,
                "new_password": new_password,
                "verification_code": "123456",
            },
        )

    def test_register_login_me_chain(self):
        """注册、登录、获取当前用户接口链路测试。"""

        register_resp = self._register_verified_user("testuser", "test123456", "testuser@example.com")
        register_data = register_resp.json()
        self.assertTrue(register_data["success"])
        self.assertEqual(register_data["message"], "注册成功")
        self.assertIn("access_token", register_data["data"])

        duplicate_resp = self._request_register_code("testuser", "another@example.com")
        self.assertEqual(duplicate_resp.status_code, 400)
        duplicate_data = duplicate_resp.json()
        self.assertFalse(duplicate_data["success"])
        self.assertEqual(duplicate_data["message"], "用户名已存在")

        login_resp = self.client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "test123456",
            },
        )
        self.assertEqual(login_resp.status_code, 200)
        login_data = login_resp.json()
        self.assertTrue(login_data["success"])
        self.assertEqual(login_data["message"], "登录成功")
        self.assertIn("access_token", login_data["data"])
        self.assertEqual(login_data["data"]["token_type"], "bearer")

        token = login_data["data"]["access_token"]
        me_resp = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(me_resp.status_code, 200)
        me_data = me_resp.json()
        self.assertTrue(me_data["success"])
        self.assertEqual(me_data["data"]["username"], "testuser")
        self.assertEqual(me_data["data"]["email"], "testuser@example.com")
        self.assertIn("learner", me_data["data"]["roles"])

    def test_login_failure(self):
        """错误密码登录时应返回 401。"""

        self._register_verified_user("wronguser", "test123456", "wronguser@example.com")

        login_resp = self.client.post(
            "/api/auth/login",
            json={
                "username": "wronguser",
                "password": "bad-password",
            },
        )
        self.assertEqual(login_resp.status_code, 401)
        login_data = login_resp.json()
        self.assertFalse(login_data["success"])
        self.assertEqual(login_data["message"], "用户名或密码错误")

    def test_register_and_profile_conflicts(self):
        """重复用户名/邮箱以及资料冲突边界测试。"""

        first = self._register_verified_user("conflict_a", "test123456", "conflict_a@example.com")
        self.assertEqual(first.status_code, 200)

        self._register_verified_user("conflict_b", "test123456", "conflict_b@example.com")
        login_resp = self.client.post(
            "/api/auth/login",
            json={"username": "conflict_b", "password": "test123456"},
        )
        access_token = login_resp.json()["data"]["access_token"]

        duplicate_username = self._request_register_code("conflict_a", "conflict_c@example.com")
        self.assertEqual(duplicate_username.status_code, 400)
        self.assertEqual(duplicate_username.json()["message"], "用户名已存在")

        duplicate_email = self._request_register_code("conflict_c", "conflict_a@example.com")
        self.assertEqual(duplicate_email.status_code, 400)
        self.assertEqual(duplicate_email.json()["message"], "邮箱已存在")

        update_conflict = self.client.put(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"username": "conflict_a"},
        )
        self.assertEqual(update_conflict.status_code, 400)
        self.assertEqual(update_conflict.json()["message"], "用户名已存在")

        bad_password_change = self.client.post(
            "/api/auth/me/password",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"current_password": "wrong-pass", "new_password": "newpass123"},
        )
        self.assertEqual(bad_password_change.status_code, 400)
        self.assertEqual(bad_password_change.json()["message"], "当前密码错误")

    def test_update_profile_change_password(self):
        """个人资料和密码修改链路测试。"""

        suffix = uuid.uuid4().hex[:8]
        username = f"profile_{suffix}"
        email = f"{username}@example.com"

        self._register_verified_user(username, "test123456", email)

        login_resp = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": "test123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        updated_username = f"profile_new_{suffix}"
        updated_email = f"{updated_username}@example.com"
        update_resp = self.client.put(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"username": updated_username, "email": updated_email},
        )
        self.assertEqual(update_resp.status_code, 200)
        update_data = update_resp.json()
        self.assertTrue(update_data["success"])
        self.assertEqual(update_data["data"]["username"], updated_username)
        self.assertEqual(update_data["data"]["email"], updated_email)

        password_resp = self.client.post(
            "/api/auth/me/password",
            headers={"Authorization": f"Bearer {token}"},
            json={"current_password": "test123456", "new_password": "newpass123"},
        )
        self.assertEqual(password_resp.status_code, 200)
        password_data = password_resp.json()
        self.assertTrue(password_data["success"])
        self.assertEqual(password_data["message"], "密码修改成功")

        old_login_resp = self.client.post(
            "/api/auth/login",
            json={"username": updated_username, "password": "test123456"},
        )
        self.assertEqual(old_login_resp.status_code, 401)

        new_login_resp = self.client.post(
            "/api/auth/login",
            json={"username": updated_username, "password": "newpass123"},
        )
        self.assertEqual(new_login_resp.status_code, 200)
        self.assertTrue(new_login_resp.json()["success"])

    def test_forgot_password_reset_chain(self):
        """忘记密码重置链路测试。"""

        suffix = uuid.uuid4().hex[:8]
        username = f"forgot_{suffix}"
        email = f"{username}@example.com"

        self._register_verified_user(username, "test123456", email)

        bad_reset = self._request_forgot_code(username, "wrong@example.com")
        self.assertEqual(bad_reset.status_code, 400)
        self.assertEqual(bad_reset.json()["message"], "用户名或邮箱不正确")

        reset_resp = self._forgot_password_verified(username, email, "newpass123")
        self.assertTrue(reset_resp.json()["success"])
        self.assertEqual(reset_resp.json()["message"], "密码重置成功")

        old_login_resp = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": "test123456"},
        )
        self.assertEqual(old_login_resp.status_code, 401)

        new_login_resp = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": "newpass123"},
        )
        self.assertEqual(new_login_resp.status_code, 200)
        self.assertTrue(new_login_resp.json()["success"])

    def test_admin_permission_boundaries(self):
        """管理员接口权限和参数边界测试。"""

        self._register_verified_user("boundary_user", "test123456", "boundary_user@example.com")
        login_resp = self.client.post(
            "/api/auth/login",
            json={"username": "boundary_user", "password": "test123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        admin_list = self.client.get("/api/admin/users", headers=headers)
        self.assertEqual(admin_list.status_code, 403)
        self.assertEqual(admin_list.json()["message"], "仅管理员可访问")

        admin_config_list = self.client.get("/api/admin/ai-configs/system", headers=headers)
        self.assertEqual(admin_config_list.status_code, 403)
        self.assertEqual(admin_config_list.json()["message"], "仅管理员可访问")

        admin_login = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin123456"},
        )
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['data']['access_token']}"}

        invalid_role_user = self.client.post(
            "/api/admin/users",
            headers=admin_headers,
            json={
                "username": "role_error",
                "password": "User123456",
                "email": "role_error@example.com",
                "roles": ["not-a-real-role"],
            },
        )
        self.assertEqual(invalid_role_user.status_code, 400)
        self.assertIn("角色不存在", invalid_role_user.json()["message"])

        missing_user = self.client.delete("/api/admin/users/99999", headers=admin_headers)
        self.assertEqual(missing_user.status_code, 404)
        self.assertEqual(missing_user.json()["message"], "用户不存在")

    def test_user_ai_config_crud(self):
        """个人 AI 配置增删改查链路测试。"""

        suffix = uuid.uuid4().hex[:8]
        username = f"config_{suffix}"

        self._register_verified_user(username, "test123456", f"{username}@example.com")
        login_resp = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": "test123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        create_resp = self.client.post(
            "/api/ai-configs/me",
            headers=headers,
            json={
                "provider": "openai",
                "model_name": "gpt-4.1-mini",
                "api_key": "sk-test-123",
                "base_url": "https://api.openai.com/v1",
                "temperature": 0.2,
                "is_default": True,
            },
        )
        self.assertEqual(create_resp.status_code, 201)
        create_data = create_resp.json()
        self.assertTrue(create_data["success"])
        config_id = create_data["data"]["id"]
        self.assertTrue(create_data["data"]["is_default"])

        list_resp = self.client.get("/api/ai-configs/me?page=1&page_size=10", headers=headers)
        self.assertEqual(list_resp.status_code, 200)
        list_data = list_resp.json()
        self.assertTrue(list_data["success"])
        self.assertEqual(list_data["data"]["total"], 1)
        self.assertEqual(list_data["data"]["page"], 1)
        self.assertEqual(list_data["data"]["page_size"], 10)
        self.assertEqual(len(list_data["data"]["items"]), 1)

        update_resp = self.client.put(
            f"/api/ai-configs/me/{config_id}",
            headers=headers,
            json={"temperature": 0.8},
        )
        self.assertEqual(update_resp.status_code, 200)
        update_data = update_resp.json()
        self.assertAlmostEqual(update_data["data"]["temperature"], 0.8)

        default_resp = self.client.post(f"/api/ai-configs/me/{config_id}/default", headers=headers)
        self.assertEqual(default_resp.status_code, 200)
        self.assertTrue(default_resp.json()["data"]["is_default"])

        delete_resp = self.client.delete(f"/api/ai-configs/me/{config_id}", headers=headers)
        self.assertEqual(delete_resp.status_code, 200)
        self.assertTrue(delete_resp.json()["success"])

        list_after_delete = self.client.get("/api/ai-configs/me?page=1&page_size=10", headers=headers)
        self.assertEqual(list_after_delete.json()["data"]["items"], [])
        self.assertEqual(list_after_delete.json()["data"]["total"], 0)

    def test_admin_user_crud(self):
        """管理员用户增删改查链路测试。"""

        login_resp = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin123456"},
        )
        self.assertEqual(login_resp.status_code, 200)
        admin_token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}

        suffix = uuid.uuid4().hex[:8]
        username = f"user_{suffix}"
        email = f"{username}@example.com"

        create_resp = self.client.post(
            "/api/admin/users",
            headers=headers,
            json={
                "username": username,
                "password": "User123456",
                "email": email,
                "status": "active",
                "roles": ["learner"],
            },
        )
        self.assertEqual(create_resp.status_code, 201)
        create_data = create_resp.json()
        self.assertTrue(create_data["success"])
        user_id = create_data["data"]["id"]
        self.assertEqual(create_data["data"]["username"], username)
        self.assertIn("learner", create_data["data"]["roles"])

        list_resp = self.client.get("/api/admin/users", headers=headers)
        self.assertEqual(list_resp.status_code, 200)
        list_data = list_resp.json()
        self.assertTrue(list_data["success"])
        self.assertGreaterEqual(list_data["data"]["total"], 1)
        self.assertGreaterEqual(len(list_data["data"]["items"]), 1)

        get_resp = self.client.get(f"/api/admin/users/{user_id}", headers=headers)
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()["data"]["username"], username)

        updated_username = f"user_new_{suffix}"
        update_resp = self.client.put(
            f"/api/admin/users/{user_id}",
            headers=headers,
            json={
                "username": updated_username,
                "email": f"{updated_username}@example.com",
                "password": "UserNew123456",
                "status": "inactive",
                "roles": ["visitor"],
            },
        )
        self.assertEqual(update_resp.status_code, 200)
        update_data = update_resp.json()
        self.assertTrue(update_data["success"])
        self.assertEqual(update_data["data"]["username"], updated_username)
        self.assertEqual(update_data["data"]["status"], "inactive")
        self.assertIn("visitor", update_data["data"]["roles"])

        delete_resp = self.client.delete(f"/api/admin/users/{user_id}", headers=headers)
        self.assertEqual(delete_resp.status_code, 200)
        self.assertTrue(delete_resp.json()["success"])

        missing_resp = self.client.get(f"/api/admin/users/{user_id}", headers=headers)
        self.assertEqual(missing_resp.status_code, 404)

    def test_admin_system_ai_config_crud(self):
        """管理员系统 AI 配置增删改查链路测试。"""

        login_resp = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin123456"},
        )
        self.assertEqual(login_resp.status_code, 200)
        admin_token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}

        create_resp = self.client.post(
            "/api/admin/ai-configs/system",
            headers=headers,
            json={
                "provider": "openai",
                "model_name": "gpt-4.1-mini",
                "api_key": "sk-system-123",
                "base_url": "https://api.openai.com/v1",
                "temperature": 0.3,
                "is_default": True,
                "scope": "system",
            },
        )
        self.assertEqual(create_resp.status_code, 201)
        create_data = create_resp.json()
        self.assertTrue(create_data["success"])
        config_id = create_data["data"]["id"]
        self.assertTrue(create_data["data"]["is_default"])
        self.assertEqual(create_data["data"]["scope"], "system")

        list_resp = self.client.get("/api/admin/ai-configs/system?page=1&page_size=10", headers=headers)
        self.assertEqual(list_resp.status_code, 200)
        list_data = list_resp.json()
        self.assertTrue(list_data["success"])
        self.assertGreaterEqual(list_data["data"]["total"], 1)
        self.assertEqual(list_data["data"]["page"], 1)
        self.assertEqual(list_data["data"]["page_size"], 10)
        self.assertGreaterEqual(len(list_data["data"]["items"]), 1)

        update_resp = self.client.put(
            f"/api/admin/ai-configs/system/{config_id}",
            headers=headers,
            json={"temperature": 0.9, "scope": "system"},
        )
        self.assertEqual(update_resp.status_code, 200)
        update_data = update_resp.json()
        self.assertAlmostEqual(update_data["data"]["temperature"], 0.9)

        default_resp = self.client.post(f"/api/admin/ai-configs/system/{config_id}/default", headers=headers)
        self.assertEqual(default_resp.status_code, 200)
        self.assertTrue(default_resp.json()["data"]["is_default"])

        delete_resp = self.client.delete(f"/api/admin/ai-configs/system/{config_id}", headers=headers)
        self.assertEqual(delete_resp.status_code, 200)
        self.assertTrue(delete_resp.json()["success"])

        list_after_delete = self.client.get("/api/admin/ai-configs/system?page=1&page_size=10", headers=headers)
        self.assertEqual(list_after_delete.status_code, 200)

    def test_register_send_code_rolls_back_when_email_send_fails(self):
        """邮件发送失败时不应留下已提交的验证码记录。"""

        username = f"mailfail_{uuid.uuid4().hex[:8]}"
        email = f"{username}@example.com"

        with patch.object(
            email_service,
            "_send_smtp_email",
            side_effect=HTTPException(status_code=502, detail="邮件发送失败：mock"),
        ):
            resp = self.client.post(
                "/api/auth/register/send-code",
                json={"username": username, "email": email},
            )

        self.assertEqual(resp.status_code, 502)
        self.assertEqual(resp.json()["message"], "邮件发送失败：mock")

        with self.SessionLocal() as db:
            codes = db.query(EmailVerificationCode).filter(EmailVerificationCode.email == email).all()
            self.assertEqual(codes, [])

    def test_admin_email_duplicate_validation(self):
        """管理员邮件配置和模板重复时应返回 400，而不是数据库异常 500。"""

        admin_login = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin123456"},
        )
        headers = {"Authorization": f"Bearer {admin_login.json()['data']['access_token']}"}

        config_name = f"mail-config-{uuid.uuid4().hex[:8]}"
        config_payload = {
            "name": config_name,
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "noreply@example.com",
            "smtp_password": "password",
            "sender_email": "noreply@example.com",
            "sender_name": "申论 Agent",
            "use_tls": True,
            "use_ssl": False,
            "enabled": True,
        }
        first_config = self.client.post("/api/admin/email/configs", headers=headers, json=config_payload)
        self.assertEqual(first_config.status_code, 201)

        duplicate_config = self.client.post("/api/admin/email/configs", headers=headers, json=config_payload)
        self.assertEqual(duplicate_config.status_code, 400)
        self.assertEqual(duplicate_config.json()["message"], "邮件配置名称已存在")

        template_key = f"tpl_{uuid.uuid4().hex[:8]}"
        template_payload = {
            "template_key": template_key,
            "template_name": "重复模板测试",
            "subject": "主题",
            "body_text": "正文",
            "body_html": "<p>正文</p>",
            "enabled": True,
        }
        first_template = self.client.post("/api/admin/email/templates", headers=headers, json=template_payload)
        self.assertEqual(first_template.status_code, 201)

        duplicate_template = self.client.post("/api/admin/email/templates", headers=headers, json=template_payload)
        self.assertEqual(duplicate_template.status_code, 400)
        self.assertEqual(duplicate_template.json()["message"], "邮件模板键已存在")

        config_list = self.client.get("/api/admin/email/configs?page=1&page_size=10", headers=headers)
        self.assertEqual(config_list.status_code, 200)
        self.assertGreaterEqual(config_list.json()["data"]["total"], 2)
        self.assertEqual(config_list.json()["data"]["page"], 1)
        self.assertEqual(config_list.json()["data"]["page_size"], 10)

        template_list = self.client.get("/api/admin/email/templates?page=1&page_size=10", headers=headers)
        self.assertEqual(template_list.status_code, 200)
        self.assertGreaterEqual(template_list.json()["data"]["total"], 3)
        self.assertEqual(template_list.json()["data"]["page"], 1)
        self.assertEqual(template_list.json()["data"]["page_size"], 10)

    def test_admin_prompt_management(self):
        """管理员可以统一管理批改和答疑提示词，普通用户不可访问。"""

        user_resp = self._register_verified_user(
            f"prompt_user_{uuid.uuid4().hex[:6]}",
            "test123456",
            f"prompt_user_{uuid.uuid4().hex[:6]}@example.com",
        )
        token = user_resp.json()["data"]["access_token"]
        user_headers = {"Authorization": f"Bearer {token}"}
        forbidden = self.client.get("/api/admin/prompts", headers=user_headers)
        self.assertEqual(forbidden.status_code, 403)

        admin_login = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin123456"},
        )
        headers = {"Authorization": f"Bearer {admin_login.json()['data']['access_token']}"}

        list_resp = self.client.get("/api/admin/prompts", headers=headers)
        self.assertEqual(list_resp.status_code, 200)
        list_data = list_resp.json()["data"]
        self.assertGreaterEqual(list_data["total"], 3)

        update_resp = self.client.put(
            "/api/admin/prompts/review_repair",
            headers=headers,
            json={"name": "批改修正提示词", "content": "这是新的修正提示词。"},
        )
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(update_resp.json()["data"]["template_type"], "review_repair")
        self.assertEqual(update_resp.json()["data"]["content"], "这是新的修正提示词。")

    def test_admin_system_runtime_config_management(self):
        """管理员可以统一管理运行时配置，普通用户不可访问。"""

        user_resp = self._register_verified_user(
            f"runtime_user_{uuid.uuid4().hex[:6]}",
            "test123456",
            f"runtime_user_{uuid.uuid4().hex[:6]}@example.com",
        )
        token = user_resp.json()["data"]["access_token"]
        user_headers = {"Authorization": f"Bearer {token}"}
        forbidden = self.client.get("/api/admin/system-configs", headers=user_headers)
        self.assertEqual(forbidden.status_code, 403)

        admin_login = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin123456"},
        )
        headers = {"Authorization": f"Bearer {admin_login.json()['data']['access_token']}"}

        list_resp = self.client.get("/api/admin/system-configs", headers=headers)
        self.assertEqual(list_resp.status_code, 200)
        list_data = list_resp.json()["data"]
        self.assertGreaterEqual(list_data["total"], 5)

        update_resp = self.client.put(
            "/api/admin/system-configs/point_compare",
            headers=headers,
            json={
                "name": "要点比对配置",
                "content_json": {
                    "exact_match_threshold": 0.9,
                    "partial_match_threshold": 0.5,
                },
            },
        )
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(update_resp.json()["data"]["config_key"], "point_compare")
        self.assertAlmostEqual(update_resp.json()["data"]["content_json"]["exact_match_threshold"], 0.9)

    def test_question_import_allows_partial_success(self):
        """批量导入遇到单条失败时，应保留其余成功项并返回失败列表。"""

        suffix = uuid.uuid4().hex[:8]
        username = f"import_{suffix}"
        email = f"{username}@example.com"
        self._register_verified_user(username, "test123456", email)
        login_resp = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": "test123456"},
        )
        headers = {"Authorization": f"Bearer {login_resp.json()['data']['access_token']}"}

        original_create_question = question_service.create_question
        call_counter = {"value": 0}

        def flaky_create(db, question):
            call_counter["value"] += 1
            if call_counter["value"] == 2:
                raise RuntimeError("模拟导入失败")
            return original_create_question(db, question)

        payload = {
            "items": [
                {"title": "题目一", "content": "内容一", "question_type": "概括题", "tags": ["A"], "source": "测试"},
                {"title": "题目二", "content": "内容二", "question_type": "对策题", "tags": ["B"], "source": "测试"},
                {"title": "题目三", "content": "内容三", "question_type": "分析题", "tags": ["C"], "source": "测试"},
            ]
        }

        with patch.object(question_service, "create_question", side_effect=flaky_create):
            import_resp = self.client.post("/api/questions/import", headers=headers, json=payload)

        self.assertEqual(import_resp.status_code, 201)
        import_data = import_resp.json()["data"]
        self.assertEqual(len(import_data["imported"]), 2)
        self.assertEqual(len(import_data["failed"]), 1)
        self.assertEqual(import_data["failed"][0]["index"], 1)
        self.assertIn("模拟导入失败", import_data["failed"][0]["message"])

        list_resp = self.client.get("/api/questions?page=1&page_size=10", headers=headers)
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(list_resp.json()["data"]["total"], 2)

    def test_question_user_filter_requires_admin(self):
        """普通用户带 user_id 过滤题库时应明确返回 403。"""

        suffix = uuid.uuid4().hex[:8]
        username = f"question_filter_{suffix}"
        email = f"{username}@example.com"
        self._register_verified_user(username, "test123456", email)
        login_resp = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": "test123456"},
        )
        headers = {"Authorization": f"Bearer {login_resp.json()['data']['access_token']}"}

        resp = self.client.get("/api/questions?user_id=1", headers=headers)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()["message"], "仅管理员可按用户筛选题库")

    def test_question_list_supports_sorting(self):
        """题库列表应支持稳定排序契约。"""

        suffix = uuid.uuid4().hex[:8]
        username = f"question_sort_{suffix}"
        email = f"{username}@example.com"
        self._register_verified_user(username, "test123456", email)
        login_resp = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": "test123456"},
        )
        headers = {"Authorization": f"Bearer {login_resp.json()['data']['access_token']}"}

        self.client.post(
            "/api/questions",
            headers=headers,
            json={"title": "B题目", "content": "内容B", "question_type": "概括题", "tags": ["A"], "source": "测试"},
        )
        self.client.post(
            "/api/questions",
            headers=headers,
            json={"title": "A题目", "content": "内容A", "question_type": "概括题", "tags": ["A"], "source": "测试"},
        )

        sorted_resp = self.client.get(
            "/api/questions?page=1&page_size=10&sort_by=title&sort_order=asc",
            headers=headers,
        )
        self.assertEqual(sorted_resp.status_code, 200)
        sorted_data = sorted_resp.json()["data"]
        items = sorted_data["items"]
        self.assertGreaterEqual(len(items), 2)
        self.assertEqual(items[0]["title"], "A题目")
        self.assertEqual(items[1]["title"], "B题目")
        self.assertEqual(sorted_data["applied_sort"]["sort_by"], "title")
        self.assertEqual(sorted_data["applied_sort"]["sort_order"], "asc")
        self.assertEqual(sorted_data["applied_filters"]["question_type"], None)


if __name__ == "__main__":
    unittest.main()
