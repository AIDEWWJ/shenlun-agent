-- 索引与约束优化脚本
-- 用途：
-- 1. 给已存在的 MySQL 数据库补齐高频查询索引
-- 2. 对与当前服务逻辑一致的一对一关系补充唯一约束
--
-- 执行前建议：
-- 1. 先备份数据库
-- 2. 在低峰期执行
-- 3. 如历史库里 reviews.answer_id 存在重复值，需要先人工清理再加唯一约束

USE shenlun_agent;

-- practice_records 在旧逻辑下可能重复写入同一个 answer_id，这里保留最新一条
DELETE pr_old
FROM practice_records pr_old
JOIN practice_records pr_new
  ON pr_old.answer_id = pr_new.answer_id
 AND pr_old.id < pr_new.id;

ALTER TABLE user_roles
    ADD INDEX idx_user_roles_role_id (role_id);

ALTER TABLE email_configs
    ADD INDEX idx_email_configs_enabled_id (enabled, id);

ALTER TABLE email_verification_codes
    ADD INDEX idx_email_verification_email_purpose_id (email, purpose, id),
    ADD INDEX idx_email_verification_expires_at (expires_at);

ALTER TABLE ai_configs
    ADD INDEX idx_ai_configs_scope_user_default_created (scope, user_id, is_default, created_at),
    ADD INDEX idx_ai_configs_created_by (created_by),
    ADD INDEX idx_ai_configs_provider_model (provider, model_name);

ALTER TABLE questions
    ADD INDEX idx_questions_user_id_id (user_id, id),
    ADD INDEX idx_questions_question_type_id (question_type, id),
    ADD INDEX idx_questions_source_id (source, id);

ALTER TABLE answers
    ADD UNIQUE KEY uk_answers_question_user_version (question_id, user_id, version_no);

ALTER TABLE reviews
    ADD UNIQUE KEY uk_reviews_answer_id (answer_id),
    ADD INDEX idx_reviews_user_id_id (user_id, id),
    ADD INDEX idx_reviews_question_id_id (question_id, id);

ALTER TABLE review_steps
    ADD INDEX idx_review_steps_review_order_id (review_id, order_no, id);

ALTER TABLE practice_records
    ADD UNIQUE KEY uk_practice_records_answer_id (answer_id),
    ADD INDEX idx_practice_records_user_id_id (user_id, id),
    ADD INDEX idx_practice_records_user_status_id (user_id, status, id),
    ADD INDEX idx_practice_records_user_question_id (user_id, question_id, id),
    ADD INDEX idx_practice_records_review_id (review_id);

ALTER TABLE prompt_templates
    ADD INDEX idx_prompt_templates_user_type (user_id, template_type);
