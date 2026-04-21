# 申论 Agent

一个面向申论刷题者的开源 AI Agent 平台。

## 当前状态

项目已完成基础骨架和第一批可验证功能：

- FastAPI 后端已启动并接入统一路由
- 用户注册、登录、当前用户查询已可用
- 用户个人信息更新、修改密码已可用
- JWT Bearer 鉴权已接入前端
- 用户 AI 配置与管理员系统默认配置接口已落地
- 题目分析、提纲生成、答案批改接口已提供占位实现
- 已接入统一返回格式与全局异常处理
- 后端已补齐 repositories、services、agents 分层目录
- 前端已补充个人信息、密码与 AI 配置接口封装
- 前端已补充个人中心、管理员用户管理、系统配置和接口联调页面
- 前端已拆分为标准路由页、布局页和复用组件
- 前端已继续拆分为标题、提示、列表等通用组件
- 前端已继续拆分为表单编辑组件，页面更清晰
- 登录、注册、当前用户接口已完成并通过测试
- 后端已补充更完整的权限与冲突边界测试
- 前端已完成登录/注册界面与受保护接口联调页
- 数据库初始化时会自动建表并写入默认角色

## 项目目标

把申论练习从“单次问答”升级为“可持续训练的 Agent 流程”，帮助用户完成：

- 题目分析
- 作答思路拆解
- 参考提纲生成
- 答案批改与点评
- 改写优化与提升建议
- 错题复盘与长期训练

## 核心特性

- **Agent 化流程**：不是简单聊天，而是围绕申论训练任务组织步骤
- **模型自由选择**：支持接入不同 AI 模型，避免单一厂商绑定
- **自定义 AI 配置**：用户在界面中配置自己的 API Key、模型、温度、系统提示词等
- **开源可扩展**：便于二次开发、部署到本地或私有环境
- **训练闭环**：支持记录练习、复盘、错题本和持续优化

## 已实现能力

### 后端

- `GET /api/health`
- `POST /api/auth/register/send-code`
- `POST /api/auth/register`
- `POST /api/auth/forgot-password/send-code`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `PUT /api/auth/me`
- `POST /api/auth/me/password`
- `POST /api/auth/forgot-password`
- `GET /api/ai-configs/me`
- `POST /api/ai-configs/me`
- `PUT /api/ai-configs/me/{config_id}`
- `DELETE /api/ai-configs/me/{config_id}`
- `POST /api/ai-configs/me/{config_id}/default`
- `GET /api/ai-configs/system-default`
- `GET /api/admin/ai-configs/system`
- `POST /api/admin/ai-configs/system`
- `PUT /api/admin/ai-configs/system/{config_id}`
- `DELETE /api/admin/ai-configs/system/{config_id}`
- `POST /api/admin/ai-configs/system/{config_id}/default`
- `GET /api/admin/email/configs`
- `POST /api/admin/email/configs`
- `PUT /api/admin/email/configs/{config_id}`
- `DELETE /api/admin/email/configs/{config_id}`
- `GET /api/admin/email/templates`
- `POST /api/admin/email/templates`
- `PUT /api/admin/email/templates/{template_key}`
- `DELETE /api/admin/email/templates/{template_key}`
- `GET /api/admin/users`
- `GET /api/admin/users/{user_id}`
- `POST /api/admin/users`
- `PUT /api/admin/users/{user_id}`
- `DELETE /api/admin/users/{user_id}`
- `POST /api/analyze`
- `POST /api/outline`
- `POST /api/review`

### 前端

- 登录 / 注册切换
- 邮箱验证码注册 / 找回密码
- 自动恢复本地登录态
- Bearer Token 注入请求
- 受保护接口联调页
- 管理员邮件配置与模板管理页

### 通用能力

- 统一返回结构：`success`、`message`、`data`、`error`
- 统一异常处理：参数校验、业务错误、系统异常会返回标准 JSON
- 后端分层：`repositories`、`services`、`agents` 已准备好

## 适用人群

- 申论刷题者
- 公考备考者
- 想要系统提升申论表达与结构化作答能力的用户
- 希望私有化部署 AI 学习工具的开发者

## 建议的 MVP 功能

1. 题目输入与解析
2. 自动识别题型与作答要求
3. 输出作答框架/提纲
4. 支持答案批改与评分建议
5. 支持用户在界面中切换模型
6. 支持管理员在后台设置系统默认模型
7. 支持用户自定义 AI 参数
8. 支持练习记录与复盘

## 未来可扩展方向

- 申论题库管理
- 历年真题整理
- 自动生成训练计划
- 多轮追问式答题教练
- 本地模型与云模型统一适配层
- 多端同步与导出

## 推荐技术方向

- 前端：Vue 3 + Vite
- 后端：Python + FastAPI
- ORM：SQLAlchemy
- 配置管理：Pydantic Settings
- AI 编排：LangChain
- 数据存储：MySQL
- 部署方式：本地优先，支持私有部署
- 可选增强：LangGraph（复杂流程编排时再引入）

## 快速启动

### 后端

1. 进入 backend 目录并安装依赖
2. 配置 .env
3. 启动 FastAPI 服务

### 前端

1. 进入 frontend 目录
2. 安装依赖
3. 启动 Vite 开发服务

前端默认请求地址为 http://127.0.0.1:8000/api，可通过环境变量覆盖。

## 文档导航

- [项目文档](PROJECT.md)
- [技术架构](ARCHITECTURE.md)
- [前端视觉风格规范](docs/FRONTEND_VISUAL_STYLE_GUIDE.md)
- [目录结构](DIRECTORY_STRUCTURE.md)
- [MVP 开发计划](MVP_PLAN.md)
- [接口设计](API_DESIGN.md)
- [数据模型](DATA_MODEL.md)
- [数据库表设计](DB_SCHEMA.md)
- [建表说明文档](DB_SCHEMA_DOC.md)
- [索引优化版](DB_INDEX_OPTIMIZATION.md)
- [角色设计](ROLE_DESIGN.md)
- [权限矩阵](ROLE_MATRIX.md)
- [数据库初始化说明](DB_SCHEMA.md#部署初始化方式)
- [进度追踪](PROGRESS.md)

