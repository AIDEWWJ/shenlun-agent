from dataclasses import dataclass


@dataclass(slots=True)
class PointCompareConfig:
    exact_match_threshold: float = 0.82
    partial_match_threshold: float = 0.45
    max_keyword_length: int = 12
    max_keywords_per_point: int = 12


@dataclass(slots=True)
class StructureAnalysisConfig:
    markers: tuple[str, ...] = (
        "首先",
        "其次",
        "再次",
        "最后",
        "一是",
        "二是",
        "三是",
        "第一",
        "第二",
        "第三",
        "综上",
        "因此",
        "总之",
        "一方面",
        "另一方面",
    )
    min_paragraphs_for_bonus: int = 2
    low_coverage_threshold: float = 0.5
    base_score: int = 10
    paragraph_bonus: int = 6
    marker_bonus_unit: int = 2
    marker_bonus_cap: int = 5
    bullet_bonus_unit: int = 2
    bullet_bonus_cap: int = 4
    applied_doc_bonus: int = 2


@dataclass(slots=True)
class LanguageAnalysisConfig:
    formal_markers: tuple[str, ...] = (
        "因此",
        "综上",
        "建议",
        "需要",
        "应当",
        "必须",
        "要",
        "应该",
        "首先",
        "其次",
        "再次",
        "最后",
        "一是",
        "二是",
        "三是",
        "一方面",
        "另一方面",
    )
    punctuation_targets: tuple[str, ...] = ("，", "。", "；")
    punctuation_threshold: int = 5
    formal_marker_threshold: int = 2
    formal_marker_bonus_unit: int = 2
    formal_marker_bonus_cap: int = 8
    min_paragraphs_for_bonus: int = 2
    short_answer_threshold: int = 80
    short_answer_penalty: int = 2
    base_score: int = 10
    punctuation_bonus: int = 5
    paragraph_bonus: int = 2


@dataclass(slots=True)
class RuleValidationConfig:
    min_answer_length: int = 80
    min_answer_penalty: int = 6
    max_answer_length: int = 3000
    max_answer_penalty: int = 3
    zero_coverage_penalty: int = 8
    summary_question_max_length: int = 1200
    summary_overlength_penalty: int = 4
    applied_doc_min_paragraphs: int = 2
    applied_doc_structure_penalty: int = 4
    penalty_cap: int = 25
    summary_question_type_hints: tuple[str, ...] = ("概括", "归纳", "提炼")
    applied_doc_type_hints: tuple[str, ...] = ("贯彻执行", "应用文", "公文")


@dataclass(slots=True)
class PracticeFallbackConfig:
    question_type_mapping: tuple[tuple[str, str], ...] = (
        ("概括", "概括题"),
        ("对策", "对策题"),
        ("公文", "公文题"),
        ("写作", "大作文"),
        ("作文", "大作文"),
        ("综合分析", "综合分析"),
    )
    structured_question_types: tuple[str, ...] = ("对策题", "概括题", "大作文")
    structured_hints: tuple[str, ...] = ("总分总", "分点作答")
    default_hints: tuple[str, ...] = ("分层展开",)
