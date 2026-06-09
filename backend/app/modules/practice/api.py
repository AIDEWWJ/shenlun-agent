from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.response import api_success
from app.modules.auth.models import User
from app.modules.practice.schemas import (
	AnswerCreateRequest,
	AnswerDuplicateRequest,
	AnswerUpdateRequest,
	PracticeRecordFavoriteUpdateRequest,
	PracticeSessionCreateRequest,
	PracticeSessionSubmitRequest,
	PracticeSessionUpdateRequest,
	QuestionWorkRequest,
	ReviewCreateRequest,
	ReviewFromContentRequest,
)
from app.modules.practice.service import (
	analyze_question as analyze_question_service,
	create_answer_draft as create_answer_draft_service,
	create_practice_session as create_practice_session_service,
	duplicate_answer as duplicate_answer_service,
	generate_outline as generate_outline_service,
	get_answer_detail as get_answer_detail_service,
	get_current_practice_session as get_current_practice_session_service,
	get_practice_record_detail as get_practice_record_detail_service,
	list_practice_records as list_practice_records_service,
	list_question_answers as list_question_answers_service,
	review_answer as review_answer_service,
	review_answer_from_content as review_answer_from_content_service,
	submit_practice_session as submit_practice_session_service,
	update_answer_draft as update_answer_draft_service,
	update_practice_record_favorite as update_practice_record_favorite_service,
	update_practice_session as update_practice_session_service,
)
from app.shared.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.shared.deps import get_current_active_user, get_db
from app.shared.schemas import ApiResponse


router = APIRouter(tags=["用户-练习与批改"])


@router.post("/answers", response_model=ApiResponse, status_code=status.HTTP_201_CREATED, summary="创建答案版本")
def create_answer(
	data: AnswerCreateRequest,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	result = create_answer_draft_service(
		db,
		user_id=current_user.id,
		question_id=data.question_id,
		content=data.content,
	)
	return api_success(result, message="创建答案成功")


@router.get("/questions/{question_id}/answers", response_model=ApiResponse, summary="查询题目答案版本列表")
def list_answers(
	question_id: int,
	page: int = Query(default=DEFAULT_PAGE, ge=1),
	page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	result = list_question_answers_service(
		db,
		user_id=current_user.id,
		question_id=question_id,
		page=page,
		page_size=page_size,
	)
	return api_success(result, message="获取答案列表成功")


@router.get("/answers/{answer_id}", response_model=ApiResponse, summary="获取答案详情")
def get_answer(
	answer_id: int,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	result = get_answer_detail_service(db, user_id=current_user.id, answer_id=answer_id)
	return api_success(result, message="获取答案详情成功")


@router.put("/answers/{answer_id}", response_model=ApiResponse, summary="更新未批改答案")
def update_answer(
	answer_id: int,
	data: AnswerUpdateRequest,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	result = update_answer_draft_service(db, user_id=current_user.id, answer_id=answer_id, content=data.content)
	return api_success(result, message="更新答案成功")


@router.post("/answers/{answer_id}/duplicate", response_model=ApiResponse, status_code=status.HTTP_201_CREATED, summary="复制答案版本")
def duplicate_answer(
	answer_id: int,
	data: AnswerDuplicateRequest | None = None,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	"""基于旧答案创建新版本，可选传入修改后的内容。"""
	content = data.content if data else None
	result = duplicate_answer_service(db, user_id=current_user.id, answer_id=answer_id, content=content)
	return api_success(result, message="复制答案成功")


@router.get("/practice-sessions/current", response_model=ApiResponse, summary="获取当前题目的可继续练习会话")
def get_current_practice_session(
	question_id: int = Query(ge=1),
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	result = get_current_practice_session_service(db, user_id=current_user.id, question_id=question_id)
	return api_success(result, message="获取练习会话成功")


@router.post("/practice-sessions", response_model=ApiResponse, status_code=status.HTTP_201_CREATED, summary="创建练习会话")
def create_practice_session(
	data: PracticeSessionCreateRequest,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	result = create_practice_session_service(db, user_id=current_user.id, question_id=data.question_id)
	return api_success(result, message="创建练习会话成功")


@router.patch("/practice-sessions/{session_id}", response_model=ApiResponse, summary="更新练习会话草稿")
def update_practice_session(
	session_id: int,
	data: PracticeSessionUpdateRequest,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	result = update_practice_session_service(
		db,
		user_id=current_user.id,
		session_id=session_id,
		answers=data.answers,
		elapsed_seconds=data.elapsed_seconds,
	)
	return api_success(result, message="保存练习草稿成功")


@router.post("/practice-sessions/{session_id}/submit", response_model=ApiResponse, summary="提交练习会话并发起批改")
def submit_practice_session(
	session_id: int,
	data: PracticeSessionSubmitRequest,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	result = submit_practice_session_service(
		db,
		user_id=current_user.id,
		session_id=session_id,
		reference_points=data.reference_points,
		use_llm=data.use_llm,
	)
	return api_success(result, message="提交练习并完成批改")


@router.post("/analyze", response_model=ApiResponse, summary="分析题目")
def analyze_question(
	data: QuestionWorkRequest,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	result = analyze_question_service(
		db,
		user_id=current_user.id,
		question_id=data.question_id,
		reference_points=data.reference_points,
		use_llm=data.use_llm,
	)
	return api_success(result, message="分析完成")


@router.post("/outline", response_model=ApiResponse, summary="生成作答提纲")
def generate_outline(
	data: QuestionWorkRequest,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	result = generate_outline_service(
		db,
		user_id=current_user.id,
		question_id=data.question_id,
		reference_points=data.reference_points,
		use_llm=data.use_llm,
	)
	return api_success(result, message="提纲生成完成")


@router.post("/review/from-content", response_model=ApiResponse, summary="基于答案正文直接批改")
def review_answer_from_content(
	data: ReviewFromContentRequest,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	result = review_answer_from_content_service(
		db,
		user_id=current_user.id,
		question_id=data.question_id,
		answer_content=data.answer_content,
		answer_id=data.answer_id,
		reference_points=data.reference_points,
		use_llm=data.use_llm,
	)
	return api_success(result, message="批改完成")


@router.post("/review", response_model=ApiResponse, summary="按答案版本发起批改")
def review_answer(
	data: ReviewCreateRequest,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	result = review_answer_service(
		db,
		user_id=current_user.id,
		question_id=data.question_id,
		answer_id=data.answer_id,
		reference_points=data.reference_points,
		use_llm=data.use_llm,
	)
	return api_success(result, message="批改完成")


@router.get("/practice-records", response_model=ApiResponse, summary="分页查询练习记录")
def list_practice_records(
	page: int = Query(default=DEFAULT_PAGE, ge=1),
	page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
	paper_id: int | None = Query(default=None, ge=1),
	question_id: int | None = Query(default=None, ge=1),
	question_type: str | None = Query(default=None),
	answer_version_no: int | None = Query(default=None, ge=1),
	status_value: str | None = Query(default=None, alias="status"),
	review_id: int | None = Query(default=None, ge=1),
	score_min: int | None = Query(default=None, ge=0, le=100),
	score_max: int | None = Query(default=None, ge=0, le=100),
	model_provider: str | None = Query(default=None),
	model_name: str | None = Query(default=None),
	is_favorite: bool | None = Query(default=None),
	date_from: date | None = Query(default=None),
	date_to: date | None = Query(default=None),
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	result = list_practice_records_service(
		db,
		current_user_id=current_user.id,
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
	return api_success(result, message="获取练习记录成功")


@router.get("/practice-records/{record_id}", response_model=ApiResponse, summary="获取练习记录详情")
def get_practice_record(
	record_id: int,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	result = get_practice_record_detail_service(db, current_user_id=current_user.id, record_id=record_id)
	return api_success(result, message="获取练习记录详情成功")


@router.patch("/practice-records/{record_id}/favorite", response_model=ApiResponse, summary="更新练习记录收藏状态")
def update_practice_record_favorite(
	record_id: int,
	data: PracticeRecordFavoriteUpdateRequest,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	result = update_practice_record_favorite_service(
		db,
		current_user_id=current_user.id,
		record_id=record_id,
		is_favorite=data.is_favorite,
	)
	return api_success(result, message="更新练习收藏状态成功")


# ========== 整套试卷练习会话 ==========

@router.get("/paper-sessions/{paper_id}", response_model=ApiResponse, summary="获取试卷练习会话")
def get_paper_session(
	paper_id: int,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	"""获取用户在某套试卷上的练习会话。"""
	from app.modules.practice.repository import get_paper_practice_session
	session = get_paper_practice_session(db, current_user.id, paper_id)
	if not session:
		return api_success(None, message="无历史会话")
	import json
	return api_success({
		"id": session.id,
		"paper_id": session.paper_id,
		"answers": json.loads(session.answers_json) if session.answers_json else {},
		"current_index": session.current_index,
		"timer_seconds": session.timer_seconds,
		"status": session.status,
	}, message="获取会话成功")


@router.post("/paper-sessions/{paper_id}", response_model=ApiResponse, summary="保存试卷练习会话")
def save_paper_session(
	paper_id: int,
	body: dict,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	"""保存或更新试卷练习会话。"""
	import json
	from app.modules.practice.repository import upsert_paper_practice_session
	session = upsert_paper_practice_session(
		db, current_user.id, paper_id,
		answers_json=json.dumps(body.get("answers", {}), ensure_ascii=False),
		current_index=body.get("current_index", 0),
		timer_seconds=body.get("timer_seconds", 0),
		status=body.get("status", "drafting"),
	)
	db.commit()
	return api_success({"id": session.id}, message="保存成功")


@router.delete("/paper-sessions/{paper_id}", response_model=ApiResponse, summary="删除试卷练习会话")
def delete_paper_session(
	paper_id: int,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	"""删除试卷练习会话（重新开始时调用）。"""
	from app.modules.practice.repository import delete_paper_practice_session
	delete_paper_practice_session(db, current_user.id, paper_id)
	db.commit()
	return api_success(message="已删除")


@router.post("/paper-sessions/{paper_id}/submit", response_model=ApiResponse, summary="提交整套试卷并触发批改")
def submit_paper_session(
	paper_id: int,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	"""提交整套试卷：为每道题创建答案，触发批改，生成练习记录。"""
	from app.modules.paper.repository import get_paper
	from app.modules.practice.repository import get_paper_practice_session, create_answer
	from app.modules.practice.service import submit_paper_answers

	# 获取试卷
	paper = get_paper(db, paper_id)
	if not paper:
		return api_success(None, message="试卷不存在", code=404)

	# 获取练习会话
	session = get_paper_practice_session(db, current_user.id, paper_id)
	if not session:
		return api_success(None, message="无练习会话", code=404)

	# 提交
	result = submit_paper_answers(db, current_user, paper, session)
	db.commit()

	return api_success(result, message="试卷提交成功")
