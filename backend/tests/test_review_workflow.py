import unittest
from unittest.mock import Mock

from app.workflows.review.dto import (
    PointComparisonResult,
    PointExtractionResult,
    PointItem,
    QuestionAnalysisResult,
    ReviewAnalysis,
    ReviewDimension,
    ReviewLLMConfig,
    ReviewRequest,
)
from app.workflows.review.orchestrator import ReviewService


class ReviewWorkflowTestCase(unittest.TestCase):
    def setUp(self):
        self.llm_config = ReviewLLMConfig(
            provider="openai",
            model_name="gpt-4.1-mini",
            api_key="test-key",
            base_url="https://example.com/v1",
            temperature=0.2,
            system_prompt="你是申论批改官。",
        )

    def test_ai_review_is_primary_and_no_reference_points_do_not_trigger_rule_penalty(self):
        service = ReviewService(self.llm_config)
        request = ReviewRequest(
            question_title="如何提升基层治理能力",
            question_content="围绕基层治理能力提升展开分析，提出有效对策。",
            answer_content="首先强化基层队伍建设，其次完善协同机制，最后推动问题闭环解决。",
            question_type=None,
            reference_points=[],
        )

        question_analysis = QuestionAnalysisResult(
            question_type="对策题",
            task_requirements=["围绕基层治理能力提升提出对策"],
            scoring_focus=["基层队伍", "协同机制", "闭环解决"],
            constraints=["围绕题干要求作答"],
            key_topics=["基层治理", "协同机制"],
            structure_hint=["总分总", "分点作答"],
            note="AI 已完成题目解析",
        )
        user_points = PointExtractionResult(
            points=[
                PointItem(text="强化基层队伍建设", keywords=["基层队伍"]),
                PointItem(text="完善协同机制", keywords=["协同机制"]),
            ],
            summary="已提取用户答案要点",
        )
        comparison = PointComparisonResult(
            matched_points=[],
            partial_points=[],
            missing_points=[],
            extra_points=["强化基层队伍建设", "完善协同机制"],
            coverage_rate=0.0,
            note="未提供参考要点，未做覆盖率扣分",
        )
        ai_analysis = ReviewAnalysis(
            score=92,
            dimensions=[
                ReviewDimension(name="审题与回应", score=23, comment="回应题干较完整", suggestions=[]),
                ReviewDimension(name="内容覆盖", score=22, comment="内容较充实", suggestions=[]),
                ReviewDimension(name="结构组织", score=23, comment="结构清晰", suggestions=["保持分点结构"]),
                ReviewDimension(name="表达与语言", score=24, comment="表达规范", suggestions=["补充更有力的论证"]),
            ],
            strengths=["整体切题", "结构清晰"],
            issues=["论证深度还可提升"],
            suggestions=["补充执行层举措"],
            summary="AI 认为整体质量较高。",
            analysis_explanation="答案对题干回应较完整，结构和表达较好。",
            outline_explanation="问题-原因-对策三段式展开。",
            keyword_hits=["基层队伍", "协同机制"],
            keyword_misses=[],
            answer_length=len(request.answer_content),
            question_type="对策题",
            comparison_analysis={"matched_points": [], "missing_points": [], "extra_points": ["强化基层队伍建设"]},
            structure_analysis={"score": 23, "issues": [], "suggestions": ["保持分点结构"], "note": "结构清晰"},
            language_analysis={"score": 24, "issues": [], "suggestions": ["补充更有力的论证"], "note": "表达规范"},
            rule_analysis={},
            score_breakdown={
                "question_score": 23,
                "content_score": 22,
                "structure_score": 23,
                "language_score": 24,
                "rule_score": 0,
                "total_score": 92,
            },
            report_json={"outline": "问题-原因-对策三段式展开。"},
        )

        service.question_analyzer.analyze = Mock(return_value=question_analysis)
        service.reference_point_extractor.extract = Mock(side_effect=RuntimeError("should not be called"))
        service.user_point_extractor.extract = Mock(return_value=user_points)
        service.point_comparator.compare = Mock(return_value=comparison)
        service.reviewer.review = Mock(return_value=ai_analysis)
        result = service.review(request)

        service.reference_point_extractor.extract.assert_not_called()
        service.reviewer.review.assert_called_once()
        self.assertEqual(result.analysis.score, 92)
        self.assertEqual(result.analysis.question_type, "对策题")
        self.assertEqual(result.analysis.score_breakdown["total_score"], 92)
        self.assertEqual(result.analysis.rule_analysis, {})
        self.assertEqual(result.analysis.outline_explanation, "问题-原因-对策三段式展开。")

        step_keys = [step.step_key for step in result.steps]
        self.assertEqual(
            step_keys,
            [
                "question_analysis",
                "reference_point_extraction",
                "user_point_extraction",
                "point_comparison",
                "ai_review",
            ],
        )

    def test_ai_review_missing_dimensions_raises(self):
        service = ReviewService(self.llm_config)
        request = ReviewRequest(
            question_title="如何优化政务服务",
            question_content="围绕政务服务优化提出建议。",
            answer_content="通过流程再造和数据共享提升服务效率。",
            question_type="对策题",
            reference_points=["流程再造", "数据共享"],
        )

        service.question_analyzer.analyze = Mock(
            return_value=QuestionAnalysisResult(
                question_type="对策题",
                scoring_focus=["流程再造", "数据共享"],
                note="完成解析",
            )
        )
        service.reference_point_extractor.extract = Mock(
            return_value=PointExtractionResult(points=[PointItem(text="流程再造"), PointItem(text="数据共享")], summary="")
        )
        service.user_point_extractor.extract = Mock(
            return_value=PointExtractionResult(points=[PointItem(text="流程再造"), PointItem(text="数据共享")], summary="")
        )
        service.point_comparator.compare = Mock(
            return_value=PointComparisonResult(
                matched_points=["流程再造", "数据共享"],
                partial_points=[],
                missing_points=[],
                extra_points=[],
                coverage_rate=1.0,
                note="完全命中",
            )
        )
        service.reviewer.review = Mock(side_effect=RuntimeError("AI批改结果缺少核心评分维度"))
        with self.assertRaises(RuntimeError):
            service.review(request)


if __name__ == "__main__":
    unittest.main()
