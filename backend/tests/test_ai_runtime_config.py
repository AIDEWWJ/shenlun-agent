import unittest

from app.ai.capabilities.analyzers.language_analyzer import LanguageAnalyzerAgent
from app.ai.capabilities.analyzers.structure_analyzer import StructureAnalyzerAgent
from app.ai.capabilities.comparators.point_comparator import PointComparatorAgent
from app.ai.capabilities.runtime_config import (
    LanguageAnalysisConfig,
    PointCompareConfig,
    PracticeFallbackConfig,
    RuleValidationConfig,
    StructureAnalysisConfig,
)
from app.ai.capabilities.validators.rule_validator import RuleValidatorAgent
from app.modules.practice.service import PracticeService
from app.modules.question.models import Question
from app.workflows.review.dto import (
    PointComparisonResult,
    PointExtractionResult,
    PointItem,
    QuestionAnalysisResult,
    ReviewRequest,
    StructureAnalysisResult,
)


class AiRuntimeConfigTestCase(unittest.TestCase):
    def test_point_comparator_uses_configured_thresholds(self):
        comparator = PointComparatorAgent(
            PointCompareConfig(
                exact_match_threshold=0.6,
                partial_match_threshold=0.3,
                max_keyword_length=20,
                max_keywords_per_point=20,
            )
        )
        reference = PointExtractionResult(points=[PointItem(text="强化基层队伍建设", keywords=[])], summary="")
        user = PointExtractionResult(points=[PointItem(text="基层队伍建设", keywords=[])], summary="")

        result = comparator.compare(reference, user)

        self.assertEqual(result.matched_points, ["强化基层队伍建设"])
        self.assertEqual(result.partial_points, [])

    def test_structure_analyzer_uses_configured_markers(self):
        analyzer = StructureAnalyzerAgent(
            StructureAnalysisConfig(
                markers=("第一步", "第二步"),
                min_paragraphs_for_bonus=1,
                low_coverage_threshold=0.3,
                base_score=5,
                paragraph_bonus=3,
                marker_bonus_unit=3,
                marker_bonus_cap=6,
                bullet_bonus_unit=1,
                bullet_bonus_cap=2,
                applied_doc_bonus=0,
            )
        )
        request = ReviewRequest(
            question_title="测试",
            question_content="测试内容",
            answer_content="第一步推进协同。第二步闭环落实。",
            question_type="对策题",
            reference_points=[],
        )
        question_analysis = QuestionAnalysisResult(question_type="对策题")
        comparison = PointComparisonResult(coverage_rate=1.0, matched_points=[], partial_points=[], missing_points=[], extra_points=[], note="")

        result = analyzer.analyze(request, question_analysis, comparison)

        self.assertGreaterEqual(result.score, 11)
        self.assertEqual(result.marker_count, 2)

    def test_language_analyzer_uses_configured_markers(self):
        analyzer = LanguageAnalyzerAgent(
            LanguageAnalysisConfig(
                formal_markers=("特别是",),
                punctuation_targets=("，",),
                punctuation_threshold=1,
                formal_marker_threshold=1,
                formal_marker_bonus_unit=4,
                formal_marker_bonus_cap=4,
                min_paragraphs_for_bonus=1,
                short_answer_threshold=5,
                short_answer_penalty=0,
                base_score=5,
                punctuation_bonus=3,
                paragraph_bonus=1,
            )
        )
        request = ReviewRequest(
            question_title="测试",
            question_content="测试内容",
            answer_content="特别是，要强化协同。",
            question_type="对策题",
            reference_points=[],
        )

        result = analyzer.analyze(request)

        self.assertGreaterEqual(result.score, 12)
        self.assertEqual(result.formal_markers, 1)
        self.assertEqual(result.punctuation_hits, 1)

    def test_practice_service_uses_fallback_config(self):
        service = PracticeService()
        service.fallback_config = PracticeFallbackConfig(
            question_type_mapping=(("治理", "治理题"),),
            structured_question_types=("治理题",),
            structured_hints=("提出问题", "分析原因", "给出对策"),
            default_hints=("分层展开",),
        )
        question = Question(
            id=1,
            user_id=1,
            title="基层治理如何提效",
            content="请围绕基层治理提出建议。",
            question_type=None,
            tags=None,
            source=None,
        )

        analysis = service._fallback_question_analysis(question, [])

        self.assertEqual(analysis.question_type, "治理题")
        self.assertEqual(analysis.structure_hint, ["提出问题", "分析原因", "给出对策"])

    def test_rule_validator_uses_configured_thresholds(self):
        validator = RuleValidatorAgent(
            RuleValidationConfig(
                min_answer_length=50,
                min_answer_penalty=2,
                max_answer_length=100,
                max_answer_penalty=1,
                zero_coverage_penalty=5,
                summary_question_max_length=80,
                summary_overlength_penalty=2,
                applied_doc_min_paragraphs=3,
                applied_doc_structure_penalty=2,
                penalty_cap=10,
                summary_question_type_hints=("概括",),
                applied_doc_type_hints=("公文",),
            )
        )
        request = ReviewRequest(
            question_title="测试",
            question_content="测试内容",
            answer_content="这是一个非常短的答案。",
            question_type="概括题",
            reference_points=[],
        )
        question_analysis = QuestionAnalysisResult(question_type="概括题")
        comparison = PointComparisonResult(coverage_rate=0.0, matched_points=[], partial_points=[], missing_points=[], extra_points=[], note="")
        structure_analysis = StructureAnalysisResult(paragraph_count=1)

        result = validator.validate(request, question_analysis, comparison, structure_analysis)

        self.assertEqual(result.penalty, 7)
        self.assertIn("答案过短", result.violations)
        self.assertIn("参考要点未命中", result.violations)


if __name__ == "__main__":
    unittest.main()
