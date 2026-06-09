-- ============================================================
-- 增量迁移脚本：添加 scope 字段 + 新建表
-- 适用于已有数据库，不会丢失现有数据
-- ============================================================

USE shenlun_agent;

-- 1. questions 表添加 scope 字段
ALTER TABLE questions
    ADD COLUMN scope VARCHAR(16) NOT NULL DEFAULT 'user' COMMENT '题库范围：system / user'
    AFTER user_id;

ALTER TABLE questions
    ADD KEY idx_questions_scope_id (scope, id);

-- 2. 题目收藏表
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

-- 3. 错题本条目表
CREATE TABLE IF NOT EXISTS error_notebook_entries (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    user_id BIGINT NOT NULL COMMENT '用户 ID',
    question_id BIGINT NOT NULL COMMENT '题目 ID',
    review_id BIGINT NULL COMMENT '关联批改记录 ID',
    question_title VARCHAR(255) NOT NULL COMMENT '题目标题',
    question_type VARCHAR(64) COMMENT '题型',
    score INT COMMENT '批改得分',
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
    KEY idx_error_notebook_user_id_status (user_id, status),
    KEY idx_error_notebook_user_question_type (user_id, question_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='错题本条目表';

-- 4. 学习计划表
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
