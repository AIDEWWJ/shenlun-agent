"""练习业务模块。"""

from __future__ import annotations

import json
from datetime import date, datetime, time, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.capabilities.analyzers.question_analyzer import QuestionAnalyzerAgent
from app.ai.capabilities.generators.outline_generator import OutlineGeneratorAgent
from app.modules.ai_config.service import get_effective_review_config
from app.modules.auth.repository import get_user_role_names
from app.modules.prompt.service import get_prompt_template_content
from app.modules.practice.models import Answer, PaperPracticeSession, PracticeRecord
from app.modules.practice.repository import (
    create_answer as create_answer_record,
    create_practice_record,
    create_review,
    create_review_step,
    delete_review_steps,
    get_answer,
    get_latest_answer_version_no,
    get_practice_record,
    get_practice_record_by_answer_id,
    get_question,
    get_review_by_answer_id,
    list_answers,
    list_practice_records as list_practice_records_repo,
    update_answer as update_answer_record,
    update_practice_record,
    update_review,
)
from app.modules.practice.schemas import (
    AnswerListResponse,
    AnswerRead,
    OutlineResponse,
    PracticeRecordDetail,
    PracticeRecordListItem,
    PracticeRecordListResponse,
    PracticeSessionRead,
    PracticeSessionSubmitResponse,
    QuestionAnalysisResponse,
    ReviewExecutionResponse,
)
from app.modules.question.models import Question
from app.modules.review.models import Review
from app.modules.review.models import ReviewStep as ReviewStepModel
from app.modules.review.service import ReviewService
from app.modules.system_config.service import (
    load_language_analysis_config,
    load_point_compare_config,
    load_practice_fallback_config,
    load_structure_analysis_config,
)
from app.workflows.review.dto import (
    PointComparisonResult,
    QuestionAnalysisResult,
    ReviewAnalysis,
    ReviewLLMConfig,
    ReviewRequest,
)


class PracticeService:
    """练习、答案与批改业务服务。"""

    def __init__(self, review_service: ReviewService | None = None) -> None:
        self.review_service = review_service or ReviewService()
        self.fallback_config = None

    def create_answer(
        self,
        db: Session,
        *,
        user_id: int,
        question_id: int,
        content: str,
    ) -> AnswerRead:
        question = self._load_question_for_user(db, user_id, question_id)
        answer = self._create_answer_version(db, user_id=user_id, question_id=question.id, content=content)
        db.commit()
        db.refresh(answer)
        return self._to_answer_read(answer, question=question)

    def update_answer(
        self,
        db: Session,
        *,
        user_id: int,
        answer_id: int,
        content: str,
    ) -> AnswerRead:
        answer = self._load_answer_for_user(db, user_id, answer_id)
        if get_review_by_answer_id(db, answer.id) is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该答案已批改，不能直接修改，请创建新版本",
            )

        update_answer_record(db, answer, content=content)
        db.commit()
        db.refresh(answer)
        return self._to_answer_read(answer, review=None)

    def get_answer_detail(self, db: Session, *, user_id: int, answer_id: int) -> AnswerRead:
        answer = self._load_answer_for_user(db, user_id, answer_id)
        review = get_review_by_answer_id(db, answer.id)
        return self._to_answer_read(answer, review=review)

    def duplicate_answer(
        self,
        db: Session,
        *,
        user_id: int,
        answer_id: int,
        content: str | None = None,
    ) -> AnswerRead:
        """基于旧答案创建新版本。"""
        source_answer = self._load_answer_for_user(db, user_id, answer_id)
        new_content = content if content else source_answer.content
        new_answer = self._create_answer_version(
            db, user_id=user_id, question_id=source_answer.question_id, content=new_content
        )
        db.commit()
        db.refresh(new_answer)
        return self._to_answer_read(new_answer)

    def list_question_answers(
        self,
        db: Session,
        *,
        user_id: int,
        question_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> AnswerListResponse:
        question = self._load_question_for_user(db, user_id, question_id)
        items, total = list_answers(db, user_id=user_id, question_id=question.id, page=page, page_size=page_size)
        return AnswerListResponse(
            items=[self._to_answer_read(item, question=question) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_current_practice_session(
        self,
        db: Session,
        *,
        user_id: int,
        question_id: int,
    ) -> PracticeSessionRead | None:
        self._load_question_for_user(db, user_id, question_id)
        session = get_current_practice_session_by_question(db, user_id=user_id, question_id=question_id)
        if session is None:
            return None
        return self._to_practice_session_read(session)

    def create_practice_session(
        self,
        db: Session,
        *,
        user_id: int,
        question_id: int,
    ) -> PracticeSessionRead:
        question = self._load_question_for_user(db, user_id, question_id)
        current_session = get_current_practice_session_by_question(db, user_id=user_id, question_id=question_id)
        if current_session is not None:
            return self._to_practice_session_read(current_session)

        session = create_practice_session_record(
            db,
            PracticeSession(
                user_id=user_id,
                question_id=question.id,
                status="drafting",
                answers_json=json.dumps(self._build_empty_session_answers(question), ensure_ascii=False),
                elapsed_seconds=0,
            ),
        )
        db.commit()
        db.refresh(session)
        return self._to_practice_session_read(session)

    def update_practice_session(
        self,
        db: Session,
        *,
        user_id: int,
        session_id: int,
        answers: dict[str, str],
        elapsed_seconds: int | None = None,
    ) -> PracticeSessionRead:
        session = self._load_practice_session_for_user(db, user_id, session_id)
        if session.status != "drafting":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前练习会话不可再编辑")

        update_practice_session_record(
            db,
            session,
            answers_json=json.dumps(answers, ensure_ascii=False),
            elapsed_seconds=elapsed_seconds,
        )
        db.commit()
        db.refresh(session)
        return self._to_practice_session_read(session)

    def submit_practice_session(
        self,
        db: Session,
        *,
        user_id: int,
        session_id: int,
        reference_points: list[str] | None = None,
        use_llm: bool = True,
    ) -> PracticeSessionSubmitResponse:
        session = self._load_practice_session_for_user(db, user_id, session_id)
        if session.status != "drafting":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前练习会话不可重复提交")

        question = self._load_question_for_user(db, user_id, session.question_id)
        answers = self._load_session_answers(session)
        answer_content = self._compose_answer_content_from_session(question, answers)
        if not answer_content.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="练习内容为空，无法提交")

        execution = self.review_answer_from_content(
            db,
            user_id=user_id,
            question_id=question.id,
            answer_content=answer_content,
            answer_id=session.answer_id,
            reference_points=reference_points,
            use_llm=use_llm,
        )
        update_practice_session_record(
            db,
            session,
            answer_id=execution.answer_id,
            status="completed",
            submitted_at=datetime.now(timezone.utc),
        )
        db.commit()
        db.refresh(session)
        return PracticeSessionSubmitResponse(
            session_id=session.id,
            answer_id=execution.answer_id,
            review_id=execution.review_id,
            status=session.status,
            analysis=execution.analysis,
        )

    def list_practice_records(
        self,
        db: Session,
        *,
        current_user_id: int,
        page: int = 1,
        page_size: int = 20,
        paper_id: int | None = None,
        question_id: int | None = None,
        question_type: str | None = None,
        answer_version_no: int | None = None,
        status_value: str | None = None,
        review_id: int | None = None,
        score_min: int | None = None,
        score_max: int | None = None,
        model_provider: str | None = None,
        model_name: str | None = None,
        is_favorite: bool | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> PracticeRecordListResponse:
        created_from = datetime.combine(date_from, time.min) if date_from is not None else None
        created_to = datetime.combine(date_to, time.max) if date_to is not None else None
        items, total = list_practice_records_repo(
            db,
            user_id=current_user_id,
            paper_id=paper_id,
            question_id=question_id,
            question_type=question_type,
            answer_version_no=answer_version_no,
            status=status_value,
            review_id=review_id,
            score_min=score_min,
            score_max=score_max,
            model_provider=model_provider,
            model_name=model_name,
            is_favorite=is_favorite,
            created_from=created_from,
            created_to=created_to,
            page=page,
            page_size=page_size,
        )
        return PracticeRecordListResponse(
            items=[self._to_practice_record_list_item(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_practice_record_detail(
        self,
        db: Session,
        *,
        current_user_id: int,
        record_id: int,
    ) -> PracticeRecordDetail:
        record = get_practice_record(db, record_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="练习记录不存在")
        if record.user_id != current_user_id and not self._is_admin(db, current_user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该练习记录")
        return self._to_practice_record_detail(record)

    def update_practice_record_favorite(
        self,
        db: Session,
        *,
        current_user_id: int,
        record_id: int,
        is_favorite: bool,
    ) -> PracticeRecordDetail:
        record = get_practice_record(db, record_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="练习记录不存在")
        if record.user_id != current_user_id and not self._is_admin(db, current_user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改该练习记录")
        update_practice_record(db, record, is_favorite=is_favorite)
        db.commit()
        db.refresh(record)
        return self._to_practice_record_detail(record)

    def review_answer(
        self,
        db: Session,
        *,
        user_id: int,
        question_id: int,
        answer_id: int,
        reference_points: list[str] | None = None,
        use_llm: bool = True,
    ) -> ReviewAnalysis:
        return self._execute_review(
            db,
            user_id=user_id,
            question_id=question_id,
            answer_id=answer_id,
            reference_points=reference_points,
            use_llm=use_llm,
        ).analysis

    def review_answer_from_content(
        self,
        db: Session,
        *,
        user_id: int,
        question_id: int,
        answer_content: str,
        answer_id: int | None = None,
        reference_points: list[str] | None = None,
        use_llm: bool = True,
    ) -> ReviewExecutionResponse:
        question = self._load_question_for_user(db, user_id, question_id)

        if answer_id is None:
            answer = self._create_answer_version(db, user_id=user_id, question_id=question.id, content=answer_content)
        else:
            answer = self._load_answer_for_user(db, user_id, answer_id)
            if answer.question_id != question.id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="答案不属于该题目")
            if get_review_by_answer_id(db, answer.id) is None:
                update_answer_record(db, answer, content=answer_content)
            else:
                answer = self._create_answer_version(db, user_id=user_id, question_id=question.id, content=answer_content)

        return self._execute_review(
            db,
            user_id=user_id,
            question_id=question.id,
            answer_id=answer.id,
            reference_points=reference_points,
            use_llm=use_llm,
        )

    def analyze_question(
        self,
        db: Session,
        *,
        user_id: int,
        question_id: int,
        reference_points: list[str] | None = None,
        use_llm: bool = True,
    ) -> QuestionAnalysisResponse:
        if self.fallback_config is None:
            self.fallback_config = load_practice_fallback_config(db)
        question = self._load_question_for_user(db, user_id, question_id)
        llm_config = self._build_llm_config(db, user_id) if use_llm else None
        analysis = self._analyze_question_core(question, reference_points or [], llm_config)
        return QuestionAnalysisResponse(question_id=question.id, question_title=question.title, analysis=analysis)

    def generate_outline(
        self,
        db: Session,
        *,
        user_id: int,
        question_id: int,
        reference_points: list[str] | None = None,
        use_llm: bool = True,
    ) -> OutlineResponse:
        if self.fallback_config is None:
            self.fallback_config = load_practice_fallback_config(db)
        question = self._load_question_for_user(db, user_id, question_id)
        llm_config = self._build_llm_config(db, user_id) if use_llm else None
        question_analysis = self._analyze_question_core(question, reference_points or [], llm_config)
        comparison = PointComparisonResult(
            matched_points=[],
            partial_points=[],
            missing_points=list(reference_points or []),
            extra_points=[],
            coverage_rate=0.0,
            note="仅基于题目生成提纲",
        )
        outline = self._generate_outline_core(question_analysis, comparison, llm_config)
        return OutlineResponse(question_id=question.id, question_title=question.title, analysis=question_analysis, outline=outline)

    def _execute_review(
        self,
        db: Session,
        *,
        user_id: int,
        question_id: int,
        answer_id: int,
        reference_points: list[str] | None = None,
        use_llm: bool = True,
    ) -> ReviewExecutionResponse:
        question = get_question(db, question_id)
        if question is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")

        answer = get_answer(db, answer_id)
        if answer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="答案不存在")

        if answer.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="不能批改他人的答案")
        if answer.question_id != question_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="答案不属于该题目")

        llm_config = self._build_llm_config(db, user_id) if use_llm else None
        if llm_config is None and self.review_service.llm_config is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="批改模型未配置，当前不支持非 LLM 批改",
            )

        request = self._build_review_request(question, answer, reference_points)
        review_service = self._build_review_service(db, llm_config)
        review_result = review_service.review(request)

        review = self._upsert_review(
            db=db,
            question=question,
            answer=answer,
            analysis=review_result.analysis,
            reference_points=request.reference_points,
            llm_config=llm_config,
        )
        self._save_review_steps(db, review.id, review_result.steps)
        self._upsert_practice_record(
            db,
            user_id=user_id,
            question_id=question.id,
            answer_id=answer.id,
            review_id=review.id,
        )
        db.commit()
        return ReviewExecutionResponse(answer_id=answer.id, review_id=review.id, analysis=review_result.analysis)

    def _build_review_request(self, question: Question, answer: Answer, reference_points: list[str] | None) -> ReviewRequest:
        return ReviewRequest(
            question_title=question.title,
            question_content=question.content,
            answer_content=answer.content,
            question_type=question.question_type,
            reference_points=reference_points or [],
        )

    def _load_question_for_user(self, db: Session, user_id: int, question_id: int) -> Question:
        question = get_question(db, question_id)
        if question is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")
        # 系统题库所有人可访问；个人题库只有本人和管理员可访问
        if question.scope != "system" and question.user_id != user_id and not self._is_admin(db, user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该题目")
        return question

    def _load_answer_for_user(self, db: Session, user_id: int, answer_id: int) -> Answer:
        answer = get_answer(db, answer_id)
        if answer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="答案不存在")
        if answer.user_id != user_id and not self._is_admin(db, user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该答案")
        return answer

    def _load_practice_session_for_user(self, db: Session, user_id: int, session_id: int) -> PracticeSession:
        session = get_practice_session(db, session_id)
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="练习会话不存在")
        if session.user_id != user_id and not self._is_admin(db, user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该练习会话")
        return session

    def _load_session_answers(self, session: PracticeSession) -> dict[str, str]:
        try:
            loaded = json.loads(session.answers_json or "{}")
            if isinstance(loaded, dict):
                return {str(key): str(value or "") for key, value in loaded.items()}
        except Exception:
            pass
        return {}

    def _get_question_answer_sections(self, question: Question) -> list[dict]:
        try:
            loaded = json.loads(question.answer_sections_json or "[]")
            if isinstance(loaded, list):
                return [item for item in loaded if isinstance(item, dict)]
        except Exception:
            pass
        return []

    def _build_empty_session_answers(self, question: Question) -> dict[str, str]:
        sections = self._get_question_answer_sections(question)
        if not sections:
            return {}
        answers: dict[str, str] = {}
        for section in sections:
            section_id = str(section.get("id") or "").strip()
            if section_id:
                answers[section_id] = ""
        return answers

    def _compose_answer_content_from_session(self, question: Question, answers: dict[str, str]) -> str:
        sections = self._get_question_answer_sections(question)
        if not sections:
            return "\n\n".join(value.strip() for value in answers.values() if value and value.strip())

        blocks: list[str] = []
        for section in sections:
            section_id = str(section.get("id") or "").strip()
            if not section_id:
                continue
            content = (answers.get(section_id) or "").strip()
            if not content:
                continue
            title = str(section.get("title") or "").strip()
            if title:
                blocks.append(f"{title}\n{content}")
            else:
                blocks.append(content)
        return "\n\n".join(blocks)

    def _create_answer_version(self, db: Session, *, user_id: int, question_id: int, content: str) -> Answer:
        latest_version = get_latest_answer_version_no(db, user_id=user_id, question_id=question_id)
        return create_answer_record(
            db,
            Answer(
                user_id=user_id,
                question_id=question_id,
                content=content,
                version_no=latest_version + 1,
            ),
        )

    def _is_admin(self, db: Session, user_id: int) -> bool:
        return "admin" in get_user_role_names(db, user_id)

    def _analyze_question_core(
        self,
        question: Question,
        reference_points: list[str],
        llm_config: ReviewLLMConfig | None,
    ) -> QuestionAnalysisResult:
        request = ReviewRequest(
            question_title=question.title,
            question_content=question.content,
            answer_content="占位",
            question_type=question.question_type,
            reference_points=reference_points,
        )
        if llm_config is not None:
            try:
                return QuestionAnalyzerAgent(llm_config).analyze(request)
            except Exception:
                pass
        return self._fallback_question_analysis(question, reference_points)

    def _fallback_question_analysis(self, question: Question, reference_points: list[str]) -> QuestionAnalysisResult:
        fallback_config = self.fallback_config
        question_type = question.question_type or self._infer_question_type(question.title + " " + question.content)
        scoring_focus = [item for item in reference_points[:4]]
        key_topics = self._extract_keywords(question.title + " " + question.content)
        structure_hint = (
            list(fallback_config.structured_hints)
            if question_type in set(fallback_config.structured_question_types)
            else list(fallback_config.default_hints)
        )
        note = f"基于题干关键词识别到题型为：{question_type or '未识别'}"
        return QuestionAnalysisResult(
            question_type=question_type,
            task_requirements=[question.title, *reference_points[:3]],
            scoring_focus=scoring_focus or key_topics[:4],
            constraints=["围绕题干要求作答"],
            key_topics=key_topics[:6],
            structure_hint=structure_hint,
            note=note,
        )

    def _generate_outline_core(
        self,
        question_analysis: QuestionAnalysisResult,
        comparison: PointComparisonResult,
        llm_config: ReviewLLMConfig | None,
    ) -> str:
        if llm_config is not None:
            try:
                return OutlineGeneratorAgent(llm_config).generate(question_analysis, comparison)
            except Exception:
                pass
        return self._fallback_outline(question_analysis, comparison)

    def _fallback_outline(self, question_analysis: QuestionAnalysisResult, comparison: PointComparisonResult) -> str:
        sections = [
            f"题型：{question_analysis.question_type or '未识别'}",
            f"核心要求：{'；'.join(question_analysis.task_requirements[:3]) or '围绕题干展开'}",
            f"评分重点：{'；'.join(question_analysis.scoring_focus[:4]) or '围绕材料与题干回应'}",
            f"结构提示：{'；'.join(question_analysis.structure_hint[:3]) or '总分总'}",
        ]
        if comparison.missing_points:
            sections.append(f"需覆盖要点：{'；'.join(comparison.missing_points[:4])}")
        return "\n".join(sections)

    def _infer_question_type(self, text: str) -> str | None:
        for key, value in self.fallback_config.question_type_mapping:
            if key in text:
                return value
        return None

    def _extract_keywords(self, text: str) -> list[str]:
        tokens = []
        for item in text.replace("，", " ").replace("。", " ").split():
            token = item.strip()
            if len(token) >= 2 and token not in tokens:
                tokens.append(token)
        return tokens[:10]

    def _build_llm_config(self, db: Session, user_id: int) -> ReviewLLMConfig | None:
        config = get_effective_review_config(db, user_id)
        if config is None:
            return None

        return ReviewLLMConfig(
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

    def _build_review_service(self, db: Session, llm_config: ReviewLLMConfig | None) -> ReviewService:
        # review_service 若为外部注入测试替身，则直接复用
        if not isinstance(self.review_service, ReviewService):
            return self.review_service
        if llm_config is not None:
            return ReviewService(
                llm_config,
                point_compare_config=load_point_compare_config(db),
                structure_config=load_structure_analysis_config(db),
                language_config=load_language_analysis_config(db),
            )
        return self.review_service

    def _upsert_review(
        self,
        *,
        db: Session,
        question: Question,
        answer: Answer,
        analysis: ReviewAnalysis,
        reference_points: list[str],
        llm_config: ReviewLLMConfig | None,
    ) -> Review:
        existing_review = get_review_by_answer_id(db, answer.id)
        review_payload = self._build_review_payload(
            question=question,
            answer=answer,
            analysis=analysis,
            reference_points=reference_points,
            llm_config=llm_config,
        )
        if existing_review is None:
            return create_review(db, review_data=review_payload)

        review = update_review(db, existing_review, review_payload)
        delete_review_steps(db, review.id)
        return review

    def _build_review_payload(
        self,
        *,
        question: Question,
        answer: Answer,
        analysis: ReviewAnalysis,
        reference_points: list[str],
        llm_config: ReviewLLMConfig | None,
    ) -> dict:
        return {
            "answer_id": answer.id,
            "question_id": question.id,
            "user_id": answer.user_id,
            "question_title_snapshot": question.title,
            "question_type_snapshot": analysis.question_type or question.question_type,
            "question_content_snapshot": question.content,
            "answer_content_snapshot": answer.content,
            "reference_points_json": json.dumps(reference_points, ensure_ascii=False),
            "question_analysis_json": json.dumps(analysis.question_analysis or {}, ensure_ascii=False),
            "reference_point_analysis_json": json.dumps(analysis.reference_point_analysis, ensure_ascii=False),
            "user_point_analysis_json": json.dumps(analysis.user_point_analysis, ensure_ascii=False),
            "comparison_json": json.dumps(analysis.comparison_analysis or {}, ensure_ascii=False),
            "structure_analysis_json": json.dumps(analysis.structure_analysis or {}, ensure_ascii=False),
            "language_analysis_json": json.dumps(analysis.language_analysis or {}, ensure_ascii=False),
            "rule_analysis_json": json.dumps(analysis.rule_analysis or {}, ensure_ascii=False),
            "score_breakdown_json": json.dumps(analysis.score_breakdown, ensure_ascii=False),
            "report_json": json.dumps(analysis.report_json or {}, ensure_ascii=False),
            "model_provider": llm_config.provider if llm_config else None,
            "model_name": llm_config.model_name if llm_config else None,
            "score": analysis.score,
            "strengths": "\n".join(analysis.strengths) if analysis.strengths else None,
            "issues": "\n".join(analysis.issues) if analysis.issues else None,
            "suggestions": "\n".join(analysis.suggestions) if analysis.suggestions else None,
            "summary": analysis.summary,
        }

    def _save_review_steps(self, db: Session, review_id: int, steps: list) -> None:
        for step in steps:
            create_review_step(
                db,
                ReviewStepModel(
                    review_id=review_id,
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

    def _upsert_practice_record(
        self,
        db: Session,
        *,
        user_id: int,
        question_id: int,
        answer_id: int,
        review_id: int,
    ) -> PracticeRecord:
        existing_record = get_practice_record_by_answer_id(db, answer_id)
        if existing_record is not None:
            return update_practice_record(db, existing_record, review_id=review_id, status="finished")
        return create_practice_record(
            db,
            user_id=user_id,
            question_id=question_id,
            answer_id=answer_id,
            review_id=review_id,
        )

    def _to_answer_read(
        self,
        answer: Answer,
        *,
        question: Question | None = None,
        review: Review | None = None,
    ) -> AnswerRead:
        related_question = question or answer.question
        related_review = review if review is not None else (answer.reviews[-1] if answer.reviews else None)

        return AnswerRead(
            id=answer.id,
            question_id=answer.question_id,
            user_id=answer.user_id,
            content=answer.content,
            version_no=answer.version_no,
            created_at=answer.created_at,
            question_title=related_question.title if related_question else None,
            question_type=related_question.question_type if related_question else None,
            reviewed=related_review is not None,
            review_id=related_review.id if related_review is not None else None,
        )

    def _to_practice_session_read(self, session: PracticeSession) -> PracticeSessionRead:
        return PracticeSessionRead(
            id=session.id,
            user_id=session.user_id,
            question_id=session.question_id,
            answer_id=session.answer_id,
            status=session.status,
            answers=self._load_session_answers(session),
            elapsed_seconds=session.elapsed_seconds or 0,
            started_at=session.started_at,
            submitted_at=session.submitted_at,
            updated_at=session.updated_at,
        )

    def _to_practice_record_list_item(self, record: PracticeRecord) -> PracticeRecordListItem:
        question = record.question
        answer = record.answer
        review = record.review
        return PracticeRecordListItem(
            id=record.id,
            user_id=record.user_id,
            question_id=record.question_id,
            answer_id=record.answer_id,
            review_id=record.review_id,
            status=record.status,
            is_favorite=record.is_favorite,
            created_at=record.created_at,
            question_title=question.title if question else "",
            question_type=question.question_type if question else None,
            answer_version_no=answer.version_no if answer else 1,
            score=review.score if review else None,
            summary=review.summary if review else None,
            model_provider=review.model_provider if review else None,
            model_name=review.model_name if review else None,
        )

    def _to_practice_record_detail(self, record: PracticeRecord) -> PracticeRecordDetail:
        item = self._to_practice_record_list_item(record)
        question = record.question
        answer = record.answer
        review = record.review
        return PracticeRecordDetail(
            **item.model_dump(),
            question_content=question.content if question else "",
            answer_content=answer.content if answer else "",
            review_created_at=review.created_at if review else None,
        )


def create_answer_draft(
    db: Session,
    *,
    user_id: int,
    question_id: int,
    content: str,
) -> AnswerRead:
    return PracticeService().create_answer(db, user_id=user_id, question_id=question_id, content=content)


def update_answer_draft(
    db: Session,
    *,
    user_id: int,
    answer_id: int,
    content: str,
) -> AnswerRead:
    return PracticeService().update_answer(db, user_id=user_id, answer_id=answer_id, content=content)


def get_answer_detail(
    db: Session,
    *,
    user_id: int,
    answer_id: int,
) -> AnswerRead:
    return PracticeService().get_answer_detail(db, user_id=user_id, answer_id=answer_id)


def duplicate_answer(
    db: Session,
    *,
    user_id: int,
    answer_id: int,
    content: str | None = None,
) -> AnswerRead:
    return PracticeService().duplicate_answer(db, user_id=user_id, answer_id=answer_id, content=content)


def list_question_answers(
    db: Session,
    *,
    user_id: int,
    question_id: int,
    page: int = 1,
    page_size: int = 20,
) -> AnswerListResponse:
    return PracticeService().list_question_answers(
        db,
        user_id=user_id,
        question_id=question_id,
        page=page,
        page_size=page_size,
    )


def get_current_practice_session(
    db: Session,
    *,
    user_id: int,
    question_id: int,
) -> PracticeSessionRead | None:
    return PracticeService().get_current_practice_session(db, user_id=user_id, question_id=question_id)


def create_practice_session(
    db: Session,
    *,
    user_id: int,
    question_id: int,
) -> PracticeSessionRead:
    return PracticeService().create_practice_session(db, user_id=user_id, question_id=question_id)


def update_practice_session(
    db: Session,
    *,
    user_id: int,
    session_id: int,
    answers: dict[str, str],
    elapsed_seconds: int | None = None,
) -> PracticeSessionRead:
    return PracticeService().update_practice_session(
        db,
        user_id=user_id,
        session_id=session_id,
        answers=answers,
        elapsed_seconds=elapsed_seconds,
    )


def submit_practice_session(
    db: Session,
    *,
    user_id: int,
    session_id: int,
    reference_points: list[str] | None = None,
    use_llm: bool = True,
) -> PracticeSessionSubmitResponse:
    return PracticeService().submit_practice_session(
        db,
        user_id=user_id,
        session_id=session_id,
        reference_points=reference_points,
        use_llm=use_llm,
    )


def list_practice_records(
    db: Session,
    *,
    current_user_id: int,
    page: int = 1,
    page_size: int = 20,
    paper_id: int | None = None,
    question_id: int | None = None,
    question_type: str | None = None,
    answer_version_no: int | None = None,
    status_value: str | None = None,
    review_id: int | None = None,
    score_min: int | None = None,
    score_max: int | None = None,
    model_provider: str | None = None,
    model_name: str | None = None,
    is_favorite: bool | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> PracticeRecordListResponse:
    return PracticeService().list_practice_records(
        db,
        current_user_id=current_user_id,
        page=page,
        page_size=page_size,
        paper_id=paper_id,
        question_id=question_id,
        question_type=question_type,
        answer_version_no=answer_version_no,
        status_value=status_value,
        review_id=review_id,
        score_min=score_min,
        score_max=score_max,
        model_provider=model_provider,
        model_name=model_name,
        is_favorite=is_favorite,
        date_from=date_from,
        date_to=date_to,
    )


def get_practice_record_detail(
    db: Session,
    *,
    current_user_id: int,
    record_id: int,
) -> PracticeRecordDetail:
    return PracticeService().get_practice_record_detail(db, current_user_id=current_user_id, record_id=record_id)


def update_practice_record_favorite(
    db: Session,
    *,
    current_user_id: int,
    record_id: int,
    is_favorite: bool,
) -> PracticeRecordDetail:
    return PracticeService().update_practice_record_favorite(
        db,
        current_user_id=current_user_id,
        record_id=record_id,
        is_favorite=is_favorite,
    )


def review_answer(
    db: Session,
    *,
    user_id: int,
    question_id: int,
    answer_id: int,
    reference_points: list[str] | None = None,
    use_llm: bool = True,
) -> ReviewAnalysis:
    return PracticeService().review_answer(
        db,
        user_id=user_id,
        question_id=question_id,
        answer_id=answer_id,
        reference_points=reference_points,
        use_llm=use_llm,
    )


def review_answer_from_content(
    db: Session,
    *,
    user_id: int,
    question_id: int,
    answer_content: str,
    answer_id: int | None = None,
    reference_points: list[str] | None = None,
    use_llm: bool = True,
) -> ReviewExecutionResponse:
    return PracticeService().review_answer_from_content(
        db,
        user_id=user_id,
        question_id=question_id,
        answer_content=answer_content,
        answer_id=answer_id,
        reference_points=reference_points,
        use_llm=use_llm,
    )


def analyze_question(
    db: Session,
    *,
    user_id: int,
    question_id: int,
    reference_points: list[str] | None = None,
    use_llm: bool = True,
) -> QuestionAnalysisResponse:
    return PracticeService().analyze_question(
        db,
        user_id=user_id,
        question_id=question_id,
        reference_points=reference_points,
        use_llm=use_llm,
    )


def generate_outline(
    db: Session,
    *,
    user_id: int,
    question_id: int,
    reference_points: list[str] | None = None,
    use_llm: bool = True,
) -> OutlineResponse:
    return PracticeService().generate_outline(
        db,
        user_id=user_id,
        question_id=question_id,
        reference_points=reference_points,
        use_llm=use_llm,
    )


def submit_paper_answers(
    db: Session,
    user,
    paper,
    session,
) -> dict:
    """提交整套试卷：为每道题创建答案，触发批改，生成练习记录。"""
    from app.modules.practice.models import Answer
    from app.modules.review.models import Review
    from app.modules.practice.repository import (
        create_answer as create_answer_record,
        create_practice_record,
        create_review,
        get_latest_answer_version_no,
    )

    answers_data = json.loads(session.answers_json) if session.answers_json else {}
    results = []

    for question in paper.questions:
        question_id = question.id
        answer_content = answers_data.get(str(question_id), "")

        if not answer_content or not answer_content.strip():
            continue

        # 创建答案记录
        version_no = get_latest_answer_version_no(db, user_id=user.id, question_id=question_id) or 0
        answer = Answer(
            user_id=user.id,
            question_id=question_id,
            paper_id=paper.id,
            content=answer_content,
            version_no=version_no + 1,
        )
        answer = create_answer_record(db, answer)

        # 创建批改记录（简化版，后续可接入 AI）
        review = create_review(
            db,
            review_data={
                "answer_id": answer.id,
                "question_id": question_id,
                "user_id": user.id,
                "paper_id": paper.id,
                "question_title_snapshot": question.title or "",
                "question_type_snapshot": question.question_type or "",
                "question_content_snapshot": question.content or "",
                "answer_content_snapshot": answer_content,
                "reference_points_json": "{}",
                "question_analysis_json": "{}",
                "reference_point_analysis_json": "{}",
                "user_point_analysis_json": "{}",
                "comparison_json": "{}",
                "structure_analysis_json": "{}",
                "language_analysis_json": "{}",
                "rule_analysis_json": "{}",
                "score_breakdown_json": "{}",
                "report_json": "{}",
            },
        )

        # 创建练习记录
        practice_record = create_practice_record(
            db,
            user_id=user.id,
            paper_id=paper.id,
            question_id=question_id,
            answer_id=answer.id,
            review_id=review.id,
        )

        results.append({
            "question_id": question_id,
            "answer_id": answer.id,
            "review_id": review.id,
            "practice_record_id": practice_record.id,
        })

    # 更新会话状态
    session.status = "submitted"
    db.flush()

    return {
        "paper_id": paper.id,
        "submitted_count": len(results),
        "details": results,
    }
