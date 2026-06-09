"""流式批改接口 — 通过 SSE 逐步返回批改进度。"""

from __future__ import annotations

import json
import traceback
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.modules.auth.models import User
from app.modules.practice.schemas import ReviewCreateRequest, ReviewFromContentRequest
from app.shared.deps import get_current_active_user, get_db
from app.shared.schemas import ApiResponse


router = APIRouter(tags=["用户-练习与批改"])


class ReviewQAStreamRequest(BaseModel):
    """流式答疑请求。"""

    question: str = Field(min_length=1, max_length=2000, description="用户当前的追问内容")
    use_llm: bool = Field(default=True, description="是否使用 AI 模型生成答疑")
    conversation_id: str | None = Field(default=None, max_length=64, description="会话 ID")
    parent_message_id: int | None = Field(default=None, ge=1, description="上一条答疑消息 ID")


def _sse_event(event: str, data: dict) -> dict:
    """构造 SSE 事件。"""
    return {"event": event, "data": json.dumps(data, ensure_ascii=False)}


def _stream_review_from_content(
    db: Session,
    user_id: int,
    question_id: int,
    answer_content: str,
    answer_id: int | None,
    reference_points: list[str],
    use_llm: bool,
) -> AsyncGenerator[dict, None]:
    """生成器：逐步执行批改并 yield SSE 事件。"""

    async def event_generator():
        from app.modules.ai_config.service import get_effective_review_config
        from app.modules.auth.repository import get_user_role_names
        from app.modules.practice.models import Answer
        from app.modules.practice.repository import (
            create_answer as create_answer_record,
            create_practice_record,
            create_review,
            create_review_step,
            delete_review_steps,
            get_answer,
            get_latest_answer_version_no,
            get_practice_record_by_answer_id,
            get_question,
            get_review_by_answer_id,
            update_answer as update_answer_record,
            update_practice_record,
            update_review,
        )
        from app.modules.prompt.service import get_prompt_template_content
        from app.modules.review.models import Review, ReviewStep as ReviewStepModel
        from app.modules.system_config.service import (
            load_language_analysis_config,
            load_point_compare_config,
            load_structure_analysis_config,
        )
        from app.workflows.review.dto import ReviewLLMConfig, ReviewRequest, ReviewStep
        from app.workflows.review.orchestrator import ReviewService

        try:
            # Step 0: 准备阶段
            yield _sse_event("step", {"step": "prepare", "step_name": "准备批改", "order": 0, "status": "running"})

            question = get_question(db, question_id)
            if question is None:
                yield _sse_event("error", {"message": "题目不存在"})
                return
            if question.user_id != user_id and "admin" not in get_user_role_names(db, user_id):
                yield _sse_event("error", {"message": "无权访问该题目"})
                return

            # 处理答案版本
            if answer_id is None:
                latest_version = get_latest_answer_version_no(db, user_id=user_id, question_id=question.id)
                answer = create_answer_record(
                    db,
                    Answer(user_id=user_id, question_id=question.id, content=answer_content, version_no=latest_version + 1),
                )
            else:
                answer = get_answer(db, answer_id)
                if answer is None:
                    yield _sse_event("error", {"message": "答案不存在"})
                    return
                if answer.user_id != user_id:
                    yield _sse_event("error", {"message": "无权操作该答案"})
                    return
                if answer.question_id != question.id:
                    yield _sse_event("error", {"message": "答案不属于该题目"})
                    return
                if get_review_by_answer_id(db, answer.id) is None:
                    update_answer_record(db, answer, content=answer_content)
                else:
                    latest_version = get_latest_answer_version_no(db, user_id=user_id, question_id=question.id)
                    answer = create_answer_record(
                        db,
                        Answer(user_id=user_id, question_id=question.id, content=answer_content, version_no=latest_version + 1),
                    )

            # 构建 LLM 配置
            llm_config = None
            if use_llm:
                config = get_effective_review_config(db, user_id)
                if config is not None:
                    llm_config = ReviewLLMConfig(
                        provider=config.provider,
                        model_name=config.model_name,
                        api_key=config.api_key,
                        base_url=config.base_url,
                        temperature=config.temperature,
                        system_prompt=config.system_prompt,
                        repair_system_prompt=get_prompt_template_content(db, "review_repair"),
                        review_system_prompt=get_prompt_template_content(db, "review_system"),
                        review_qa_system_prompt=get_prompt_template_content(db, "review_qa"),
                        question_analysis_system_prompt=get_prompt_template_content(db, "question_analysis_system"),
                        question_analysis_user_prompt=get_prompt_template_content(db, "question_analysis_user"),
                        reference_point_extract_system_prompt=get_prompt_template_content(db, "reference_point_extract_system"),
                        reference_point_extract_user_prompt=get_prompt_template_content(db, "reference_point_extract_user"),
                        user_point_extract_system_prompt=get_prompt_template_content(db, "user_point_extract_system"),
                        user_point_extract_user_prompt=get_prompt_template_content(db, "user_point_extract_user"),
                        outline_generate_system_prompt=get_prompt_template_content(db, "outline_generate_system"),
                        outline_generate_user_prompt=get_prompt_template_content(db, "outline_generate_user"),
                    )

            if llm_config is None:
                yield _sse_event("error", {"message": "批改模型未配置"})
                return

            yield _sse_event("step", {"step": "prepare", "step_name": "准备批改", "order": 0, "status": "done", "answer_id": answer.id})

            # 构建批改请求
            request = ReviewRequest(
                question_title=question.title,
                question_content=question.content,
                answer_content=answer.content,
                question_type=question.question_type,
                reference_points=reference_points or [],
            )

            # 构建 ReviewService
            review_service = ReviewService(
                llm_config,
                point_compare_config=load_point_compare_config(db),
                structure_config=load_structure_analysis_config(db),
                language_config=load_language_analysis_config(db),
            )

            steps: list[ReviewStep] = []

            # Step 1: 题目解析
            yield _sse_event("step", {"step": "question_analysis", "step_name": "题目解析", "order": 1, "status": "running"})
            question_analysis = review_service.question_analyzer.analyze(request)
            step1 = ReviewStep(step_key="question_analysis", step_name="题目解析", order_no=1, output_data=question_analysis.model_dump())
            steps.append(step1)
            yield _sse_event("step", {
                "step": "question_analysis", "step_name": "题目解析", "order": 1, "status": "done",
                "result": {"question_type": question_analysis.question_type, "key_topics": question_analysis.key_topics[:5]},
            })

            # Step 2: 参考答案要点抽取
            yield _sse_event("step", {"step": "reference_point_extraction", "step_name": "参考答案要点抽取", "order": 2, "status": "running"})
            if not request.reference_points:
                from app.workflows.review.dto import PointExtractionResult
                reference_points_result = PointExtractionResult(points=[], summary="未提供参考要点，AI 将基于题干和作答直接批改")
            else:
                reference_points_result = review_service.reference_point_extractor.extract(request.reference_points, question_analysis)
            step2 = ReviewStep(step_key="reference_point_extraction", step_name="参考答案要点抽取", order_no=2, output_data=reference_points_result.model_dump())
            steps.append(step2)
            yield _sse_event("step", {
                "step": "reference_point_extraction", "step_name": "参考答案要点抽取", "order": 2, "status": "done",
                "result": {"point_count": len(reference_points_result.points)},
            })

            # Step 3: 用户答案要点抽取
            yield _sse_event("step", {"step": "user_point_extraction", "step_name": "用户答案要点抽取", "order": 3, "status": "running"})
            user_points = review_service.user_point_extractor.extract(request, question_analysis)
            step3 = ReviewStep(step_key="user_point_extraction", step_name="用户答案要点抽取", order_no=3, output_data=user_points.model_dump())
            steps.append(step3)
            yield _sse_event("step", {
                "step": "user_point_extraction", "step_name": "用户答案要点抽取", "order": 3, "status": "done",
                "result": {"point_count": len(user_points.points)},
            })

            # Step 4: 要点比对
            yield _sse_event("step", {"step": "point_comparison", "step_name": "要点比对", "order": 4, "status": "running"})
            comparison = review_service.point_comparator.compare(reference_points_result, user_points)
            step4 = ReviewStep(step_key="point_comparison", step_name="要点比对", order_no=4, output_data=comparison.model_dump())
            steps.append(step4)
            yield _sse_event("step", {
                "step": "point_comparison", "step_name": "要点比对", "order": 4, "status": "done",
                "result": {"coverage_rate": comparison.coverage_rate, "matched": len(comparison.matched_points), "missing": len(comparison.missing_points)},
            })

            # Step 5: AI 综合批改
            yield _sse_event("step", {"step": "ai_review", "step_name": "AI综合批改", "order": 5, "status": "running"})
            ai_analysis = review_service.reviewer.review(
                request,
                question_analysis=question_analysis,
                reference_point_analysis=reference_points_result,
                user_point_analysis=user_points,
                comparison=comparison,
            )
            step5 = ReviewStep(step_key="ai_review", step_name="AI综合批改", order_no=5, output_data=ai_analysis.model_dump())
            steps.append(step5)
            yield _sse_event("step", {
                "step": "ai_review", "step_name": "AI综合批改", "order": 5, "status": "done",
                "result": {"score": ai_analysis.score},
            })

            # Step 6: 保存结果
            yield _sse_event("step", {"step": "save", "step_name": "保存批改结果", "order": 6, "status": "running"})

            # Finalize analysis
            analysis = review_service._finalize_ai_analysis(
                request=request,
                ai_analysis=ai_analysis,
                question_analysis=question_analysis,
                reference_points=reference_points_result,
                user_points=user_points,
                comparison=comparison,
                steps=steps,
            )

            # 保存 review
            review_payload = {
                "answer_id": answer.id,
                "question_id": question.id,
                "user_id": user_id,
                "question_title_snapshot": question.title,
                "question_type_snapshot": analysis.question_type or question.question_type,
                "question_content_snapshot": question.content,
                "answer_content_snapshot": answer.content,
                "reference_points_json": json.dumps(reference_points or [], ensure_ascii=False),
                "question_analysis_json": json.dumps(analysis.question_analysis or {}, ensure_ascii=False),
                "reference_point_analysis_json": json.dumps(analysis.reference_point_analysis, ensure_ascii=False),
                "user_point_analysis_json": json.dumps(analysis.user_point_analysis, ensure_ascii=False),
                "comparison_json": json.dumps(analysis.comparison_analysis or {}, ensure_ascii=False),
                "structure_analysis_json": json.dumps(analysis.structure_analysis or {}, ensure_ascii=False),
                "language_analysis_json": json.dumps(analysis.language_analysis or {}, ensure_ascii=False),
                "rule_analysis_json": json.dumps(analysis.rule_analysis or {}, ensure_ascii=False),
                "score_breakdown_json": json.dumps(analysis.score_breakdown, ensure_ascii=False),
                "report_json": json.dumps(analysis.report_json or {}, ensure_ascii=False),
                "model_provider": llm_config.provider,
                "model_name": llm_config.model_name,
                "score": analysis.score,
                "strengths": "\n".join(analysis.strengths) if analysis.strengths else None,
                "issues": "\n".join(analysis.issues) if analysis.issues else None,
                "suggestions": "\n".join(analysis.suggestions) if analysis.suggestions else None,
                "summary": analysis.summary,
            }

            existing_review = get_review_by_answer_id(db, answer.id)
            if existing_review is None:
                review = create_review(db, review_data=review_payload)
            else:
                for key, value in review_payload.items():
                    setattr(existing_review, key, value)
                db.flush()
                delete_review_steps(db, existing_review.id)
                review = existing_review

            # 保存步骤
            for step in steps:
                create_review_step(
                    db,
                    ReviewStepModel(
                        review_id=review.id,
                        step_key=step.step_key,
                        step_name=step.step_name,
                        order_no=step.order_no,
                        status=step.status,
                        critical=step.critical,
                        attempts=step.attempts,
                        error=step.error,
                        input_json=json.dumps(step.input_data, ensure_ascii=False),
                        output_json=json.dumps(step.output_data, ensure_ascii=False),
                        note=step.note,
                    ),
                )

            # 保存练习记录
            existing_record = get_practice_record_by_answer_id(db, answer.id)
            if existing_record is None:
                create_practice_record(
                    db,
                    user_id=user_id,
                    question_id=question.id,
                    answer_id=answer.id,
                    review_id=review.id,
                    status="finished",
                )
            else:
                update_practice_record(db, existing_record, review_id=review.id, status="finished")

            db.commit()

            yield _sse_event("step", {"step": "save", "step_name": "保存批改结果", "order": 6, "status": "done"})

            # 最终结果
            yield _sse_event("complete", {
                "answer_id": answer.id,
                "review_id": review.id,
                "analysis": jsonable_encoder(analysis.model_dump()),
            })

        except Exception as exc:
            db.rollback()
            yield _sse_event("error", {"message": f"批改过程出错：{str(exc)}"})

    return event_generator()


@router.post("/review/stream", summary="流式批改（SSE）")
async def review_stream(
    data: ReviewFromContentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """基于答案正文发起流式批改，通过 SSE 逐步返回批改进度。

    事件类型：
    - `step`: 批改步骤进度，包含 step/step_name/order/status/result
    - `complete`: 批改完成，包含 answer_id/review_id/analysis
    - `error`: 批改出错，包含 message
    """
    generator = _stream_review_from_content(
        db,
        user_id=current_user.id,
        question_id=data.question_id,
        answer_content=data.answer_content,
        answer_id=data.answer_id,
        reference_points=data.reference_points,
        use_llm=data.use_llm,
    )
    return EventSourceResponse(generator)


@router.post("/review/from-content/stream", summary="流式批改（SSE）- 别名")
async def review_from_content_stream(
    data: ReviewFromContentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """与 /review/stream 相同，提供更语义化的路径。"""
    generator = _stream_review_from_content(
        db,
        user_id=current_user.id,
        question_id=data.question_id,
        answer_content=data.answer_content,
        answer_id=data.answer_id,
        reference_points=data.reference_points,
        use_llm=data.use_llm,
    )
    return EventSourceResponse(generator)



@router.post("/reviews/{review_id}/qa/stream", summary="流式答疑（SSE）")
async def review_qa_stream(
    review_id: int,
    data: ReviewQAStreamRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """围绕批改结果发起流式答疑，通过 SSE 逐步返回答疑进度。

    事件类型：
    - `thinking`: AI 正在思考
    - `chunk`: 答疑内容片段（流式文本）
    - `complete`: 答疑完成，包含完整结果
    - `error`: 出错
    """
    from app.modules.review.service import get_review_detail, _is_admin, _classify_review_question, _json_loads
    from app.modules.review.repository import (
        get_review,
        get_review_qa_message,
        list_review_qa_messages as list_review_qa_messages_repo,
        create_review_qa_message,
    )
    from app.modules.review.models import ReviewQAMessage
    from app.modules.review.schemas import ReviewQAMessageRead
    from app.modules.ai_config.service import get_effective_review_config
    from app.modules.prompt.service import get_prompt_template_content
    from app.workflows.review.dto import ReviewLLMConfig
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    import uuid

    async def event_generator():
        try:
            # 验证权限
            review = get_review(db, review_id)
            if review is None:
                yield _sse_event("error", {"message": "批改记录不存在"})
                return
            if review.user_id != current_user.id and not _is_admin(db, current_user.id):
                yield _sse_event("error", {"message": "无权查看该批改记录"})
                return

            detail = get_review_detail(db, review_id=review_id, current_user_id=current_user.id)

            # 处理会话
            conversation_id = data.conversation_id
            parent_message_id = data.parent_message_id

            if parent_message_id is not None:
                parent_message = get_review_qa_message(db, parent_message_id)
                if parent_message is None:
                    yield _sse_event("error", {"message": "父答疑消息不存在"})
                    return
                if parent_message.review_id != review_id:
                    yield _sse_event("error", {"message": "父答疑消息不属于该批改记录"})
                    return
                if conversation_id is None:
                    conversation_id = parent_message.conversation_id
            else:
                parent_message = None

            if conversation_id is None:
                conversation_id = uuid.uuid4().hex

            # 获取历史对话
            history, total = list_review_qa_messages_repo(
                db,
                review_id=review_id,
                user_id=None if _is_admin(db, current_user.id) else current_user.id,
                conversation_id=conversation_id,
                page=1,
                page_size=200,
            )
            round_no = total + 1

            yield _sse_event("thinking", {"message": "正在分析问题..."})

            # 构建 LLM 配置
            config = get_effective_review_config(db, current_user.id)
            if config is None or not data.use_llm:
                # 回退到非流式答疑
                from app.modules.review.service import _build_review_qa_fallback
                response = _build_review_qa_fallback(detail, data.question)
                yield _sse_event("chunk", {"text": response.answer_text})
                # 保存消息
                message = create_review_qa_message(
                    db,
                    ReviewQAMessage(
                        review_id=review_id,
                        user_id=current_user.id,
                        conversation_id=conversation_id,
                        parent_message_id=parent_message_id,
                        round_no=round_no,
                        question_text=data.question,
                        question_category=response.question_category,
                        answer_text=response.answer_text,
                        evidence_refs_json=json.dumps(response.evidence_refs, ensure_ascii=False),
                        used_llm=False,
                    ),
                )
                db.commit()
                db.refresh(message)
                yield _sse_event("complete", {
                    "message_id": message.id,
                    "conversation_id": conversation_id,
                    "question_category": response.question_category,
                    "answer_text": response.answer_text,
                    "evidence_refs": response.evidence_refs,
                    "used_llm": False,
                })
                return

            llm_config = ReviewLLMConfig(
                provider=config.provider,
                model_name=config.model_name,
                api_key=config.api_key,
                base_url=config.base_url,
                temperature=config.temperature,
                system_prompt=config.system_prompt,
                repair_system_prompt=get_prompt_template_content(db, "review_repair"),
                review_system_prompt=get_prompt_template_content(db, "review_system"),
                review_qa_system_prompt=get_prompt_template_content(db, "review_qa"),
            )

            category = _classify_review_question(data.question)

            # 构建 prompt
            history_lines: list[str] = []
            for item in history[-5:]:
                history_lines.append(f"第{item.round_no}轮用户问题：{item.question_text}")
                history_lines.append(f"第{item.round_no}轮系统回答：{item.answer_text}")
            history_text = "\n".join(history_lines) if history_lines else "无历史对话"

            evidence_lines = [
                f"总评：{detail.summary or '无'}",
                f"总分：{detail.score if detail.score is not None else '未评分'}",
                f"分数拆解：{json.dumps(detail.score_breakdown, ensure_ascii=False)}",
                f"要点对比：{json.dumps(detail.comparison, ensure_ascii=False)}",
                f"结构分析：{json.dumps(detail.structure_analysis, ensure_ascii=False)}",
                f"语言分析：{json.dumps(detail.language_analysis, ensure_ascii=False)}",
                f"规则分析：{json.dumps(detail.rule_analysis, ensure_ascii=False)}",
                f"修改建议：{detail.suggestions or '无'}",
            ]

            base_prompt = (
                llm_config.review_qa_system_prompt.strip()
                if llm_config.review_qa_system_prompt
                else (
                    llm_config.review_system_prompt.strip()
                    if llm_config.review_system_prompt
                    else (llm_config.system_prompt.strip() if llm_config.system_prompt else "")
                )
            )
            system_prompt = (
                f"{base_prompt}\n"
                "如果用户在追问上一轮，请结合历史对话连续回答。"
            ).strip()
            user_prompt = (
                f"问题分类：{category}\n"
                f"历史对话：\n{history_text}\n\n"
                f"批改证据：\n" + "\n".join(evidence_lines) + "\n\n"
                f"当前用户问题：{data.question}\n"
                "请给出简洁明确的答复。"
            )

            yield _sse_event("thinking", {"message": "AI 正在生成回答..."})

            # 流式调用 LLM
            llm = ChatOpenAI(
                model=llm_config.model_name,
                api_key=llm_config.api_key,
                base_url=llm_config.base_url,
                temperature=llm_config.temperature,
                streaming=True,
            )

            full_answer = ""
            async for chunk in llm.astream([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]):
                if chunk.content:
                    text_chunk = str(chunk.content)
                    full_answer += text_chunk
                    yield _sse_event("chunk", {"text": text_chunk})

            if not full_answer.strip():
                # 回退
                from app.modules.review.service import _build_review_qa_fallback
                response = _build_review_qa_fallback(detail, data.question)
                full_answer = response.answer_text
                category = response.question_category

            evidence_refs = ["summary", "score_breakdown", "comparison", "structure_analysis", "language_analysis", "rule_analysis", "suggestions"]

            # 保存消息
            message = create_review_qa_message(
                db,
                ReviewQAMessage(
                    review_id=review_id,
                    user_id=current_user.id,
                    conversation_id=conversation_id,
                    parent_message_id=parent_message_id,
                    round_no=round_no,
                    question_text=data.question,
                    question_category=category,
                    answer_text=full_answer,
                    evidence_refs_json=json.dumps(evidence_refs, ensure_ascii=False),
                    used_llm=True,
                ),
            )
            db.commit()
            db.refresh(message)

            yield _sse_event("complete", {
                "message_id": message.id,
                "conversation_id": conversation_id,
                "question_category": category,
                "answer_text": full_answer,
                "evidence_refs": evidence_refs,
                "used_llm": True,
            })

        except Exception as exc:
            db.rollback()
            yield _sse_event("error", {"message": f"答疑过程出错：{str(exc)}"})

    return EventSourceResponse(event_generator())

