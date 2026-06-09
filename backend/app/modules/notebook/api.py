"""错题本与学习计划接口。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import api_success
from app.modules.auth.models import User
from app.modules.notebook.schemas import (
    ErrorNotebookGenerateRequest,
    ErrorNotebookResolveRequest,
    StudyPlanGenerateRequest,
)
from app.modules.notebook.service import (
    generate_error_notebook,
    generate_study_plan,
    list_error_notebook,
    list_user_study_plans,
    resolve_error_entry,
)
from app.shared.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.shared.deps import get_current_active_user, get_db
from app.shared.schemas import ApiResponse


router = APIRouter(tags=["用户-错题本与学习计划"])


# ========== 错题本 ==========

@router.get("/error-notebook", response_model=ApiResponse, summary="查询错题本")
def list_notebook(
    page: int = Query(default=DEFAULT_PAGE, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    status: str | None = Query(default=None, description="筛选状态：unresolved / resolved"),
    question_type: str | None = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """分页查询当前用户的错题本，支持按状态和题型筛选。"""
    return api_success(
        list_error_notebook(
            db, current_user.id,
            entry_status=status,
            question_type=question_type,
            page=page,
            page_size=page_size,
        ),
        message="获取错题本成功",
    )


@router.post("/error-notebook/generate", response_model=ApiResponse, summary="生成错题本")
def generate_notebook(
    data: ErrorNotebookGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """基于低分批改记录自动生成错题本条目。已存在的记录会被跳过。"""
    return api_success(
        generate_error_notebook(
            db, current_user.id,
            score_threshold=data.score_threshold,
            limit=data.limit,
        ),
        message="生成错题本完成",
    )


@router.patch("/error-notebook/{entry_id}/resolve", response_model=ApiResponse, summary="标记错题已解决")
def resolve_entry(
    entry_id: int,
    data: ErrorNotebookResolveRequest | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """标记错题本中的某条记录为已解决，可附带解决备注。"""
    resolve_note = data.resolve_note if data else None
    return api_success(
        resolve_error_entry(db, current_user.id, entry_id, resolve_note=resolve_note),
        message="标记已解决",
    )


# ========== 学习计划 ==========

@router.get("/study-plans/me", response_model=ApiResponse, summary="查询我的学习计划")
def list_plans(
    status: str | None = Query(default=None, description="筛选状态：active / completed / archived"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """查询当前用户的学习计划列表。"""
    return api_success(
        list_user_study_plans(db, current_user.id, plan_status=status),
        message="获取学习计划成功",
    )


@router.post("/study-plans/generate", response_model=ApiResponse, summary="生成学习计划")
def generate_plan(
    data: StudyPlanGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """根据用户练习数据生成个性化学习计划。支持 AI 生成和规则回退。"""
    return api_success(
        generate_study_plan(
            db, current_user.id,
            days=data.days,
            focus_types=data.focus_types or None,
            use_llm=data.use_llm,
        ),
        message="生成学习计划成功",
    )
