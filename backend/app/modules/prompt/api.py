from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import api_success
from app.modules.auth.models import User
from app.modules.prompt.schemas import PromptTemplateUpsertRequest
from app.modules.prompt.service import list_admin_prompt_templates, upsert_admin_prompt_template
from app.shared.deps import get_current_admin_user, get_db
from app.shared.schemas import ApiResponse


router = APIRouter(prefix="/admin/prompts", tags=["后台-Prompt 管理"])


@router.get("", response_model=ApiResponse, summary="查询系统提示词")
def list_prompts(current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    """列出系统级批改、答疑、分析和提纲提示词模板。"""
    return api_success(list_admin_prompt_templates(db), message="获取系统提示词成功")


@router.put("/{template_type}", response_model=ApiResponse, summary="更新系统提示词")
def upsert_prompt(
    template_type: str,
    data: PromptTemplateUpsertRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """更新指定类型的系统提示词模板。"""
    return api_success(upsert_admin_prompt_template(db, template_type, data), message="更新系统提示词成功")
