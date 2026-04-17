from sqlalchemy import select

from app.db.base import Base
from app.models import (  # noqa: F401
    AiConfig,
    Answer,
    PracticeRecord,
    PromptTemplate,
    Question,
    Role,
    Review,
    User,
    UserRole,
)
from app.db.session import SessionLocal, engine


DEFAULT_ROLES = [
    {"name": "visitor", "display_name": "访客", "description": "只读浏览用户"},
    {"name": "learner", "display_name": "学员", "description": "核心训练用户"},
    {"name": "admin", "display_name": "管理员", "description": "系统维护用户"},
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


if __name__ == "__main__":
    init_database()
