# 申论 Agent 索引优化版

## 说明

本文档用于说明在首版表结构基础上，哪些字段建议增加索引，以提升常用查询性能。

## 一、索引设计原则

- 优先覆盖高频查询字段
- 外键字段默认建议建立索引
- 唯一字段使用唯一索引
- 不盲目添加过多复合索引，避免写入成本过高

## 二、建议索引清单

### 1. `users`

```sql
CREATE UNIQUE INDEX uk_users_username ON users(username);
CREATE UNIQUE INDEX uk_users_email ON users(email);
```

**说明：**
- 用户登录和找回账号时高频使用
- `username` 和 `email` 都应唯一

### 2. `roles`

```sql
CREATE UNIQUE INDEX uk_roles_name ON roles(name);
```

**说明：**
- 角色编码固定且需要唯一

### 3. `user_roles`

```sql
CREATE UNIQUE INDEX uk_user_roles_user_role ON user_roles(user_id, role_id);
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);
```

**说明：**
- 用户授权查询高频
- 支持按用户查角色、按角色查用户

### 4. `ai_configs`

```sql
CREATE INDEX idx_ai_configs_user_id ON ai_configs(user_id);
CREATE INDEX idx_ai_configs_user_default ON ai_configs(user_id, is_default);
CREATE INDEX idx_ai_configs_provider_model ON ai_configs(provider, model_name);
```

**说明：**
- 用户读取自己的 AI 配置
- 默认配置获取很常见
- 后续可按模型提供方筛选

### 5. `questions`

```sql
CREATE INDEX idx_questions_user_id ON questions(user_id);
CREATE INDEX idx_questions_question_type ON questions(question_type);
CREATE INDEX idx_questions_created_at ON questions(created_at);
```

**说明：**
- 练习列表、题型筛选、最近题目排序都会用到

### 6. `answers`

```sql
CREATE INDEX idx_answers_question_id ON answers(question_id);
CREATE INDEX idx_answers_user_id ON answers(user_id);
CREATE INDEX idx_answers_question_user ON answers(question_id, user_id);
CREATE INDEX idx_answers_created_at ON answers(created_at);
```

**说明：**
- 同题历史答案查询高频
- 用户维度历史记录查询高频

### 7. `reviews`

```sql
CREATE INDEX idx_reviews_answer_id ON reviews(answer_id);
CREATE INDEX idx_reviews_created_at ON reviews(created_at);
```

**说明：**
- 答案详情页会根据 answer_id 获取批改结果

### 8. `practice_records`

```sql
CREATE INDEX idx_practice_records_user_id ON practice_records(user_id);
CREATE INDEX idx_practice_records_question_id ON practice_records(question_id);
CREATE INDEX idx_practice_records_answer_id ON practice_records(answer_id);
CREATE INDEX idx_practice_records_review_id ON practice_records(review_id);
CREATE INDEX idx_practice_records_user_status ON practice_records(user_id, status);
CREATE INDEX idx_practice_records_user_favorite ON practice_records(user_id, is_favorite);
CREATE INDEX idx_practice_records_created_at ON practice_records(created_at);
```

**说明：**
- 历史记录、收藏、状态筛选都需要
- 这是最值得优化的核心表之一

### 9. `prompt_templates`

```sql
CREATE INDEX idx_prompt_templates_user_id ON prompt_templates(user_id);
CREATE INDEX idx_prompt_templates_type ON prompt_templates(template_type);
CREATE INDEX idx_prompt_templates_user_type ON prompt_templates(user_id, template_type);
```

**说明：**
- 用户模板加载和模板分类查询频繁

## 三、推荐复合索引场景

### 场景 1：用户练习历史查询

常见条件：
- `user_id`
- `status`
- `created_at`

建议：

```sql
CREATE INDEX idx_practice_records_user_status_created ON practice_records(user_id, status, created_at);
```

### 场景 2：用户题目列表

常见条件：
- `user_id`
- `created_at`

建议：

```sql
CREATE INDEX idx_questions_user_created ON questions(user_id, created_at);
```

### 场景 3：用户答案版本查找

常见条件：
- `question_id`
- `user_id`
- `version_no`

建议：

```sql
CREATE INDEX idx_answers_question_user_version ON answers(question_id, user_id, version_no);
```

## 四、首版优化建议

第一版不要一次性加太多索引，建议至少保留以下关键索引：

- `users.username`
- `roles.name`
- `user_roles(user_id, role_id)`
- `ai_configs.user_id`
- `questions.user_id`
- `answers.question_id`
- `answers.user_id`
- `reviews.answer_id`
- `practice_records.user_id`
- `practice_records.user_id, status`

## 五、后续优化方向

- 根据真实查询 SQL 再补复合索引
- 使用 `EXPLAIN` 分析慢查询
- 为分页和排序场景补充联合索引
- 避免对低基数字段过度建索引
