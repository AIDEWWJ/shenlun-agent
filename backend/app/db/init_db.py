from sqlalchemy import select

from app.db.base import Base
from app.modules.ai_config.models import AiConfig
from app.modules.auth.models import Role, User, UserRole
from app.modules.email.models import EmailConfig, EmailTemplate, EmailVerificationCode
from app.modules.notebook.models import ErrorNotebookEntry, StudyPlan
from app.modules.practice.models import Answer, PracticeRecord
from app.modules.question.models import Question, QuestionFavorite
from app.modules.review.models import Review, ReviewQAMessage, ReviewStep
from app.modules.prompt.models import PromptTemplate
from app.modules.prompt.service import ensure_default_prompt_templates
from app.modules.system_config.models import SystemConfig
from app.modules.system_config.service import ensure_default_system_configs
from app.db.session import SessionLocal, engine


DEFAULT_ROLES = [
    {"name": "visitor", "display_name": "访客", "description": "只读浏览用户"},
    {"name": "learner", "display_name": "学员", "description": "核心训练用户"},
    {"name": "admin", "display_name": "管理员", "description": "系统维护用户"},
]

DEFAULT_EMAIL_TEMPLATES = [
    {
        "template_key": "register_verify",
        "template_name": "注册验证码",
        "subject": "{app_name} 注册验证码",
        "body_text": "您好，{username}。\n\n你的注册验证码是：{code}\n有效期 {expires_minutes} 分钟。\n如果不是你本人操作，请忽略此邮件。",
        "body_html": "<p>您好，{username}。</p><p>你的注册验证码是：<strong>{code}</strong></p><p>有效期 {expires_minutes} 分钟。</p><p>如果不是你本人操作，请忽略此邮件。</p>",
        "enabled": True,
    },
    {
        "template_key": "forgot_password_verify",
        "template_name": "找回密码验证码",
        "subject": "{app_name} 找回密码验证码",
        "body_text": "您好，{username}。\n\n你的找回密码验证码是：{code}\n有效期 {expires_minutes} 分钟。\n如果不是你本人操作，请忽略此邮件。",
        "body_html": "<p>您好，{username}。</p><p>你的找回密码验证码是：<strong>{code}</strong></p><p>有效期 {expires_minutes} 分钟。</p><p>如果不是你本人操作，请忽略此邮件。</p>",
        "enabled": True,
    },
]


def init_database() -> None:
    """部署时初始化数据库：建表并写入默认角色。"""

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        existing_roles = {role.name for role in session.scalars(select(Role)).all()}
        changed = False

        for role_data in DEFAULT_ROLES:
            if role_data["name"] not in existing_roles:
                session.add(Role(**role_data))
                changed = True

        if changed:
            session.commit()

        existing_templates = {template.template_key for template in session.scalars(select(EmailTemplate)).all()}
        template_changed = False
        for template_data in DEFAULT_EMAIL_TEMPLATES:
            if template_data["template_key"] not in existing_templates:
                session.add(EmailTemplate(**template_data))
                template_changed = True

        if template_changed:
            session.commit()

        ensure_default_prompt_templates(session)
        ensure_default_system_configs(session)


if __name__ == "__main__":
    init_database()
