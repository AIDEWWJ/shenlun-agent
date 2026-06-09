CREATE DATABASE IF NOT EXISTS shenlun_agent
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE shenlun_agent;

-- =========================
-- 用户表
-- 用于保存系统登录用户信息
-- =========================
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    username VARCHAR(64) NOT NULL UNIQUE COMMENT '用户名',
    email VARCHAR(128) UNIQUE COMMENT '邮箱，可为空',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    status VARCHAR(32) NOT NULL DEFAULT 'active' COMMENT '状态：active / disabled',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';

-- =========================
-- 邮件配置表
-- 用于保存管理员配置的 SMTP 发送参数
-- =========================
CREATE TABLE IF NOT EXISTS email_configs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    name VARCHAR(64) NOT NULL UNIQUE COMMENT '配置名称',
    smtp_host VARCHAR(255) NOT NULL COMMENT 'SMTP 主机',
    smtp_port INT NOT NULL DEFAULT 587 COMMENT 'SMTP 端口',
    smtp_username VARCHAR(255) COMMENT 'SMTP 用户名',
    smtp_password VARCHAR(255) COMMENT 'SMTP 密码',
    sender_email VARCHAR(128) NOT NULL COMMENT '发件邮箱',
    sender_name VARCHAR(128) COMMENT '发件名称',
    use_tls BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用 TLS',
    use_ssl BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否启用 SSL',
    enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    KEY idx_email_configs_enabled_id (enabled, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='邮件配置表';

-- =========================
-- 邮件模板表
-- 用于保存注册验证、找回密码等邮件模板
-- =========================
CREATE TABLE IF NOT EXISTS email_templates (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    template_key VARCHAR(64) NOT NULL UNIQUE COMMENT '模板键',
    template_name VARCHAR(128) NOT NULL COMMENT '模板名称',
    subject VARCHAR(255) NOT NULL COMMENT '邮件主题',
    body_text TEXT NOT NULL COMMENT '纯文本模板',
    body_html TEXT COMMENT 'HTML 模板',
    enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='邮件模板表';

-- =========================
-- 邮件验证码表
-- 用于保存注册验证、找回密码验证码
-- =========================
CREATE TABLE IF NOT EXISTS email_verification_codes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    email VARCHAR(128) NOT NULL COMMENT '目标邮箱',
    purpose VARCHAR(32) NOT NULL COMMENT '用途：register_verify / forgot_password_verify',
    code_hash VARCHAR(255) NOT NULL COMMENT '验证码哈希',
    context_json TEXT NOT NULL COMMENT '上下文 JSON',
    expires_at DATETIME NOT NULL COMMENT '过期时间',
    used_at DATETIME NULL COMMENT '使用时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    KEY idx_email_verification_email_purpose_id (email, purpose, id),
    KEY idx_email_verification_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='邮件验证码表';

-- =========================
-- 角色表
-- 用于定义系统角色：访客、学员、管理员
-- =========================
CREATE TABLE IF NOT EXISTS roles (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    name VARCHAR(64) NOT NULL UNIQUE COMMENT '角色编码，如 learner/admin',
    display_name VARCHAR(128) NOT NULL COMMENT '角色显示名称',
    description VARCHAR(255) COMMENT '角色说明'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统角色表';

-- =========================
-- 用户角色关联表
-- 用于实现一个用户拥有多个角色的 RBAC 结构
-- =========================
CREATE TABLE IF NOT EXISTS user_roles (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    user_id BIGINT NOT NULL COMMENT '用户 ID',
    role_id BIGINT NOT NULL COMMENT '角色 ID',
    CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_role (user_id, role_id),
    KEY idx_user_roles_role_id (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户角色关联表';

-- =========================
-- AI 配置表
-- 保存用户个人配置和管理员维护的系统默认配置
-- =========================
CREATE TABLE IF NOT EXISTS ai_configs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    user_id BIGINT NULL COMMENT '所属用户 ID；系统默认配置可为空',
    scope VARCHAR(16) NOT NULL DEFAULT 'user' COMMENT '配置范围：user / system',
    created_by BIGINT NULL COMMENT '创建人 ID；通常是管理员',
    provider VARCHAR(64) NOT NULL COMMENT '模型提供方，如 openai / qwen / deepseek',
    model_name VARCHAR(128) NOT NULL COMMENT '模型名称',
    api_key VARCHAR(255) NOT NULL COMMENT 'API Key（建议加密或脱敏保存）',
    base_url VARCHAR(255) COMMENT '模型接口地址',
    temperature DOUBLE NOT NULL DEFAULT 0.3 COMMENT '生成温度',
    system_prompt TEXT COMMENT '系统提示词',
    repair_system_prompt TEXT COMMENT '批改结果修正提示词',
    is_default BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否默认配置',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_ai_configs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_ai_configs_creator FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    KEY idx_ai_configs_scope_user_default_created (scope, user_id, is_default, created_at),
    KEY idx_ai_configs_created_by (created_by),
    KEY idx_ai_configs_provider_model (provider, model_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI 配置表';

-- =========================
-- 试卷表
-- 保存试卷元数据，一道试卷包含多道小题
-- =========================
CREATE TABLE IF NOT EXISTS papers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    user_id BIGINT NOT NULL COMMENT '创建者用户 ID',
    scope VARCHAR(16) NOT NULL DEFAULT 'system' COMMENT '题库范围：system / user',
    title VARCHAR(255) NOT NULL COMMENT '试卷标题',
    category VARCHAR(32) COMMENT '分类，如申论',
    region VARCHAR(64) COMMENT '地区，如国考、广东',
    difficulty VARCHAR(32) COMMENT '难度等级',
    year INT COMMENT '年份',
    source_url VARCHAR(512) COMMENT '来源链接',
    question_count INT NOT NULL DEFAULT 0 COMMENT '小题数量',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_papers_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    KEY idx_papers_scope_id (scope, id),
    KEY idx_papers_user_id (user_id, id),
    KEY idx_papers_region_year (region, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='试卷表';

-- =========================
-- 题目表
-- 保存申论题目内容、分类和来源
-- =========================
CREATE TABLE IF NOT EXISTS questions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    user_id BIGINT NOT NULL COMMENT '创建者用户 ID',
    paper_id BIGINT NULL COMMENT '所属试卷 ID；NULL 表示独立题目',
    scope VARCHAR(16) NOT NULL DEFAULT 'user' COMMENT '题库范围：system（系统总题库）/ user（个人题库）',
    title VARCHAR(255) NOT NULL COMMENT '题目标题',
    content TEXT NOT NULL COMMENT '题目正文（兼容旧数据，新数据用 material + requirement）',
    material TEXT COMMENT '给定材料正文',
    requirement TEXT COMMENT '作答要求',
    sort_order INT COMMENT '在试卷中的排序',
    category VARCHAR(32) COMMENT '题目分类',
    year INT COMMENT '年份',
    region VARCHAR(64) COMMENT '地区',
    question_type VARCHAR(64) COMMENT '题型，如概括题、对策题、综合分析题',
    difficulty VARCHAR(32) COMMENT '难度等级',
    theme VARCHAR(64) COMMENT '主题',
    suggested_minutes INT COMMENT '建议作答时长（分钟）',
    tags VARCHAR(255) COMMENT '标签，逗号分隔',
    source VARCHAR(255) COMMENT '题目来源',
    cover_note VARCHAR(255) COMMENT '封面摘要',
    intro TEXT COMMENT '简要介绍',
    overview TEXT COMMENT '训练概览',
    tasks_json LONGTEXT COMMENT '题目任务 JSON',
    instructions_json LONGTEXT COMMENT '作答指南 JSON',
    notices_json LONGTEXT COMMENT '提示事项 JSON',
    materials_json LONGTEXT COMMENT '材料分段 JSON',
    answer_sections_json LONGTEXT COMMENT '作答分栏 JSON',
    reference_answer LONGTEXT COMMENT '参考答案',
    optimized_example LONGTEXT COMMENT '优化示例',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_questions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_questions_paper FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
    KEY idx_questions_user_id_id (user_id, id),
    KEY idx_questions_question_type_id (question_type, id),
    KEY idx_questions_source_id (source, id),
    KEY idx_questions_scope_id (scope, id),
    KEY idx_questions_paper_id (paper_id, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='申论题目表';

-- =========================
-- 答案表
-- 保存用户针对某道题提交的答案版本
-- =========================
CREATE TABLE IF NOT EXISTS answers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    question_id BIGINT NOT NULL COMMENT '题目 ID',
    user_id BIGINT NOT NULL COMMENT '用户 ID',
    content TEXT NOT NULL COMMENT '答案正文',
    version_no INT NOT NULL DEFAULT 1 COMMENT '答案版本号',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
    CONSTRAINT fk_answers_question FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    CONSTRAINT fk_answers_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_answers_question_user_version (question_id, user_id, version_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='答案表';

-- =========================
-- 批改结果表
-- 保存 AI 对答案的评分、点评和复盘结论
-- =========================
CREATE TABLE IF NOT EXISTS reviews (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    answer_id BIGINT NOT NULL COMMENT '答案 ID',
    question_id BIGINT NOT NULL COMMENT '题目 ID',
    user_id BIGINT NOT NULL COMMENT '用户 ID',
    question_title_snapshot VARCHAR(255) NOT NULL COMMENT '题目标题快照',
    question_type_snapshot VARCHAR(64) COMMENT '题型快照',
    question_content_snapshot TEXT NOT NULL COMMENT '题目内容快照',
    answer_content_snapshot TEXT NOT NULL COMMENT '答案内容快照',
    reference_points_json LONGTEXT NOT NULL COMMENT '参考要点 JSON',
    question_analysis_json LONGTEXT NOT NULL COMMENT '题目解析 JSON',
    reference_point_analysis_json LONGTEXT NOT NULL COMMENT '参考要点抽取 JSON',
    user_point_analysis_json LONGTEXT NOT NULL COMMENT '用户要点抽取 JSON',
    comparison_json LONGTEXT NOT NULL COMMENT '要点比对 JSON',
    structure_analysis_json LONGTEXT NOT NULL COMMENT '结构分析 JSON',
    language_analysis_json LONGTEXT NOT NULL COMMENT '语言分析 JSON',
    rule_analysis_json LONGTEXT NOT NULL COMMENT '规则校验 JSON',
    score_breakdown_json LONGTEXT NOT NULL COMMENT '分数拆解 JSON',
    report_json LONGTEXT NOT NULL COMMENT '批改报告 JSON',
    model_provider VARCHAR(64) COMMENT '模型提供方',
    model_name VARCHAR(128) COMMENT '模型名称',
    score INT COMMENT '评分',
    strengths TEXT COMMENT '优点',
    issues TEXT COMMENT '问题',
    suggestions TEXT COMMENT '修改建议',
    summary TEXT COMMENT '复盘总结',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
    CONSTRAINT fk_reviews_question FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    CONSTRAINT fk_reviews_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_reviews_answer FOREIGN KEY (answer_id) REFERENCES answers(id) ON DELETE CASCADE,
    UNIQUE KEY uk_reviews_answer_id (answer_id),
    KEY idx_reviews_user_id_id (user_id, id),
    KEY idx_reviews_question_id_id (question_id, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='批改结果表';

-- =========================
-- 批改步骤表
-- 保存题目解析、要点抽取、比对等中间证据
-- =========================
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
    KEY idx_review_steps_review_order_id (review_id, order_no, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='批改步骤表';

-- =========================
-- 批改答疑记录表
-- 保存围绕某次批改结果的追问和回答
-- =========================
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
    used_llm BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否实际使用 LLM',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_review_qa_messages_review FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE,
    CONSTRAINT fk_review_qa_messages_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_review_qa_messages_parent FOREIGN KEY (parent_message_id) REFERENCES review_qa_messages(id) ON DELETE SET NULL,
    KEY idx_review_qa_messages_review_conversation_round (review_id, conversation_id, round_no),
    KEY idx_review_qa_messages_user_id_id (user_id, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='批改答疑记录表';

-- =========================
-- 练习会话表
-- 保存某道题的云端草稿与提交状态
-- 注意：user_id / question_id / answer_id 必须与 users / questions / answers 主键保持 BIGINT 一致
-- =========================
CREATE TABLE IF NOT EXISTS practice_sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    user_id BIGINT NOT NULL COMMENT '用户 ID',
    question_id BIGINT NOT NULL COMMENT '题目 ID',
    answer_id BIGINT NULL COMMENT '提交后关联的答案 ID',
    status VARCHAR(32) NOT NULL DEFAULT 'drafting' COMMENT '会话状态：drafting / completed',
    answers_json LONGTEXT NOT NULL COMMENT '分栏作答 JSON',
    elapsed_seconds INT NOT NULL DEFAULT 0 COMMENT '累计作答时长（秒）',
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
    submitted_at DATETIME NULL COMMENT '提交时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_practice_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_practice_sessions_question FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    CONSTRAINT fk_practice_sessions_answer FOREIGN KEY (answer_id) REFERENCES answers(id) ON DELETE SET NULL,
    KEY idx_practice_sessions_user_question_status_id (user_id, question_id, status, id),
    KEY idx_practice_sessions_answer_id (answer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='练习会话表';

-- =========================
-- 练习记录表
-- 保存一次完整练习链路的聚合数据
-- =========================
CREATE TABLE IF NOT EXISTS practice_records (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    user_id BIGINT NOT NULL COMMENT '用户 ID',
    question_id BIGINT NOT NULL COMMENT '题目 ID',
    answer_id BIGINT NOT NULL COMMENT '答案 ID',
    review_id BIGINT NULL COMMENT '批改结果 ID',
    status VARCHAR(32) NOT NULL DEFAULT 'finished' COMMENT '练习状态',
    is_favorite BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否收藏',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '完成时间',
    CONSTRAINT fk_records_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_records_question FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    CONSTRAINT fk_records_answer FOREIGN KEY (answer_id) REFERENCES answers(id) ON DELETE CASCADE,
    CONSTRAINT fk_records_review FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE SET NULL,
    UNIQUE KEY uk_practice_records_answer_id (answer_id),
    KEY idx_practice_records_user_id_id (user_id, id),
    KEY idx_practice_records_user_status_id (user_id, status, id),
    KEY idx_practice_records_user_question_id (user_id, question_id, id),
    KEY idx_practice_records_review_id (review_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='练习记录表';

-- =========================
-- Prompt 模板表
-- 保存可编辑、可复用的提示词模板
-- =========================
CREATE TABLE IF NOT EXISTS prompt_templates (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    user_id BIGINT NULL COMMENT '所属用户 ID；为空表示全局模板',
    name VARCHAR(128) NOT NULL COMMENT '模板名称',
    template_type VARCHAR(64) NOT NULL COMMENT '模板类型，如分析、提纲、批改',
    content TEXT NOT NULL COMMENT '模板内容',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_prompt_templates_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_prompt_templates_template_type (template_type),
    KEY idx_prompt_templates_user_type (user_id, template_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Prompt 模板表';

-- =========================
-- 系统运行配置表
-- 保存阈值、词表、fallback 映射等非 prompt 配置
-- =========================
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

-- =========================
-- 题目收藏表
-- 保存用户对题目的收藏关系
-- =========================
CREATE TABLE IF NOT EXISTS question_favorites (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    user_id BIGINT NOT NULL COMMENT '用户 ID',
    question_id BIGINT NOT NULL COMMENT '题目 ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
    CONSTRAINT fk_question_favorites_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_question_favorites_question FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    UNIQUE KEY uk_question_favorites_user_question (user_id, question_id),
    KEY idx_question_favorites_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='题目收藏表';

-- =========================
-- 错题本条目表
-- 保存用户的错题归集记录，支持标记已解决
-- =========================
CREATE TABLE IF NOT EXISTS error_notebook_entries (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    user_id BIGINT NOT NULL COMMENT '用户 ID',
    question_id BIGINT NOT NULL COMMENT '题目 ID',
    review_id BIGINT NULL COMMENT '关联批改记录 ID',
    error_type VARCHAR(64) NOT NULL DEFAULT 'low_score' COMMENT '错误类型：low_score / very_low_score / missing_key_points / structure_issue / language_issue',
    error_summary TEXT COMMENT '错误摘要',
    missing_points LONGTEXT COMMENT '漏答要点 JSON',
    weak_dimensions LONGTEXT COMMENT '薄弱维度 JSON',
    status VARCHAR(32) NOT NULL DEFAULT 'unresolved' COMMENT '状态：unresolved / resolved',
    resolve_note TEXT COMMENT '解决备注',
    resolved_at DATETIME NULL COMMENT '解决时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_error_notebook_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_error_notebook_question FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    CONSTRAINT fk_error_notebook_review FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE SET NULL,
    KEY idx_error_notebook_user_id_status (user_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='错题本条目表';

-- =========================
-- 学习计划表
-- 保存 AI 或规则生成的个性化学习计划
-- =========================
CREATE TABLE IF NOT EXISTS study_plans (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    user_id BIGINT NOT NULL COMMENT '用户 ID',
    title VARCHAR(255) NOT NULL COMMENT '计划标题',
    description TEXT COMMENT '计划说明',
    plan_json LONGTEXT NOT NULL COMMENT '计划任务 JSON',
    status VARCHAR(32) NOT NULL DEFAULT 'active' COMMENT '状态：active / completed / archived',
    generated_by VARCHAR(64) NOT NULL DEFAULT 'ai' COMMENT '生成方式：ai / rule / manual',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_study_plans_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    KEY idx_study_plans_user_id_status (user_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习计划表';

-- =========================
-- 初始化默认角色
-- =========================
INSERT INTO roles (name, display_name, description)
SELECT 'visitor', '访客', '只读浏览用户'
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'visitor');

INSERT INTO roles (name, display_name, description)
SELECT 'learner', '学员', '核心训练用户'
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'learner');

INSERT INTO roles (name, display_name, description)
SELECT 'admin', '管理员', '系统维护用户'
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'admin');

INSERT INTO email_templates (template_key, template_name, subject, body_text, body_html, enabled)
SELECT
    'register_verify',
    '注册验证码',
    '{app_name} 注册验证码',
    '您好，{username}。\n\n你的注册验证码是：{code}\n有效期 {expires_minutes} 分钟。\n如果不是你本人操作，请忽略此邮件。',
    '<p>您好，{username}。</p><p>你的注册验证码是：<strong>{code}</strong></p><p>有效期 {expires_minutes} 分钟。</p><p>如果不是你本人操作，请忽略此邮件。</p>',
    TRUE
WHERE NOT EXISTS (SELECT 1 FROM email_templates WHERE template_key = 'register_verify');

INSERT INTO email_templates (template_key, template_name, subject, body_text, body_html, enabled)
SELECT
    'forgot_password_verify',
    '找回密码验证码',
    '{app_name} 找回密码验证码',
    '您好，{username}。\n\n你的找回密码验证码是：{code}\n有效期 {expires_minutes} 分钟。\n如果不是你本人操作，请忽略此邮件。',
    '<p>您好，{username}。</p><p>你的找回密码验证码是：<strong>{code}</strong></p><p>有效期 {expires_minutes} 分钟。</p><p>如果不是你本人操作，请忽略此邮件。</p>',
    TRUE
WHERE NOT EXISTS (SELECT 1 FROM email_templates WHERE template_key = 'forgot_password_verify');

INSERT INTO prompt_templates (user_id, name, template_type, content)
SELECT
    NULL,
    '批改主提示词',
    'review_system',
    '你是资深申论批改官。你的任务是基于题目、题目解析、参考要点、用户答案要点和比对证据，输出一份结构化、可直接展示的批改结果。 1. 以语义理解和写作质量判断为主，不要机械依赖固定字数阈值或简单规则直接打分。 2. 如果参考要点为空，也要基于题干要求和用户作答质量完成批改，不能因为缺少参考要点而直接判零。 3. dimensions 至少包含：审题与回应、内容覆盖、结构组织、表达与语言；如确有必要，可额外补充规则约束。 4. score_breakdown、comparison_analysis、suggestions 必须尽量完整；summary 和 analysis_explanation 必须清晰、具体。 5. suggestions 必须是可执行的修改建议，避免空泛鼓励。 6. outline_explanation 要给出下一版作答提纲或结构方向。 7. 回答风格要专业、克制、可解释，适合直接展示在批改报告页。'
WHERE NOT EXISTS (SELECT 1 FROM prompt_templates WHERE template_type = 'review_system');

INSERT INTO prompt_templates (user_id, name, template_type, content)
SELECT
    NULL,
    '批改修正提示词',
    'review_repair',
    '你是申论批改结果结构化修正器。你的任务不是重新自由发挥，而是基于已有批改结果和原始批改证据，补齐缺失或不完整的结构化字段。 1. 优先修正：dimensions、score_breakdown、comparison_analysis、suggestions、summary、analysis_explanation。 2. 尽量保持第一次批改的结论方向和总分区间，不要无依据大幅改动评分。 3. 如果原结果已有合理字段，优先保留原意，只补结构，不随意重写。 4. 缺少核心维度时必须补齐四个核心维度：审题与回应、内容覆盖、结构组织、表达与语言。 5. 缺少建议时，补充具体、可执行的修改建议，而不是泛泛而谈。 6. 输出必须仍然符合 ReviewAnalysis 结构，可直接落库。'
WHERE NOT EXISTS (SELECT 1 FROM prompt_templates WHERE template_type = 'review_repair');

INSERT INTO prompt_templates (user_id, name, template_type, content)
SELECT
    NULL,
    '批改答疑提示词',
    'review_qa',
    '你是申论批改答疑助手。你的任务是围绕已有批改结果回答用户追问。 1. 只能基于已提供的批改证据、评分拆解、要点比对、结构分析、语言分析和修改建议回答，不能杜撰新的评分依据。 2. 如果用户在追问上一轮内容，要结合历史问答连续回答，不要把每轮都当成全新问题。 3. 回答要具体、克制、可执行，优先说明为什么这样批改、问题出在哪里、下一步怎么改。 4. 如果证据不足以支撑结论，要明确说明证据不足，不要硬编。 5. 输出面向最终用户，避免暴露内部实现术语。'
WHERE NOT EXISTS (SELECT 1 FROM prompt_templates WHERE template_type = 'review_qa');

INSERT INTO prompt_templates (user_id, name, template_type, content)
SELECT
    NULL,
    '题目分析系统提示词',
    'question_analysis_system',
    '你是申论题目分析师。 1. 识别题型、核心任务、评分重点、约束条件和结构提示。 2. 输出必须结构化、简洁、准确，避免空泛表述。 3. 如果题型不明确，也要给出最可能的判断和解释。'
WHERE NOT EXISTS (SELECT 1 FROM prompt_templates WHERE template_type = 'question_analysis_system');

INSERT INTO prompt_templates (user_id, name, template_type, content)
SELECT
    NULL,
    '题目分析用户提示词',
    'question_analysis_user',
    '请根据下面信息完成题目分析，并输出结构化结果。 题目标题：{question_title} 题目内容：{question_content} 题目类型：{question_type} 参考要点：{reference_points} 请输出题型、核心要求、评分重点、约束、关键主题词和结构提示。'
WHERE NOT EXISTS (SELECT 1 FROM prompt_templates WHERE template_type = 'question_analysis_user');

INSERT INTO prompt_templates (user_id, name, template_type, content)
SELECT
    NULL,
    '参考要点抽取系统提示词',
    'reference_point_extract_system',
    '你是申论参考答案要点抽取器。 1. 将参考答案或官方要点拆成可比对的评分点。 2. 输出要结构化、稳定，方便后续内容比对。 3. 每个要点尽量提炼成清晰、独立的评分单元。'
WHERE NOT EXISTS (SELECT 1 FROM prompt_templates WHERE template_type = 'reference_point_extract_system');

INSERT INTO prompt_templates (user_id, name, template_type, content)
SELECT
    NULL,
    '参考要点抽取用户提示词',
    'reference_point_extract_user',
    '请根据下面信息抽取参考要点。 参考答案/官方要点： {reference_points_text} 题目类型：{question_type} 评分重点：{scoring_focus} 题目解析：{question_analysis_json} 请输出可比对的参考要点，每个要点包含 text、keywords、weight、evidence、matched_keywords。'
WHERE NOT EXISTS (SELECT 1 FROM prompt_templates WHERE template_type = 'reference_point_extract_user');

INSERT INTO prompt_templates (user_id, name, template_type, content)
SELECT
    NULL,
    '用户要点抽取系统提示词',
    'user_point_extract_system',
    '你是申论用户作答要点抽取器。 1. 将用户作答拆成可比对的结构化要点。 2. 输出要结构化、稳定，方便后续批改和要点比对。 3. 保留答题原意，不要改写成立场不同的内容。'
WHERE NOT EXISTS (SELECT 1 FROM prompt_templates WHERE template_type = 'user_point_extract_system');

INSERT INTO prompt_templates (user_id, name, template_type, content)
SELECT
    NULL,
    '用户要点抽取用户提示词',
    'user_point_extract_user',
    '请根据下面信息抽取用户作答要点。 题目标题：{question_title} 题目内容：{question_content} 题目类型：{question_type} 题目解析：{question_analysis_json} 参考要点：{reference_points_text} 作答内容：{answer_content} 请输出可比对的用户作答要点，每个要点包含 text、keywords、weight、evidence、matched_keywords。'
WHERE NOT EXISTS (SELECT 1 FROM prompt_templates WHERE template_type = 'user_point_extract_user');

INSERT INTO prompt_templates (user_id, name, template_type, content)
SELECT
    NULL,
    '提纲生成系统提示词',
    'outline_generate_system',
    '你是申论提纲生成器。 1. 根据题目解析、命中要点和遗漏要点，给出下一版可直接落笔的提纲。 2. 输出要简洁、分层清晰、可执行。 3. 重点帮助用户补齐漏答内容并优化结构。'
WHERE NOT EXISTS (SELECT 1 FROM prompt_templates WHERE template_type = 'outline_generate_system');

INSERT INTO prompt_templates (user_id, name, template_type, content)
SELECT
    NULL,
    '提纲生成用户提示词',
    'outline_generate_user',
    '请根据下面信息生成下一版作答提纲。 题目类型：{question_type} 评分重点：{scoring_focus} 遗漏要点：{missing_points} 命中要点：{matched_points} 题目解析：{question_analysis_json} 要点比对结果：{comparison_json} 请输出下一版写作提纲和分点建议。'
WHERE NOT EXISTS (SELECT 1 FROM prompt_templates WHERE template_type = 'outline_generate_user');

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
