"""Legacy 批改评分标准。

说明：
- 当前主批改链已不依赖本模块作为主评分标准。
- 仅保留历史兼容和参考用途。
"""

from __future__ import annotations

from app.workflows.review.scoring import REVIEW_RUBRIC, ReviewRubricItem

__all__ = ["REVIEW_RUBRIC", "ReviewRubricItem"]
