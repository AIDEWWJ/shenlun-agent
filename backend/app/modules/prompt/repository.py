from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.prompt.models import PromptTemplate


def list_system_prompt_templates(db: Session) -> list[PromptTemplate]:
    return db.scalars(
        select(PromptTemplate)
        .where(PromptTemplate.user_id.is_(None))
        .order_by(PromptTemplate.template_type.asc(), PromptTemplate.id.asc())
    ).all()


def get_system_prompt_template(db: Session, template_type: str) -> PromptTemplate | None:
    return db.scalars(
        select(PromptTemplate)
        .where(PromptTemplate.user_id.is_(None), PromptTemplate.template_type == template_type)
    ).first()


def create_prompt_template(db: Session, template: PromptTemplate) -> PromptTemplate:
    db.add(template)
    db.flush()
    return template


def update_prompt_template(db: Session, template: PromptTemplate, *, name: str | None = None, content: str | None = None) -> PromptTemplate:
    if name is not None:
        template.name = name
    if content is not None:
        template.content = content
    db.flush()
    return template
