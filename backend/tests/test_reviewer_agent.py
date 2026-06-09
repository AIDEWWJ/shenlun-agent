import unittest
from unittest.mock import patch

from app.ai.capabilities.generators.reviewer import ReviewerAgent
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


class ReviewerAgentTestCase(unittest.TestCase):
    def setUp(self):
        self.agent = ReviewerAgent()

        self.llm_config = ReviewLLMConfig(
            provider="openai",
            model_name="gpt-4.1-mini",
            api_key="test-key",
            base_url="https://example.com/v1",
            temperature=0.2,
            system_prompt="你是批改官。",
        )

    def test_review_uses_llm_result(self):
        request = ReviewRequest(
            question_title="如何提升基层治理能力",
            question_content="围绕基层治理能力提升展开分析，提出有效对策。",
            answer_content="首先，强化基层队伍建设。其次，完善协同机制。最后，推动问题闭环解决。",
            question_type="对策题",
            reference_points=["强化基层队伍建设", "完善协同机制", "推动问题闭环解决"],
        )

        expected = ReviewAnalysis(
            score=88,
            dimensions=[
                ReviewDimension(name="审题与回应", score=22, comment="命中要点", suggestions=[]),
                ReviewDimension(name="内容覆盖", score=21, comment="内容较完整", suggestions=[]),
                ReviewDimension(name="结构组织", score=22, comment="结构清晰", suggestions=["保持分点结构"]),
                ReviewDimension(name="表达与语言", score=23, comment="表达较规范", suggestions=["补充案例论证"]),
            ],
            strengths=["切题"],
            issues=["略简"],
            suggestions=["补充案例"],
            summary="整体不错",
            analysis_explanation="先批改，再解释。",
            outline_explanation="按总分总展开。",
            keyword_hits=["基层治理"],
            keyword_misses=[],
            answer_length=len(request.answer_content),
            question_type="对策题",
            comparison_analysis={"matched_points": ["基层治理"], "missing_points": []},
            score_breakdown={"question_score": 22, "content_score": 21, "structure_score": 22, "language_score": 23, "total_score": 88},
        )

        with patch.object(self.agent, "_review_with_llm", return_value=expected) as mocked:
            result = self.agent.review(request, self.llm_config)

        mocked.assert_called_once()

        self.assertEqual(result.score, 88)
        self.assertEqual(result.summary, "整体不错")

    def test_review_without_llm_config_raises(self):
        request = ReviewRequest(
            question_title="请概括材料主要问题",
            question_content="材料反映了若干方面的问题，需要进行归纳。",
            answer_content="这是一个问题。",
            question_type="概括题",
            reference_points=["材料问题一", "材料问题二"],
        )

        with self.assertRaises(ValueError):
            self.agent.review(request)

    def test_repair_prompt_uses_dedicated_config(self):
        config = ReviewLLMConfig(
            provider="openai",
            model_name="gpt-4.1-mini",
            api_key="test-key",
            base_url="https://example.com/v1",
            temperature=0.2,
            system_prompt="常规批改提示词",
            repair_system_prompt="专用修正提示词",
        )

        prompt = self.agent.build_repair_system_prompt(config)

        self.assertIn("专用修正提示词", prompt)
        self.assertNotIn("常规批改提示词\n你是申论批改结果结构化修正器", prompt)

    def test_review_stabilizes_score_breakdown_and_comparison(self):
        request = ReviewRequest(
            question_title="如何提升基层治理能力",
            question_content="围绕基层治理能力提升展开分析，提出有效对策。",
            answer_content="首先，强化基层队伍建设。其次，完善协同机制。最后，推动问题闭环解决。",
            question_type="对策题",
            reference_points=["强化基层队伍建设", "完善协同机制", "推动问题闭环解决"],
        )
        question_analysis = QuestionAnalysisResult(
            question_type="对策题",
            scoring_focus=["基层队伍建设", "协同机制"],
            note="题目解析完成",
        )
        reference_points = PointExtractionResult(
            points=[PointItem(text="强化基层队伍建设"), PointItem(text="完善协同机制")],
            summary="参考要点已提取",
        )
        user_points = PointExtractionResult(
            points=[PointItem(text="强化基层队伍建设"), PointItem(text="完善协同机制")],
            summary="用户要点已提取",
        )
        comparison = PointComparisonResult(
            matched_points=["强化基层队伍建设", "完善协同机制"],
            partial_points=[],
            missing_points=[],
            extra_points=[],
            coverage_rate=1.0,
            note="命中较完整",
        )
        llm_output = ReviewAnalysis(
            score=88,
            dimensions=[
                ReviewDimension(name="审题", score=22, comment="回应较好", suggestions=[]),
                ReviewDimension(name="内容覆盖", score=23, comment="要点较完整", suggestions=[]),
                ReviewDimension(name="结构", score=21, comment="层次清晰", suggestions=["保持分点结构"]),
                ReviewDimension(name="语言", score=22, comment="表达规范", suggestions=["补充更有力的论证"]),
            ],
            strengths=["整体切题"],
            issues=["论证深度一般"],
            suggestions=[],
            summary="整体较好",
            analysis_explanation="整体回应较完整。",
            outline_explanation="总分总展开。",
            keyword_hits=[],
            keyword_misses=[],
            answer_length=len(request.answer_content),
            question_type=None,
            comparison_analysis=None,
            score_breakdown={},
        )

        with patch.object(self.agent, "_review_with_llm", return_value=llm_output):
            result = self.agent.review(
                request,
                self.llm_config,
                question_analysis=question_analysis,
                reference_point_analysis=reference_points,
                user_point_analysis=user_points,
                comparison=comparison,
            )

        self.assertEqual([item.name for item in result.dimensions], ["审题与回应", "内容覆盖", "结构组织", "表达与语言"])
        self.assertEqual(result.score_breakdown["total_score"], 88)
        self.assertEqual(result.score_breakdown["question_score"], 22)
        self.assertEqual(result.comparison_analysis["matched_points"], ["强化基层队伍建设", "完善协同机制"])
        self.assertEqual(result.suggestions, ["保持分点结构", "补充更有力的论证"])

    def test_review_repairs_incomplete_result_with_second_call(self):
        request = ReviewRequest(
            question_title="如何提升基层治理能力",
            question_content="围绕基层治理能力提升展开分析，提出有效对策。",
            answer_content="首先，强化基层队伍建设。其次，完善协同机制。最后，推动问题闭环解决。",
            question_type="对策题",
            reference_points=["强化基层队伍建设", "完善协同机制", "推动问题闭环解决"],
        )
        question_analysis = QuestionAnalysisResult(question_type="对策题", note="题目解析完成")
        reference_points = PointExtractionResult(points=[PointItem(text="强化基层队伍建设")], summary="参考要点")
        user_points = PointExtractionResult(points=[PointItem(text="强化基层队伍建设")], summary="用户要点")
        comparison = PointComparisonResult(
            matched_points=["强化基层队伍建设"],
            partial_points=[],
            missing_points=[],
            extra_points=[],
            coverage_rate=1.0,
            note="命中完整",
        )
        first_output = ReviewAnalysis(
            score=86,
            dimensions=[ReviewDimension(name="审题", score=22, comment="回应较好", suggestions=[])],
            strengths=["整体切题"],
            issues=[],
            suggestions=[],
            summary="",
            analysis_explanation="",
            outline_explanation="",
            keyword_hits=[],
            keyword_misses=[],
            answer_length=len(request.answer_content),
            question_type=None,
        )
        repaired_output = ReviewAnalysis(
            score=86,
            dimensions=[
                ReviewDimension(name="审题与回应", score=22, comment="回应较好", suggestions=[]),
                ReviewDimension(name="内容覆盖", score=21, comment="内容较完整", suggestions=[]),
                ReviewDimension(name="结构组织", score=21, comment="结构清晰", suggestions=["保持分点结构"]),
                ReviewDimension(name="表达与语言", score=22, comment="表达较规范", suggestions=["补充例证"]),
            ],
            strengths=["整体切题"],
            issues=["论证可再展开"],
            suggestions=["保持分点结构", "补充例证"],
            summary="整体较好",
            analysis_explanation="答案对题干回应较完整。",
            outline_explanation="总分总展开。",
            keyword_hits=["基层治理"],
            keyword_misses=[],
            answer_length=len(request.answer_content),
            question_type="对策题",
            comparison_analysis={"matched_points": ["强化基层队伍建设"], "missing_points": []},
            score_breakdown={"question_score": 22, "content_score": 21, "structure_score": 21, "language_score": 22, "total_score": 86},
        )

        with patch.object(self.agent, "_review_with_llm", return_value=first_output), patch.object(
            self.agent, "_repair_with_llm", return_value=repaired_output
        ) as repair_mock:
            result = self.agent.review(
                request,
                self.llm_config,
                question_analysis=question_analysis,
                reference_point_analysis=reference_points,
                user_point_analysis=user_points,
                comparison=comparison,
            )

        repair_mock.assert_called_once()
        self.assertEqual(result.summary, "整体较好")
        self.assertEqual(len(result.dimensions), 4)
        self.assertEqual(result.score_breakdown["total_score"], 86)

    def test_review_repair_failure_raises(self):
        request = ReviewRequest(
            question_title="如何提升基层治理能力",
            question_content="围绕基层治理能力提升展开分析，提出有效对策。",
            answer_content="首先，强化基层队伍建设。其次，完善协同机制。最后，推动问题闭环解决。",
            question_type="对策题",
            reference_points=["强化基层队伍建设", "完善协同机制", "推动问题闭环解决"],
        )
        bad_output = ReviewAnalysis(
            score=70,
            dimensions=[],
            strengths=[],
            issues=[],
            suggestions=[],
            summary="",
            analysis_explanation="",
            outline_explanation="",
            keyword_hits=[],
            keyword_misses=[],
            answer_length=len(request.answer_content),
            question_type=None,
        )

        with patch.object(self.agent, "_review_with_llm", return_value=bad_output), patch.object(
            self.agent, "_repair_with_llm", return_value=bad_output
        ):
            with self.assertRaises(RuntimeError):
                self.agent.review(request, self.llm_config)
