"""错题本与学习计划业务服务。"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.modules.ai_config.service import get_effective_review_config
from app.modules.auth.repository import get_user_role_names
from app.modules.dashboard.repository import get_weak_question_types
from app.modules.notebook.models import ErrorNotebookEntry, StudyPlan
from app.modules.notebook.repository import (
    create_error_notebook_entry,
    create_study_plan,
    get_all_question_types_for_user,
    get_error_notebook_entry,
    get_existing_error_entry,
    get_low_score_reviews,
    get_questions_by_type,
    get_study_plan,
    list_error_notebook_entries,
    list_study_plans,
    update_error_notebook_entry,
)
from app.modules.notebook.schemas import (
    ErrorNotebookEntryRead,
    ErrorNotebookGenerateResponse,
    ErrorNotebookListResponse,
    StudyPlanGenerateRequest,
    StudyPlanListResponse,
    StudyPlanRead,
    StudyPlanTaskItem,
)
from app.modules.prompt.service import get_prompt_template_content
from app.workflows.review.dto import ReviewLLMConfig


def _is_admin(db: Session, user_id: int) -> bool:
    return "admin" in get_user_role_names(db, user_id)


def _json_loads(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _entry_to_read(entry: ErrorNotebookEntry, question_title: str = "", question_type: str | None = None, score: int | None = None) -> ErrorNotebookEntryRead:
    return ErrorNotebookEntryRead(
        id=entry.id,
        user_id=entry.user_id,
        question_id=entry.question_id,
        review_id=entry.review_id,
        question_title=question_title or "",
        question_type=question_type,
        score=score,
        error_type=entry.error_type,
        error_summary=entry.error_summary,
        missing_points=_json_loads(entry.missing_points, []),
        weak_dimensions=_json_loads(entry.weak_dimensions, []),
        status=entry.status,
        resolve_note=entry.resolve_note,
        resolved_at=entry.resolved_at,
        created_at=entry.created_at,
    )


def _plan_to_read(plan: StudyPlan) -> StudyPlanRead:
    tasks_data = _json_loads(plan.plan_json, [])
    tasks = []
    for item in tasks_data:
        if isinstance(item, dict):
            tasks.append(StudyPlanTaskItem(
                day=item.get("day", 1),
                question_type=item.get("question_type"),
                focus=item.get("focus", ""),
                question_ids=item.get("question_ids", []),
                target_score=item.get("target_score"),
                note=item.get("note", ""),
            ))
    return StudyPlanRead(
        id=plan.id,
        user_id=plan.user_id,
        title=plan.title,
        description=plan.description,
        tasks=tasks,
        status=plan.status,
        generated_by=plan.generated_by,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


# ========== 错题本 ==========

def list_error_notebook(
    db: Session,
    user_id: int,
    *,
    entry_status: str | None = None,
    question_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ErrorNotebookListResponse:
    """查询错题本。"""
    items, total = list_error_notebook_entries(
        db, user_id, status=entry_status, question_type=question_type, page=page, page_size=page_size
    )
    return ErrorNotebookListResponse(
        items=[_entry_to_read(
            item["entry"],
            question_title=item.get("question_title", ""),
            question_type=item.get("question_type"),
            score=item.get("score"),
        ) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def generate_error_notebook(
    db: Session,
    user_id: int,
    *,
    score_threshold: int = 60,
    limit: int = 20,
) -> ErrorNotebookGenerateResponse:
    """基于低分批改记录自动生成错题本条目。"""
    reviews = get_low_score_reviews(db, user_id, score_threshold=score_threshold, limit=limit)

    added = 0
    skipped = 0

    for review in reviews:
        # 跳过已存在的
        if get_existing_error_entry(db, user_id, review.id) is not None:
            skipped += 1
            continue

        # 解析错误信息
        comparison = _json_loads(review.comparison_json, {})
        score_breakdown = _json_loads(review.score_breakdown_json, {})

        missing_points = comparison.get("missing_points", [])
        weak_dimensions = []
        if score_breakdown:
            # 找出得分最低的维度
            dim_scores = [(k, v) for k, v in score_breakdown.items() if isinstance(v, (int, float))]
            dim_scores.sort(key=lambda x: x[1])
            weak_dimensions = [d[0] for d in dim_scores[:3]]

        # 生成错误摘要
        issues_text = review.issues or ""
        error_summary = issues_text[:200] if issues_text else None

        # 判断错误类型
        if review.score is not None and review.score < 30:
            error_type = "very_low_score"
        elif missing_points and len(missing_points) >= 3:
            error_type = "missing_key_points"
        elif weak_dimensions and "structure_score" in weak_dimensions[:2]:
            error_type = "structure_issue"
        elif weak_dimensions and "language_score" in weak_dimensions[:2]:
            error_type = "language_issue"
        else:
            error_type = "low_score"

        entry = create_error_notebook_entry(
            db,
            ErrorNotebookEntry(
                user_id=user_id,
                question_id=review.question_id,
                review_id=review.id,
                error_type=error_type,
                error_summary=error_summary,
                missing_points=json.dumps(missing_points[:5], ensure_ascii=False),
                weak_dimensions=json.dumps(weak_dimensions[:3], ensure_ascii=False),
                status="unresolved",
            ),
        )
        added += 1

    db.commit()

    # 获取当前总数
    _, total = list_error_notebook_entries(db, user_id, page=1, page_size=1)

    return ErrorNotebookGenerateResponse(added=added, skipped=skipped, total=total)


def resolve_error_entry(
    db: Session,
    user_id: int,
    entry_id: int,
    *,
    resolve_note: str | None = None,
) -> ErrorNotebookEntryRead:
    """标记错题已解决。"""
    entry = get_error_notebook_entry(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="错题本条目不存在")
    if entry.user_id != user_id and not _is_admin(db, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该条目")
    if entry.status == "resolved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该条目已标记为已解决")

    update_error_notebook_entry(
        db,
        entry,
        status="resolved",
        resolve_note=resolve_note,
        resolved_at=datetime.now(timezone.utc),
    )
    db.commit()
    db.refresh(entry)
    # 获取题目和批改信息
    from app.modules.question.repository import get_question
    question = get_question(db, entry.question_id)
    score = None
    if entry.review_id:
        from app.modules.review.repository import get_review
        review = get_review(db, entry.review_id)
        if review:
            score = review.score
    return _entry_to_read(
        entry,
        question_title=question.title if question else "",
        question_type=question.question_type if question else None,
        score=score,
    )


# ========== 学习计划 ==========

def list_user_study_plans(
    db: Session,
    user_id: int,
    *,
    plan_status: str | None = None,
) -> StudyPlanListResponse:
    """查询用户学习计划。"""
    items, total = list_study_plans(db, user_id, status=plan_status)
    return StudyPlanListResponse(
        items=[_plan_to_read(item) for item in items],
        total=total,
    )


def generate_study_plan(
    db: Session,
    user_id: int,
    *,
    days: int = 7,
    focus_types: list[str] | None = None,
    use_llm: bool = True,
) -> StudyPlanRead:
    """生成学习计划。"""
    # 确定重点题型
    if not focus_types:
        focus_types = get_weak_question_types(db, user_id, limit=3)
    if not focus_types:
        # 如果没有薄弱题型，取所有题型
        focus_types = get_all_question_types_for_user(db, user_id)[:3]
    if not focus_types:
        focus_types = ["综合分析", "概括归纳", "提出对策"]

    # 尝试 LLM 生成
    if use_llm:
        plan_data = _generate_plan_with_llm(db, user_id, days=days, focus_types=focus_types)
        if plan_data is not None:
            plan = _save_plan(db, user_id, plan_data, generated_by="ai")
            return _plan_to_read(plan)

    # 回退：规则生成
    plan_data = _generate_plan_fallback(db, user_id, days=days, focus_types=focus_types)
    plan = _save_plan(db, user_id, plan_data, generated_by="rule")
    return _plan_to_read(plan)


def _generate_plan_with_llm(
    db: Session,
    user_id: int,
    *,
    days: int,
    focus_types: list[str],
) -> dict | None:
    """使用 LLM 生成学习计划。"""
    try:
        config = get_effective_review_config(db, user_id)
        if config is None:
            return None

        # 获取用户统计信息
        from app.modules.dashboard.repository import get_user_score_stats, get_stats_by_question_type
        score_stats = get_user_score_stats(db, user_id)
        type_stats = get_stats_by_question_type(db, user_id)

        stats_text = f"平均分：{score_stats.get('avg_score', '无')}\n"
        stats_text += f"最近分：{score_stats.get('latest_score', '无')}\n"
        stats_text += "各题型统计：\n"
        for item in type_stats:
            stats_text += f"  {item['question_type']}：练习{item['count']}次，平均{item.get('avg_score', '无')}分\n"

        system_prompt = (
            "你是一个申论训练规划师。根据用户的练习数据，生成一份学习计划。\n"
            "请以 JSON 格式返回，格式为：\n"
            '{"title": "计划标题", "description": "计划说明", "tasks": [{"day": 1, "question_type": "题型", "focus": "训练重点", "target_score": 70, "note": "备注"}]}\n'
            "注意：\n"
            "- 每天安排 1-2 个训练任务\n"
            "- 优先安排薄弱题型\n"
            "- target_score 应该比当前平均分高 5-10 分\n"
            "- 只返回 JSON，不要其他内容"
        )

        user_prompt = (
            f"请为我生成一份 {days} 天的申论训练计划。\n"
            f"我的薄弱题型是：{'、'.join(focus_types)}\n"
            f"我的练习数据：\n{stats_text}\n"
            f"请生成计划。"
        )

        llm = ChatOpenAI(
            model=config.model_name,
            api_key=config.api_key,
            base_url=config.base_url,
            temperature=0.7,
        )
        result = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        content = str(result.content).strip() if result and result.content else ""

        # 尝试解析 JSON
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        plan_data = json.loads(content)
        if isinstance(plan_data, dict) and "tasks" in plan_data:
            return plan_data

        return None
    except Exception:
        return None


def _generate_plan_fallback(
    db: Session,
    user_id: int,
    *,
    days: int,
    focus_types: list[str],
) -> dict:
    """规则生成学习计划。"""
    tasks = []
    type_count = len(focus_types) or 1

    for day in range(1, days + 1):
        # 轮流安排题型
        question_type = focus_types[(day - 1) % type_count] if focus_types else "综合分析"

        # 获取推荐题目
        questions = get_questions_by_type(db, user_id, question_type, limit=2)
        question_ids = [q.id for q in questions]

        # 根据天数安排不同重点
        if day <= days // 3:
            focus = f"基础训练：熟悉{question_type}题型的答题框架和要点提取"
            target_score = 55
        elif day <= days * 2 // 3:
            focus = f"提升训练：强化{question_type}的结构组织和语言表达"
            target_score = 65
        else:
            focus = f"冲刺训练：综合提升{question_type}的得分能力"
            target_score = 75

        tasks.append({
            "day": day,
            "question_type": question_type,
            "focus": focus,
            "question_ids": question_ids,
            "target_score": target_score,
            "note": f"第{day}天，重点练习{question_type}",
        })

    title = f"{days}天申论训练计划"
    description = f"重点提升：{'、'.join(focus_types[:3])}"

    return {
        "title": title,
        "description": description,
        "tasks": tasks,
    }


def _save_plan(db: Session, user_id: int, plan_data: dict, generated_by: str) -> StudyPlan:
    """保存学习计划。"""
    plan = create_study_plan(
        db,
        StudyPlan(
            user_id=user_id,
            title=plan_data.get("title", "学习计划"),
            description=plan_data.get("description"),
            plan_json=json.dumps(plan_data.get("tasks", []), ensure_ascii=False),
            status="active",
            generated_by=generated_by,
        ),
    )
    db.commit()
    db.refresh(plan)
    return plan
