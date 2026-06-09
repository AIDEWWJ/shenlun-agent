# 申论 Agent 接口设计

## 设计目标

接口层负责承接前端请求，并将申论训练任务分发给 Agent 编排层与模型适配层，确保不同模型和配置能够统一接入。

## 当前接口状态

> 当前代码的 API 入口由 `backend/main.py` 统一挂载各 `modules/*/api.py` 路由。  
> 用户侧题库正在向“统一题库页”收敛：前端主入口统一使用 `/papers`，不保留 `/questions` 页面路由；后端仍提供 `/api/questions` 作为题目数据接口，并提供 `/api/papers` 作为试卷数据接口。  
> 练习链路当前同时存在单题 `/api/practice-sessions/*` 与试卷 `/api/paper-sessions/*`，后续目标是按练习系统设计逐步统一。

### 已实现

#### 1. 健康检查

- **接口**：`GET /api/health`
- **用途**：检查服务是否存活
- **输出**：`{"status": "ok"}`

#### 2. 认证与用户

- **接口**：`POST /api/auth/register`
- **用途**：校验验证码后注册用户账号
- **输入**：`username`、`password`、`email`、`verification_code`
- **输出**：用户信息

- **接口**：`POST /api/auth/register/send-code`
- **用途**：发送注册验证码
- **输入**：`username`、`email`
- **输出**：发送结果

- **接口**：`POST /api/auth/login`
- **用途**：登录并获取访问令牌
- **输入**：`username`、`password`
- **输出**：`access_token`、`token_type`

- **接口**：`GET /api/auth/me`
- **用途**：获取当前登录用户信息
- **认证**：Bearer Token
- **输出**：用户信息与角色列表

- **接口**：`PUT /api/auth/me`
- **用途**：更新当前用户的个人信息
- **输入**：`username`、`email`（均可选）
- **输出**：更新后的用户信息

- **接口**：`POST /api/auth/me/password`
- **用途**：修改当前用户密码
- **输入**：`current_password`、`new_password`
- **输出**：修改结果

- **接口**：`POST /api/auth/forgot-password`
- **用途**：校验验证码后重置密码
- **输入**：`username`、`email`、`new_password`、`verification_code`
- **输出**：重置结果

- **接口**：`POST /api/auth/forgot-password/send-code`
- **用途**：发送找回密码验证码
- **输入**：`username`、`email`
- **输出**：发送结果

#### 3. 用户 AI 配置

- **接口**：`GET /api/ai-configs/me`
- **用途**：查询当前用户的 AI 配置列表
- **支持参数**：`page`、`page_size`
- **说明**：用户 AI 配置只负责模型与接口运行参数，不负责系统级批改/答疑提示词

- **接口**：`POST /api/ai-configs/me`
- **用途**：创建个人 AI 配置
- **可配置字段**：`provider`、`model_name`、`api_key`、`base_url`、`temperature`、`is_default`

- **接口**：`PUT /api/ai-configs/me/{config_id}`
- **用途**：更新个人 AI 配置
- **可更新字段**：`provider`、`model_name`、`api_key`、`base_url`、`temperature`、`is_default`

- **接口**：`DELETE /api/ai-configs/me/{config_id}`
- **用途**：删除个人 AI 配置

- **接口**：`POST /api/ai-configs/me/{config_id}/default`
- **用途**：将某个个人配置设为默认

- **接口**：`GET /api/ai-configs/system-default`
- **用途**：获取系统默认 AI 配置

#### 4. 管理员 AI 配置

- **接口**：`GET /api/admin/ai-configs/system`
- **用途**：列出系统级 AI 配置
- **权限**：管理员
- **支持参数**：`page`、`page_size`

- **接口**：`POST /api/admin/ai-configs/system`
- **用途**：创建系统级 AI 配置
- **权限**：管理员

- **接口**：`PUT /api/admin/ai-configs/system/{config_id}`
- **用途**：更新系统级 AI 配置
- **权限**：管理员

- **接口**：`DELETE /api/admin/ai-configs/system/{config_id}`
- **用途**：删除系统级 AI 配置
- **权限**：管理员

- **接口**：`POST /api/admin/ai-configs/system/{config_id}/default`
- **用途**：将某个系统配置设为默认
- **权限**：管理员
- **说明**：系统级 AI 配置同样只负责模型与接口运行参数；批改和答疑提示词改由管理员 Prompt 管理维护

#### 5. 管理员用户管理

- **接口**：`GET /api/admin/users`
- **用途**：查询用户列表
- **权限**：管理员
- **支持参数**：`page`、`page_size`

- **接口**：`GET /api/admin/users/{user_id}`
- **用途**：查询单个用户详情
- **权限**：管理员

- **接口**：`POST /api/admin/users`
- **用途**：创建用户
- **权限**：管理员

- **接口**：`PUT /api/admin/users/{user_id}`
- **用途**：更新用户信息、密码、状态与角色
- **权限**：管理员

- **接口**：`DELETE /api/admin/users/{user_id}`
- **用途**：删除用户
- **权限**：管理员

#### 6. 练习与答案接口

- **接口**：`POST /api/answers`
- **用途**：创建答案版本 / 草稿
- **认证**：Bearer Token

- **接口**：`GET /api/answers/{answer_id}`
- **用途**：获取单个答案详情
- **认证**：Bearer Token

- **接口**：`PUT /api/answers/{answer_id}`
- **用途**：更新未批改答案
- **认证**：Bearer Token

- **接口**：`GET /api/questions/{question_id}/answers`
- **用途**：查询某题目的答案版本列表
- **认证**：Bearer Token
- **支持参数**：`page`、`page_size`

- **接口**：`PATCH /api/practice-records/{record_id}/favorite`
- **用途**：切换练习记录收藏状态
- **认证**：Bearer Token

- **接口**：`POST /api/analyze`
- **用途**：分析申论题目
- **当前状态**：已接入真实分析链路和回退逻辑

- **接口**：`POST /api/outline`
- **用途**：生成作答提纲
- **当前状态**：已接入真实提纲链路和回退逻辑

- **接口**：`POST /api/review`
- **用途**：批改用户答案
- **输入**：`question_id`、`answer_id`、`reference_points`、`use_llm`

- **接口**：`POST /api/review/from-content`
- **用途**：基于答案正文直接发起批改，并按需要创建新答案版本
- **输入**：`question_id`、`answer_content`、`answer_id?`、`reference_points`、`use_llm`

- **接口**：`GET /api/practice-records`
- **用途**：查询练习记录
- **认证**：Bearer Token
- **支持参数**：`page`、`page_size`、`question_id`、`question_type`、`answer_version_no`、`status`、`review_id`、`score_min`、`score_max`、`model_provider`、`model_name`、`is_favorite`、`date_from`、`date_to`

- **接口**：`GET /api/practice-records/{record_id}`
- **用途**：查询练习记录详情
- **认证**：Bearer Token

#### 7. 批改记录接口

- **接口**：`GET /api/reviews`
- **用途**：查询当前用户的批改记录列表
- **认证**：Bearer Token
- **支持参数**：`page`、`page_size`、`question_id`、`question_type`

- **接口**：`GET /api/reviews/{review_id}`
- **用途**：查询批改详情
- **认证**：Bearer Token

- **接口**：`POST /api/reviews/{review_id}/qa`
- **用途**：围绕某次批改结果发起追问答疑
- **认证**：Bearer Token
- **输入**：`question`、`use_llm`、`conversation_id?`、`parent_message_id?`
- **说明**：首次提问可不传会话信息；后续追问可携带 `conversation_id` 与上一条 `parent_message_id`

- **接口**：`GET /api/reviews/{review_id}/qa`
- **用途**：查询某次批改的答疑记录
- **认证**：Bearer Token
- **支持参数**：`page`、`page_size`、`conversation_id`

#### 8. 题库接口

- **接口**：`GET /api/questions`
- **用途**：查询题库列表
- **认证**：Bearer Token
- **支持参数**：`page`、`page_size`、`keyword`、`question_type`、`tag`、`source`、`user_id`、`sort_by`、`sort_order`
- **说明**：`user_id` 仅管理员可用，普通用户传入将返回 403
- **返回补充**：响应中包含 `applied_filters` 和 `applied_sort`

- **接口**：`GET /api/questions/{question_id}`
- **用途**：查询题目详情
- **认证**：Bearer Token

- **接口**：`GET /api/questions/filters`
- **用途**：获取题库筛选项元数据
- **认证**：Bearer Token
- **支持参数**：`user_id`
- **说明**：`user_id` 仅管理员可用

- **接口**：`POST /api/questions`
- **用途**：创建题目
- **认证**：Bearer Token

- **接口**：`POST /api/questions/import`
- **用途**：批量导入题库
- **认证**：Bearer Token

- **接口**：`PUT /api/questions/{question_id}`
- **用途**：更新题目
- **认证**：Bearer Token

- **接口**：`DELETE /api/questions/{question_id}`
- **用途**：删除题目
- **认证**：Bearer Token

### 规划中

- 错题本与复盘接口
- 模型适配与流式输出接口

#### 12. 学习概览与统计（已实现）

- **接口**：`GET /api/dashboard/me`
- **用途**：获取当前用户的学习概览信息
- **认证**：Bearer Token
- **返回**：`total_practices`、`total_reviews`、`avg_score`、`latest_score`、`best_score`、`streak_days`、`weak_question_types`、`recent_items`

- **接口**：`GET /api/stats/by-question-type`
- **用途**：获取用户在各题型下的练习与得分统计
- **认证**：Bearer Token
- **支持参数**：`date_from`、`date_to`
- **返回**：`question_type`、`count`、`avg_score`、`best_score`、`latest_score`

- **接口**：`GET /api/questions/random`
- **用途**：按筛选条件随机返回 1 道题
- **认证**：Bearer Token
- **支持参数**：`question_type`、`tag`、`source`

- **接口**：`POST /api/answers/{answer_id}/duplicate`
- **用途**：基于旧答案创建新版本
- **认证**：Bearer Token
- **输入**：`content?`（可选，为空则复制原内容）

- **接口**：`POST /api/reviews/{review_id}/rerun`
- **用途**：对同一答案重新发起批改
- **认证**：Bearer Token
- **输入**：`reference_points?`、`use_llm`

#### 13. 流式接口（已实现）

- **接口**：`POST /api/review/stream`
- **用途**：基于答案正文发起流式批改，通过 SSE 逐步返回批改进度
- **认证**：Bearer Token
- **输入**：同 `POST /api/review/from-content`
- **SSE 事件**：
  - `step`：批改步骤进度（step/step_name/order/status/result）
  - `complete`：批改完成（answer_id/review_id/analysis）
  - `error`：批改出错（message）

- **接口**：`POST /api/review/from-content/stream`
- **用途**：同上，提供更语义化的路径别名

- **接口**：`POST /api/reviews/{review_id}/qa/stream`
- **用途**：围绕批改结果发起流式答疑，通过 SSE 逐步返回答疑内容
- **认证**：Bearer Token
- **输入**：`question`、`use_llm`、`conversation_id?`、`parent_message_id?`
- **SSE 事件**：
  - `thinking`：AI 正在思考
  - `chunk`：答疑内容片段（流式文本）
  - `complete`：答疑完成（message_id/conversation_id/answer_text/evidence_refs）
  - `error`：出错

## 统一响应格式

建议所有业务接口返回统一结构：

- `success`：是否成功
- `message`：提示信息
- `data`：核心结果
- `error`：错误信息（失败时返回）

当前实现中：

- 所有业务接口统一返回 `{ success, message, data, error }`
- 认证、AI 配置、练习、健康检查接口已全部接入统一返回封装
- 校验错误、HTTP 错误、未捕获异常已由全局异常处理器统一处理

## 异常处理约定

- 400/401/403/404 等业务错误：返回统一错误结构
- 422 参数校验错误：返回 `VALIDATION_ERROR`
- 500 未知异常：返回 `INTERNAL_SERVER_ERROR`
- 前端只需读取 `message` 和 `data` 即可完成大部分交互

## 认证约定

- 登录后返回 Bearer Token
- 前端请求头使用 `Authorization: Bearer <token>`
- 当前用户身份由 `sub` 字段解析
- 用户状态为 `active` 时才允许访问受保护接口

## 设计原则

- 接口尽量保持简洁
- 所有 AI 参数均可配置
- 同一接口可兼容不同模型
- 后续支持流式输出与多轮交互

## 数据模型摘要

- `UserRead`：`id`、`username`、`email`、`status`、`created_at`、`roles`
- `Token`：`access_token`、`token_type`
- `AiConfigRead`：`id`、`user_id`、`scope`、`created_by`、`provider`、`model_name`、`base_url`、`temperature`、`is_default`、`created_at`
- `AiConfigListResponse`：`items`、`total`、`page`、`page_size`
- `PromptTemplateRead`：`id`、`user_id`、`name`、`template_type`、`content`、`created_at`
- `PromptTemplateListResponse`：`items`、`total`
- `SystemConfigRead`：`id`、`category`、`config_key`、`name`、`content_json`、`created_at`、`updated_at`
- `SystemConfigListResponse`：`items`、`total`
- `QuestionRead`：`id`、`user_id`、`title`、`content`、`question_type`、`tags`、`source`、`created_at`
- `QuestionListResponse`：`items`、`total`、`page`、`page_size`
- `AnswerRead`：`id`、`question_id`、`user_id`、`content`、`version_no`、`created_at`、`question_title`、`question_type`、`reviewed`、`review_id`
- `AnswerListResponse`：`items`、`total`、`page`、`page_size`
- `ReviewListResponse`：`items`、`total`、`page`、`page_size`
- `PracticeRecordListResponse`：`items`、`total`、`page`、`page_size`

## 当前接口落地说明

- `app/api/router.py` 已统一聚合 `health`、`auth`、`ai_configs`、`admin_users`、`admin_emails`、`practice`、`questions` 等路由。
- `practice` 相关接口已经进入新的 `modules/practice` 业务入口，后续会继续把题库、review、auth 等模块收敛。

#### 9. 管理员邮件管理

- **接口**：`GET /api/admin/email/configs`
- **用途**：列出邮件发送配置
- **权限**：管理员
- **支持参数**：`page`、`page_size`

- **接口**：`POST /api/admin/email/configs`
- **用途**：创建邮件发送配置
- **权限**：管理员

- **接口**：`PUT /api/admin/email/configs/{config_id}`
- **用途**：更新邮件发送配置
- **权限**：管理员

- **接口**：`DELETE /api/admin/email/configs/{config_id}`
- **用途**：删除邮件发送配置
- **权限**：管理员

- **接口**：`GET /api/admin/email/templates`
- **用途**：列出邮件模板
- **权限**：管理员
- **支持参数**：`page`、`page_size`

- **接口**：`POST /api/admin/email/templates`
- **用途**：创建邮件模板
- **权限**：管理员

- **接口**：`PUT /api/admin/email/templates/{template_key}`
- **用途**：更新邮件模板
- **权限**：管理员

- **接口**：`DELETE /api/admin/email/templates/{template_key}`
- **用途**：删除邮件模板
- **权限**：管理员

#### 10. 管理员 Prompt 管理

- **接口**：`GET /api/admin/prompts`
- **用途**：列出系统级批改/答疑提示词
- **权限**：管理员

- **接口**：`PUT /api/admin/prompts/{template_type}`
- **用途**：更新系统级提示词
- **权限**：管理员
- **支持类型**：
  - `review_system`
  - `review_repair`
  - `review_qa`
  - `question_analysis_system`
  - `question_analysis_user`
  - `reference_point_extract_system`
  - `reference_point_extract_user`
  - `user_point_extract_system`
  - `user_point_extract_user`
  - `outline_generate_system`
  - `outline_generate_user`

#### 11. 管理员系统运行配置

- **接口**：`GET /api/admin/system-configs`
- **用途**：列出系统级运行时配置
- **权限**：管理员

- **接口**：`PUT /api/admin/system-configs/{config_key}`
- **用途**：更新系统级运行时配置
- **权限**：管理员
- **支持类型**：
  - `point_compare`
  - `structure_analysis`
  - `language_analysis`
  - `rule_validation`
  - `practice_fallback`
- **说明**：
  - `point_compare`：要点比对阈值
  - `structure_analysis`：结构分析词表与加分规则
  - `language_analysis`：语言分析词表与阈值
  - `rule_validation`：规则校验阈值与惩罚分
  - `practice_fallback`：无 LLM / 回退场景下的题型映射与结构提示

---

## 十二、下一阶段新增接口设计

以下接口按“申论刷题训练闭环”排序，优先补能直接提升用户训练体验和复盘效率的能力。

## 12.1 P0：优先补齐

### 1. 用户学习概览

- **接口**：`GET /api/dashboard/me`
- **用途**：获取当前用户的学习概览信息
- **认证**：Bearer Token
- **建议返回**：
  - `total_practices`
  - `total_reviews`
  - `avg_score`
  - `latest_score`
  - `streak_days`
  - `weak_question_types`
  - `recent_items`

### 2. 随机抽题

- **接口**：`GET /api/questions/random`
- **用途**：按筛选条件随机返回 1 道题
- **认证**：Bearer Token
- **支持参数**：
  - `question_type`
  - `tag`
  - `source`

### 3. 推荐题目

- **接口**：`GET /api/questions/recommendations`
- **用途**：根据用户历史练习情况推荐题目
- **认证**：Bearer Token
- **支持参数**：
  - `limit`
- **建议返回**：
  - `question_id`
  - `title`
  - `question_type`
  - `tags`
  - `reason`

### 4. 获取某题最近答案

- **接口**：`GET /api/questions/{question_id}/latest-answer`
- **用途**：获取当前用户在某道题上的最近一次答案版本
- **认证**：Bearer Token
- **建议返回**：
  - `answer_id`
  - `version_no`
  - `content`
  - `reviewed`
  - `review_id`

### 5. 复制答案版本

- **接口**：`POST /api/answers/{answer_id}/duplicate`
- **用途**：基于旧答案创建新版本
- **认证**：Bearer Token
- **建议输入**：
  - `content?`
- **建议返回**：
  - `AnswerRead`

### 6. 重新批改

- **接口**：`POST /api/reviews/{review_id}/rerun`
- **用途**：对同一答案重新发起批改
- **认证**：Bearer Token
- **建议输入**：
  - `reference_points?`
  - `use_llm`
- **建议返回**：
  - `answer_id`
  - `review_id`
  - `analysis`

### 7. 批改结果对比

- **接口**：`GET /api/reviews/{review_id}/compare/{target_review_id}`
- **用途**：对比两次批改结果
- **认证**：Bearer Token
- **建议返回**：
  - `base_review_id`
  - `target_review_id`
  - `score_diff`
  - `dimension_diffs`
  - `issues_added`
  - `issues_resolved`
  - `suggestion_changes`

### 8. 按题型统计

- **接口**：`GET /api/stats/by-question-type`
- **用途**：获取用户在各题型下的练习与得分统计
- **认证**：Bearer Token
- **支持参数**：
  - `date_from`
  - `date_to`
- **建议返回**：
  - `question_type`
  - `count`
  - `avg_score`
  - `best_score`
  - `latest_score`

## 12.2 P1：推荐补充

### 错题与复盘（已实现）

- `GET /api/error-notebook` ✅ 已实现 — 分页查询错题本，支持按状态和题型筛选
- `POST /api/error-notebook/generate` ✅ 已实现 — 基于低分批改记录自动生成错题本条目
- `PATCH /api/error-notebook/{id}/resolve` ✅ 已实现 — 标记错题已解决

### 趋势与计划（已实现）

- `GET /api/stats/trend` ✅ 已实现 — 得分趋势（按天聚合）
- `POST /api/study-plans/generate` ✅ 已实现 — AI/规则生成个性化学习计划
- `GET /api/study-plans/me` ✅ 已实现 — 查询用户学习计划列表

### 收藏与专题（已实现）

- `PATCH /api/questions/{question_id}/favorite` ✅ 已实现
- `GET /api/questions/favorites` ✅ 已实现

### 后台抽检

- `GET /api/admin/reviews`
- `GET /api/admin/metrics`
- `POST /api/admin/prompts/{template_type}/preview`
- `POST /api/admin/system-configs/{config_key}/validate`

## 12.3 设计原则

- 用户侧接口默认只操作当前登录用户数据，不再额外暴露 `user_id`
- 推荐类接口必须返回 `reason`，否则前端无法解释推荐依据
- 对比类接口返回“差异”而不是重复整份原报告
- 统计类接口优先返回聚合结果，不返回大列表
- 新接口继续保持统一响应结构 `{ success, message, data, error }`
