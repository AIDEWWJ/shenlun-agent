# 申论 Agent 建表说明文档

## 说明

本文档用于解释 MySQL 表结构设计的业务含义、字段作用和表之间的关系，方便开发、联调与后续维护。

## 一、表结构总览

| 表名 | 说明 | 作用 |
|---|---|---|
| `users` | 系统用户表 | 保存登录用户基础信息 |
| `roles` | 系统角色表 | 保存访客、学员、管理员角色定义 |
| `user_roles` | 用户角色关联表 | 实现 RBAC 权限模型 |
| `ai_configs` | AI 配置表 | 保存用户自定义模型配置 |
| `questions` | 题目表 | 保存申论题目内容与分类 |
| `answers` | 答案表 | 保存用户提交的答案版本 |
| `reviews` | 批改结果表 | 保存 AI 批改评分与建议 |
| `practice_records` | 练习记录表 | 聚合一次完整练习链路 |
| `prompt_templates` | Prompt 模板表 | 保存可复用的提示词模板 |

## 二、核心表说明

### 1. `users`

**用途**：保存系统登录用户的基础信息。

**关键字段：**

- `username`：唯一用户名
- `email`：邮箱，支持为空
- `password_hash`：密码加密后的值
- `status`：账号状态，默认 `active`
- `created_at`、`updated_at`：审计字段

**业务说明：**

- 一个用户可以拥有多个角色
- 一个用户可以配置多个 AI 模型
- 一个用户可以创建多道题目与答案

### 2. `roles`

**用途**：定义系统内置角色。

**默认角色：**

- `visitor`：访客
- `learner`：学员
- `admin`：管理员

**业务说明：**

- 角色是权限控制的基础
- 角色本身不直接对应页面，而是对应权限集合

### 3. `user_roles`

**用途**：建立用户与角色之间的多对多关系。

**业务说明：**

- 用于实现 RBAC
- 支持一个用户同时拥有多个角色
- 建议对 `(user_id, role_id)` 做唯一约束

### 4. `ai_configs`

**用途**：保存用户个人 AI 配置和管理员维护的系统默认配置。

**关键字段：**

- `scope`：配置范围，`system` 或 `user`
- `user_id`：所属用户，系统默认配置可为空
- `created_by`：创建人，通常由管理员记录
- `provider`：模型提供方，如 OpenAI、DeepSeek、Qwen
- `model_name`：模型名
- `api_key`：模型密钥，建议加密保存
- `base_url`：第三方服务地址
- `temperature`：生成温度
- `system_prompt`：系统提示词
- `is_default`：默认配置标记

**业务说明：**

- 一个用户可有多个个人配置方案
- 管理员可在后台维护系统默认配置
- 用户在界面中切换模型时，本质是切换配置记录，而不是修改环境变量

### 5. `questions`

**用途**：保存申论题目全文和分类信息。

**关键字段：**

- `title`：题目标题
- `content`：题干全文
- `question_type`：题型
- `tags`：标签
- `source`：来源

**业务说明：**

- 题目通常由学员创建或导入
- 一道题可以对应多个答案版本

### 6. `answers`

**用途**：保存用户提交的答案文本。

**关键字段：**

- `question_id`：题目关联
- `user_id`：答题用户
- `content`：答案内容
- `version_no`：答案版本号

**业务说明：**

- 支持同一题多次作答
- 可用于答案迭代与前后对比

### 7. `reviews`

**用途**：保存 AI 的批改结果。

**关键字段：**

- `score`：评分
- `strengths`：优点
- `issues`：问题
- `suggestions`：修改建议
- `summary`：复盘总结

**业务说明：**

- 一次答案对应一条批改结果
- 后续可以支持多轮批改版本

### 8. `practice_records`

**用途**：记录完整练习流程的聚合结果。

**关键字段：**

- `user_id`：用户
- `question_id`：题目
- `answer_id`：答案
- `review_id`：批改结果
- `status`：练习状态
- `is_favorite`：收藏标记

**业务说明：**

- 用于首页历史、错题本、收藏列表等场景
- 可以视为练习主表

### 9. `prompt_templates`

**用途**：保存可重复使用的 Prompt 模板。

**关键字段：**

- `user_id`：所属用户，空值表示全局模板
- `name`：模板名称
- `template_type`：模板类型
- `content`：模板内容

**业务说明：**

- 支持用户自定义提示词
- 可用于分析、提纲、批改等多个 Agent 阶段

## 三、关系说明

- `users` 与 `roles`：多对多
- `users` 与 `ai_configs`：一对多
- `users` 与 `questions`：一对多
- `questions` 与 `answers`：一对多
- `answers` 与 `reviews`：一对一或一对多演进
- `practice_records` 负责把题目、答案、批改串起来

## 四、MVP 优先级

第一版建议先稳定以下表：

1. `users`
2. `roles`
3. `user_roles`
4. `ai_configs`
5. `questions`
6. `answers`
7. `reviews`
8. `practice_records`

`prompt_templates` 可放到第二阶段。

## 五、落库建议

- 表引擎统一使用 InnoDB
- 统一字符集使用 `utf8mb4`
- 核心字段加唯一约束和外键约束
- 业务查询字段尽量配合索引优化
