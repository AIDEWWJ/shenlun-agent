import unittest
from unittest.mock import patch

from app.agents.reviewer import ReviewerAgent
from app.schemas.review import ReviewAnalysis, ReviewDimension, ReviewLLMConfig, ReviewRequest


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
            dimensions=[ReviewDimension(name="审题与回应", score=22, comment="命中要点", suggestions=[])],
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
