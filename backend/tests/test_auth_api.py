import os
import unittest
import uuid


os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main as backend_main
from app.api.deps import get_db
from app.core.security import get_password_hash
from app.db.base import Base
from app.models import EmailConfig, EmailTemplate, EmailVerificationCode, Role, User, UserRole
import app.services.email_service as email_service


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
                "system_prompt": "你是申论助手",
                "is_default": True,
            },
        )
        self.assertEqual(create_resp.status_code, 201)
        create_data = create_resp.json()
        self.assertTrue(create_data["success"])
        config_id = create_data["data"]["id"]
        self.assertTrue(create_data["data"]["is_default"])

        list_resp = self.client.get("/api/ai-configs/me", headers=headers)
        self.assertEqual(list_resp.status_code, 200)
        list_data = list_resp.json()
        self.assertTrue(list_data["success"])
        self.assertEqual(len(list_data["data"]), 1)

        update_resp = self.client.put(
            f"/api/ai-configs/me/{config_id}",
            headers=headers,
            json={"temperature": 0.8, "system_prompt": "更新后的提示词"},
        )
        self.assertEqual(update_resp.status_code, 200)
        update_data = update_resp.json()
        self.assertAlmostEqual(update_data["data"]["temperature"], 0.8)
        self.assertEqual(update_data["data"]["system_prompt"], "更新后的提示词")

        default_resp = self.client.post(f"/api/ai-configs/me/{config_id}/default", headers=headers)
        self.assertEqual(default_resp.status_code, 200)
        self.assertTrue(default_resp.json()["data"]["is_default"])

        delete_resp = self.client.delete(f"/api/ai-configs/me/{config_id}", headers=headers)
        self.assertEqual(delete_resp.status_code, 200)
        self.assertTrue(delete_resp.json()["success"])

        list_after_delete = self.client.get("/api/ai-configs/me", headers=headers)
        self.assertEqual(list_after_delete.json()["data"], [])

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
        self.assertGreaterEqual(len(list_data["data"]), 1)

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
                "system_prompt": "你是系统默认申论助手",
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

        list_resp = self.client.get("/api/admin/ai-configs/system", headers=headers)
        self.assertEqual(list_resp.status_code, 200)
        list_data = list_resp.json()
        self.assertTrue(list_data["success"])
        self.assertGreaterEqual(len(list_data["data"]), 1)

        update_resp = self.client.put(
            f"/api/admin/ai-configs/system/{config_id}",
            headers=headers,
            json={"temperature": 0.9, "system_prompt": "更新后的系统提示词", "scope": "system"},
        )
        self.assertEqual(update_resp.status_code, 200)
        update_data = update_resp.json()
        self.assertAlmostEqual(update_data["data"]["temperature"], 0.9)
        self.assertEqual(update_data["data"]["system_prompt"], "更新后的系统提示词")

        default_resp = self.client.post(f"/api/admin/ai-configs/system/{config_id}/default", headers=headers)
        self.assertEqual(default_resp.status_code, 200)
        self.assertTrue(default_resp.json()["data"]["is_default"])

        delete_resp = self.client.delete(f"/api/admin/ai-configs/system/{config_id}", headers=headers)
        self.assertEqual(delete_resp.status_code, 200)
        self.assertTrue(delete_resp.json()["success"])

        list_after_delete = self.client.get("/api/admin/ai-configs/system", headers=headers)
        self.assertEqual(list_after_delete.status_code, 200)


if __name__ == "__main__":
    unittest.main()
