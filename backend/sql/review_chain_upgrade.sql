ALTER TABLE reviews
    ADD COLUMN IF NOT EXISTS question_id BIGINT NULL COMMENT '题目 ID',
    ADD COLUMN IF NOT EXISTS user_id BIGINT NULL COMMENT '用户 ID',
    ADD COLUMN IF NOT EXISTS question_title_snapshot VARCHAR(255) NULL COMMENT '题目标题快照',
    ADD COLUMN IF NOT EXISTS question_type_snapshot VARCHAR(64) NULL COMMENT '题型快照',
    ADD COLUMN IF NOT EXISTS question_content_snapshot TEXT NULL COMMENT '题目内容快照',
    ADD COLUMN IF NOT EXISTS answer_content_snapshot TEXT NULL COMMENT '答案内容快照',
    ADD COLUMN IF NOT EXISTS reference_points_json LONGTEXT NULL COMMENT '参考要点 JSON',
    ADD COLUMN IF NOT EXISTS question_analysis_json LONGTEXT NULL COMMENT '题目解析 JSON',
    ADD COLUMN IF NOT EXISTS reference_point_analysis_json LONGTEXT NULL COMMENT '参考要点抽取 JSON',
    ADD COLUMN IF NOT EXISTS user_point_analysis_json LONGTEXT NULL COMMENT '用户要点抽取 JSON',
    ADD COLUMN IF NOT EXISTS comparison_json LONGTEXT NULL COMMENT '要点比对 JSON',
    ADD COLUMN IF NOT EXISTS structure_analysis_json LONGTEXT NULL COMMENT '结构分析 JSON',
    ADD COLUMN IF NOT EXISTS language_analysis_json LONGTEXT NULL COMMENT '语言分析 JSON',
    ADD COLUMN IF NOT EXISTS rule_analysis_json LONGTEXT NULL COMMENT '规则校验 JSON',
    ADD COLUMN IF NOT EXISTS score_breakdown_json LONGTEXT NULL COMMENT '分数拆解 JSON',
    ADD COLUMN IF NOT EXISTS report_json LONGTEXT NULL COMMENT '批改报告 JSON',
    ADD COLUMN IF NOT EXISTS model_provider VARCHAR(64) NULL COMMENT '模型提供方',
    ADD COLUMN IF NOT EXISTS model_name VARCHAR(128) NULL COMMENT '模型名称';

ALTER TABLE ai_configs
    ADD COLUMN IF NOT EXISTS repair_system_prompt TEXT NULL COMMENT '批改结果修正提示词';

ALTER TABLE prompt_templates
    ADD CONSTRAINT uk_prompt_templates_template_type UNIQUE (template_type);

CREATE TABLE IF NOT EXISTS system_configs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    category VARCHAR(64) NOT NULL COMMENT '配置类别',
    config_key VARCHAR(64) NOT NULL COMMENT '配置键',
    name VARCHAR(128) NOT NULL COMMENT '配置名称',
    content_json LONGTEXT NOT NULL COMMENT '配置 JSON',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_system_configs_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统运行配置表';

INSERT INTO system_configs (category, config_key, name, content_json)
SELECT
    'ai_runtime',
    'point_compare',
    '要点比对配置',
    '{"exact_match_threshold": 0.82, "partial_match_threshold": 0.45, "max_keyword_length": 12, "max_keywords_per_point": 12}'
WHERE NOT EXISTS (SELECT 1 FROM system_configs WHERE config_key = 'point_compare');

INSERT INTO system_configs (category, config_key, name, content_json)
SELECT
    'ai_runtime',
    'structure_analysis',
    '结构分析配置',
    '{"markers": ["首先", "其次", "再次", "最后", "一是", "二是", "三是", "第一", "第二", "第三", "综上", "因此", "总之", "一方面", "另一方面"], "min_paragraphs_for_bonus": 2, "low_coverage_threshold": 0.5, "base_score": 10, "paragraph_bonus": 6, "marker_bonus_unit": 2, "marker_bonus_cap": 5, "bullet_bonus_unit": 2, "bullet_bonus_cap": 4, "applied_doc_bonus": 2}'
WHERE NOT EXISTS (SELECT 1 FROM system_configs WHERE config_key = 'structure_analysis');

INSERT INTO system_configs (category, config_key, name, content_json)
SELECT
    'ai_runtime',
    'language_analysis',
    '语言分析配置',
    '{"formal_markers": ["因此", "综上", "建议", "需要", "应当", "必须", "要", "应该", "首先", "其次", "再次", "最后", "一是", "二是", "三是", "一方面", "另一方面"], "punctuation_targets": ["，", "。", "；"], "punctuation_threshold": 5, "formal_marker_threshold": 2, "formal_marker_bonus_unit": 2, "formal_marker_bonus_cap": 8, "min_paragraphs_for_bonus": 2, "short_answer_threshold": 80, "short_answer_penalty": 2, "base_score": 10, "punctuation_bonus": 5, "paragraph_bonus": 2}'
WHERE NOT EXISTS (SELECT 1 FROM system_configs WHERE config_key = 'language_analysis');

INSERT INTO system_configs (category, config_key, name, content_json)
SELECT
    'ai_runtime',
    'rule_validation',
    '规则校验配置',
    '{"min_answer_length": 80, "min_answer_penalty": 6, "max_answer_length": 3000, "max_answer_penalty": 3, "zero_coverage_penalty": 8, "summary_question_max_length": 1200, "summary_overlength_penalty": 4, "applied_doc_min_paragraphs": 2, "applied_doc_structure_penalty": 4, "penalty_cap": 25, "summary_question_type_hints": ["概括", "归纳", "提炼"], "applied_doc_type_hints": ["贯彻执行", "应用文", "公文"]}'
WHERE NOT EXISTS (SELECT 1 FROM system_configs WHERE config_key = 'rule_validation');

INSERT INTO system_configs (category, config_key, name, content_json)
SELECT
    'ai_runtime',
    'practice_fallback',
    '练习回退配置',
    '{"question_type_mapping": [["概括", "概括题"], ["对策", "对策题"], ["公文", "公文题"], ["写作", "大作文"], ["作文", "大作文"], ["综合分析", "综合分析"]], "structured_question_types": ["对策题", "概括题", "大作文"], "structured_hints": ["总分总", "分点作答"], "default_hints": ["分层展开"]}'
WHERE NOT EXISTS (SELECT 1 FROM system_configs WHERE config_key = 'practice_fallback');

ALTER TABLE review_steps
    ADD COLUMN IF NOT EXISTS status VARCHAR(32) NOT NULL DEFAULT 'success' COMMENT '步骤状态：success / failed / degraded / skipped',
    ADD COLUMN IF NOT EXISTS critical TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否关键步骤',
    ADD COLUMN IF NOT EXISTS attempts INT NOT NULL DEFAULT 1 COMMENT '重试次数',
    ADD COLUMN IF NOT EXISTS error TEXT NULL COMMENT '错误信息';

CREATE TABLE IF NOT EXISTS review_steps (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    review_id BIGINT NOT NULL COMMENT '批改结果 ID',
    step_key VARCHAR(64) NOT NULL COMMENT '步骤键',
    step_name VARCHAR(128) NOT NULL COMMENT '步骤名称',
    order_no INT NOT NULL COMMENT '步骤顺序',
    status VARCHAR(32) NOT NULL DEFAULT 'success' COMMENT '步骤状态：success / failed / degraded / skipped',
    critical TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否关键步骤',
    attempts INT NOT NULL DEFAULT 1 COMMENT '重试次数',
    error TEXT COMMENT '错误信息',
    input_json LONGTEXT NOT NULL COMMENT '输入 JSON',
    output_json LONGTEXT NOT NULL COMMENT '输出 JSON',
    note TEXT COMMENT '备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_review_steps_review FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE,
    KEY idx_review_steps_review_id (review_id),
    KEY idx_review_steps_order (review_id, order_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='批改步骤表';

CREATE TABLE IF NOT EXISTS review_qa_messages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    review_id BIGINT NOT NULL COMMENT '批改结果 ID',
    user_id BIGINT NOT NULL COMMENT '提问用户 ID',
    conversation_id VARCHAR(64) NOT NULL COMMENT '会话 ID',
    parent_message_id BIGINT NULL COMMENT '父答疑消息 ID',
    round_no INT NOT NULL DEFAULT 1 COMMENT '会话轮次',
    question_text TEXT NOT NULL COMMENT '用户问题',
    question_category VARCHAR(64) NOT NULL COMMENT '问题分类',
    answer_text TEXT NOT NULL COMMENT '回答内容',
    evidence_refs_json LONGTEXT NOT NULL COMMENT '证据引用 JSON',
    used_llm TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否实际使用 LLM',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_review_qa_messages_review FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE,
    CONSTRAINT fk_review_qa_messages_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_review_qa_messages_parent FOREIGN KEY (parent_message_id) REFERENCES review_qa_messages(id) ON DELETE SET NULL,
    KEY idx_review_qa_messages_review_conversation_round (review_id, conversation_id, round_no),
    KEY idx_review_qa_messages_user_id_id (user_id, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='批改答疑记录表';

ALTER TABLE review_qa_messages
    ADD COLUMN IF NOT EXISTS conversation_id VARCHAR(64) NOT NULL DEFAULT '' COMMENT '会话 ID',
    ADD COLUMN IF NOT EXISTS parent_message_id BIGINT NULL COMMENT '父答疑消息 ID',
    ADD COLUMN IF NOT EXISTS round_no INT NOT NULL DEFAULT 1 COMMENT '会话轮次';
