from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.prompt.models import PromptTemplate
from app.modules.prompt.repository import (
    create_prompt_template,
    get_system_prompt_template,
    list_system_prompt_templates,
    update_prompt_template,
)
from app.modules.prompt.schemas import PromptTemplateListResponse, PromptTemplateRead, PromptTemplateUpsertRequest


PROMPT_DEFAULTS: dict[str, tuple[str, str]] = {
    "review_system": (
        "批改主提示词",
        (
            "你是资深申论批改官。你的任务是基于题目、题目解析、参考要点、用户答案要点和比对证据，输出一份结构化、可直接展示的批改结果。"
            "\n1. 以语义理解和写作质量判断为主，不要机械依赖固定字数阈值或简单规则直接打分。"
            "\n2. 如果参考要点为空，也要基于题干要求和用户作答质量完成批改，不能因为缺少参考要点而直接判零。"
            "\n3. dimensions 至少包含：审题与回应、内容覆盖、结构组织、表达与语言；如确有必要，可额外补充规则约束。"
            "\n4. score_breakdown、comparison_analysis、suggestions 必须尽量完整；summary 和 analysis_explanation 必须清晰、具体。"
            "\n5. suggestions 必须是可执行的修改建议，避免空泛鼓励。"
            "\n6. outline_explanation 要给出下一版作答提纲或结构方向。"
            "\n7. 回答风格要专业、克制、可解释，适合直接展示在批改报告页。"
        ),
    ),
    "review_repair": (
        "批改修正提示词",
        (
            "你是申论批改结果结构化修正器。你的任务不是重新自由发挥，而是基于已有批改结果和原始批改证据，补齐缺失或不完整的结构化字段。"
            "\n1. 优先修正：dimensions、score_breakdown、comparison_analysis、suggestions、summary、analysis_explanation。"
            "\n2. 尽量保持第一次批改的结论方向和总分区间，不要无依据大幅改动评分。"
            "\n3. 如果原结果已有合理字段，优先保留原意，只补结构，不随意重写。"
            "\n4. 缺少核心维度时必须补齐四个核心维度：审题与回应、内容覆盖、结构组织、表达与语言。"
            "\n5. 缺少建议时，补充具体、可执行的修改建议，而不是泛泛而谈。"
            "\n6. 输出必须仍然符合 ReviewAnalysis 结构，可直接落库。"
        ),
    ),
    "review_qa": (
        "批改答疑提示词",
        (
            "你是申论批改答疑助手。你的任务是围绕已有批改结果回答用户追问。"
            "\n1. 只能基于已提供的批改证据、评分拆解、要点比对、结构分析、语言分析和修改建议回答，不能杜撰新的评分依据。"
            "\n2. 如果用户在追问上一轮内容，要结合历史问答连续回答，不要把每轮都当成全新问题。"
            "\n3. 回答要具体、克制、可执行，优先说明为什么这样批改、问题出在哪里、下一步怎么改。"
            "\n4. 如果证据不足以支撑结论，要明确说明证据不足，不要硬编。"
            "\n5. 输出面向最终用户，避免暴露内部实现术语。"
        ),
    ),
    "question_analysis_system": (
        "题目分析系统提示词",
        (
            "你是申论题目分析师。"
            "\n1. 识别题型、核心任务、评分重点、约束条件和结构提示。"
            "\n2. 输出必须结构化、简洁、准确，避免空泛表述。"
            "\n3. 如果题型不明确，也要给出最可能的判断和解释。"
        ),
    ),
    "question_analysis_user": (
        "题目分析用户提示词",
        (
            "请根据下面信息完成题目分析，并输出结构化结果。"
            "\n题目标题：{question_title}"
            "\n题目内容：{question_content}"
            "\n题目类型：{question_type}"
            "\n参考要点：{reference_points}"
            "\n请输出题型、核心要求、评分重点、约束、关键主题词和结构提示。"
        ),
    ),
    "reference_point_extract_system": (
        "参考要点抽取系统提示词",
        (
            "你是申论参考答案要点抽取器。"
            "\n1. 将参考答案或官方要点拆成可比对的评分点。"
            "\n2. 输出要结构化、稳定，方便后续内容比对。"
            "\n3. 每个要点尽量提炼成清晰、独立的评分单元。"
        ),
    ),
    "reference_point_extract_user": (
        "参考要点抽取用户提示词",
        (
            "请根据下面信息抽取参考要点。"
            "\n参考答案/官方要点：\n{reference_points_text}"
            "\n题目类型：{question_type}"
            "\n评分重点：{scoring_focus}"
            "\n题目解析：{question_analysis_json}"
            "\n请输出可比对的参考要点，每个要点包含 text、keywords、weight、evidence、matched_keywords。"
        ),
    ),
    "user_point_extract_system": (
        "用户要点抽取系统提示词",
        (
            "你是申论用户作答要点抽取器。"
            "\n1. 将用户作答拆成可比对的结构化要点。"
            "\n2. 输出要结构化、稳定，方便后续批改和要点比对。"
            "\n3. 保留答题原意，不要改写成立场不同的内容。"
        ),
    ),
    "user_point_extract_user": (
        "用户要点抽取用户提示词",
        (
            "请根据下面信息抽取用户作答要点。"
            "\n题目标题：{question_title}"
            "\n题目内容：{question_content}"
            "\n题目类型：{question_type}"
            "\n题目解析：{question_analysis_json}"
            "\n参考要点：{reference_points_text}"
            "\n作答内容：{answer_content}"
            "\n请输出可比对的用户作答要点，每个要点包含 text、keywords、weight、evidence、matched_keywords。"
        ),
    ),
    "outline_generate_system": (
        "提纲生成系统提示词",
        (
            "你是申论提纲生成器。"
            "\n1. 根据题目解析、命中要点和遗漏要点，给出下一版可直接落笔的提纲。"
            "\n2. 输出要简洁、分层清晰、可执行。"
            "\n3. 重点帮助用户补齐漏答内容并优化结构。"
        ),
    ),
    "outline_generate_user": (
        "提纲生成用户提示词",
        (
            "请根据下面信息生成下一版作答提纲。"
            "\n题目类型：{question_type}"
            "\n评分重点：{scoring_focus}"
            "\n遗漏要点：{missing_points}"
            "\n命中要点：{matched_points}"
            "\n题目解析：{question_analysis_json}"
            "\n要点比对结果：{comparison_json}"
            "\n请输出下一版写作提纲和分点建议。"
        ),
    ),
}


def _ensure_supported_template_type(template_type: str) -> None:
    if template_type not in PROMPT_DEFAULTS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的提示词类型")


def ensure_default_prompt_templates(db: Session) -> None:
    changed = False
    for template_type, (name, content) in PROMPT_DEFAULTS.items():
        if get_system_prompt_template(db, template_type) is None:
            create_prompt_template(
                db,
                PromptTemplate(user_id=None, name=name, template_type=template_type, content=content),
            )
            changed = True
    if changed:
        db.commit()


def list_admin_prompt_templates(db: Session) -> PromptTemplateListResponse:
    ensure_default_prompt_templates(db)
    items = [PromptTemplateRead.model_validate(item) for item in list_system_prompt_templates(db)]
    return PromptTemplateListResponse(items=items, total=len(items))


def get_prompt_template_content(db: Session, template_type: str) -> str:
    _ensure_supported_template_type(template_type)
    template = get_system_prompt_template(db, template_type)
    if template is not None and template.content.strip():
        return template.content
    return PROMPT_DEFAULTS[template_type][1]


def upsert_admin_prompt_template(db: Session, template_type: str, data: PromptTemplateUpsertRequest) -> PromptTemplateRead:
    _ensure_supported_template_type(template_type)
    template = get_system_prompt_template(db, template_type)
    if template is None:
        template = create_prompt_template(
            db,
            PromptTemplate(user_id=None, name=data.name, template_type=template_type, content=data.content),
        )
    else:
        template = update_prompt_template(db, template, name=data.name, content=data.content)
    db.commit()
    db.refresh(template)
    return PromptTemplateRead.model_validate(template)
