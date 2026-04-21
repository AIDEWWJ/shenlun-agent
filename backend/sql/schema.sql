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
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
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
    KEY idx_email_verification_email (email),
    KEY idx_email_verification_purpose (purpose),
    KEY idx_email_verification_expire (expires_at)
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
    UNIQUE KEY uk_user_role (user_id, role_id)
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
    is_default BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否默认配置',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_ai_configs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_ai_configs_creator FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    KEY idx_ai_configs_user_id (user_id),
    KEY idx_ai_configs_scope (scope),
    KEY idx_ai_configs_created_by (created_by),
    KEY idx_ai_configs_user_default (user_id, is_default),
    KEY idx_ai_configs_provider_model (provider, model_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI 配置表';

-- =========================
-- 题目表
-- 保存申论题目内容、分类和来源
-- =========================
CREATE TABLE IF NOT EXISTS questions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    user_id BIGINT NOT NULL COMMENT '所属用户 ID',
    title VARCHAR(255) NOT NULL COMMENT '题目标题',
    content TEXT NOT NULL COMMENT '题目正文',
    question_type VARCHAR(64) COMMENT '题型，如概括题、对策题、综合分析题',
    tags VARCHAR(255) COMMENT '标签，逗号分隔',
    source VARCHAR(255) COMMENT '题目来源',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_questions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
    CONSTRAINT fk_answers_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='答案表';

-- =========================
-- 批改结果表
-- 保存 AI 对答案的评分、点评和复盘结论
-- =========================
CREATE TABLE IF NOT EXISTS reviews (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    answer_id BIGINT NOT NULL COMMENT '答案 ID',
    score INT COMMENT '评分',
    strengths TEXT COMMENT '优点',
    issues TEXT COMMENT '问题',
    suggestions TEXT COMMENT '修改建议',
    summary TEXT COMMENT '复盘总结',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
    CONSTRAINT fk_reviews_answer FOREIGN KEY (answer_id) REFERENCES answers(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='批改结果表';

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
    CONSTRAINT fk_records_review FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE SET NULL
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
    CONSTRAINT fk_prompt_templates_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Prompt 模板表';

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
