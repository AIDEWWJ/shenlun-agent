from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import api_success
from app.modules.auth.models import User
from app.shared.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.modules.review.schemas import ReviewQARequest, ReviewRerunRequest
from app.modules.review.service import answer_review_question, get_review_detail, list_my_reviews, list_review_qa_messages, rerun_review
from app.shared.deps import get_current_active_user, get_db
from app.shared.schemas import ApiResponse


router = APIRouter(prefix="/reviews", tags=["用户-批改记录与答疑"])


@router.get("", response_model=ApiResponse, summary="分页查询批改记录")
def list_reviews(
	page: int = Query(default=DEFAULT_PAGE, ge=1),
	page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
	question_id: int | None = Query(default=None, ge=1),
	question_type: str | None = Query(default=None),
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	"""按题目和题型等条件分页查询当前用户的批改记录。"""
	return api_success(
		list_my_reviews(
			db,
			current_user_id=current_user.id,
			page=page,
			page_size=page_size,
			question_id=question_id,
			question_type=question_type,
		),
		message="获取批改记录成功",
	)


@router.get("/{review_id}", response_model=ApiResponse, summary="获取批改详情")
def get_review(review_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
	"""获取单次批改的完整结果、证据和步骤信息。"""
	return api_success(get_review_detail(db, review_id=review_id, current_user_id=current_user.id), message="获取批改详情成功")


@router.post("/{review_id}/rerun", response_model=ApiResponse, summary="重新批改")
def rerun(
	review_id: int,
	data: ReviewRerunRequest,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	"""对同一答案重新发起批改，可更换参考要点或模型配置。"""
	return api_success(
		rerun_review(
			db,
			review_id=review_id,
			current_user_id=current_user.id,
			reference_points=data.reference_points,
			use_llm=data.use_llm,
		),
		message="重新批改完成",
	)


@router.post("/{review_id}/qa", response_model=ApiResponse, summary="发起批改答疑")
def review_qa(
	review_id: int,
	data: ReviewQARequest,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	"""围绕某次批改结果发起追问，支持连续追问同一会话。"""
	return api_success(
		answer_review_question(
			db,
			review_id=review_id,
			current_user_id=current_user.id,
			question=data.question,
			use_llm=data.use_llm,
			conversation_id=data.conversation_id,
			parent_message_id=data.parent_message_id,
		),
		message="答疑完成",
	)


@router.get("/{review_id}/qa", response_model=ApiResponse, summary="查询批改答疑记录")
def list_review_qa(
	review_id: int,
	conversation_id: str | None = Query(default=None),
	page: int = Query(default=DEFAULT_PAGE, ge=1),
	page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	"""分页查询某次批改下的答疑记录，可按会话 ID 过滤。"""
	return api_success(
		list_review_qa_messages(
			db,
			review_id=review_id,
			current_user_id=current_user.id,
			conversation_id=conversation_id,
			page=page,
			page_size=page_size,
		),
		message="获取答疑记录成功",
	)
