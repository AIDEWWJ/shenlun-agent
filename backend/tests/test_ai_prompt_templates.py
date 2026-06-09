import unittest

from app.ai.capabilities.analyzers.question_analyzer import QuestionAnalyzerAgent
from app.ai.capabilities.extractors.reference_point_extractor import ReferencePointExtractorAgent
from app.ai.capabilities.extractors.user_point_extractor import UserPointExtractorAgent
from app.ai.capabilities.generators.outline_generator import OutlineGeneratorAgent
from app.workflows.review.dto import PointComparisonResult, QuestionAnalysisResult, ReviewLLMConfig, ReviewRequest


class AiPromptTemplateBindingTestCase(unittest.TestCase):
    def setUp(self):
        self.llm_config = ReviewLLMConfig(
            provider="openai",
            model_name="gpt-4.1-mini",
            api_key="test-key",
            base_url="https://example.com/v1",
            temperature=0.2,
            question_analysis_system_prompt="题目分析系统模板",
            question_analysis_user_prompt="分析用户模板：{question_title}|{question_type}|{reference_points}",
            reference_point_extract_system_prompt="参考要点系统模板",
            reference_point_extract_user_prompt="参考要点用户模板：{reference_points_text}|{question_type}|{scoring_focus}",
            user_point_extract_system_prompt="用户要点系统模板",
            user_point_extract_user_prompt="用户要点用户模板：{question_title}|{answer_content}|{reference_points_text}",
            outline_generate_system_prompt="提纲系统模板",
            outline_generate_user_prompt="提纲用户模板：{question_type}|{missing_points}|{matched_points}",
        )

    def test_question_analyzer_uses_configured_prompts(self):
        agent = QuestionAnalyzerAgent(self.llm_config)
        request = ReviewRequest(
            question_title="如何提升治理能力",
            question_content="围绕基层治理提升提出建议。",
            answer_content="占位",
            question_type="对策题",
            reference_points=["协同机制", "执行闭环"],
        )

        self.assertEqual(agent._build_system_prompt(), "题目分析系统模板")
        user_prompt = agent._build_prompt(request)
        self.assertIn("分析用户模板：如何提升治理能力|对策题|协同机制；执行闭环", user_prompt)

    def test_reference_point_extractor_uses_configured_prompts(self):
        agent = ReferencePointExtractorAgent(self.llm_config)
        question_analysis = QuestionAnalysisResult(
            question_type="对策题",
            scoring_focus=["协同机制", "执行闭环"],
        )

        self.assertEqual(agent._build_system_prompt(), "参考要点系统模板")
        user_prompt = agent._build_prompt(["协同机制", "执行闭环"], question_analysis)
        self.assertIn("参考要点用户模板：1. 协同机制", user_prompt)
        self.assertIn("|对策题|协同机制、执行闭环", user_prompt)

    def test_user_point_extractor_uses_configured_prompts(self):
        agent = UserPointExtractorAgent(self.llm_config)
        request = ReviewRequest(
            question_title="如何提升治理能力",
            question_content="围绕基层治理提升提出建议。",
            answer_content="先完善协同机制，再推动闭环执行。",
            question_type="对策题",
            reference_points=["协同机制", "执行闭环"],
        )
        question_analysis = QuestionAnalysisResult(question_type="对策题")

        self.assertEqual(agent._build_system_prompt(), "用户要点系统模板")
        user_prompt = agent._build_prompt(request, question_analysis)
        self.assertIn("用户要点用户模板：如何提升治理能力|先完善协同机制，再推动闭环执行。|协同机制；执行闭环", user_prompt)

    def test_outline_generator_uses_configured_prompts(self):
        agent = OutlineGeneratorAgent(self.llm_config)
        question_analysis = QuestionAnalysisResult(question_type="对策题", scoring_focus=["协同机制"])
        comparison = PointComparisonResult(
            matched_points=["协同机制"],
            partial_points=[],
            missing_points=["执行闭环"],
            extra_points=[],
            coverage_rate=0.5,
            note="部分命中",
        )

        self.assertEqual(agent._build_system_prompt(), "提纲系统模板")
        user_prompt = agent._build_prompt(question_analysis, comparison)
        self.assertIn("提纲用户模板：对策题|执行闭环|协同机制", user_prompt)


if __name__ == "__main__":
    unittest.main()
