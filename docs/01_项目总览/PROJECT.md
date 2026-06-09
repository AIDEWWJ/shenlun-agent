# 申论 Agent — PROJECT.md

## 项目概述

一个面向申论刷题者的开源 AI Agent 平台。项目目标是把申论训练从单次问答扩展为可持续的 Agent 流程，支持题目分析、提纲生成、答案批改、复盘记录，以及通过界面自由切换模型、由管理员统一维护系统默认 AI 配置、用户自定义个人 AI 配置。

**创建日期**：2026-04-16
**当前状态**：基础骨架已完成，核心鉴权与 AI 配置能力已落地

---

## 文件结构

```
20260416_shenlun-agent/
├── .env.example
├── README.md
├── ARCHITECTURE.md
├── DIRECTORY_STRUCTURE.md
├── API_DESIGN.md
├── DATA_MODEL.md
├── MVP_PLAN.md
├── DB_SCHEMA.md
├── DB_SCHEMA_DOC.md
├── DB_INDEX_OPTIMIZATION.md
├── ROLE_DESIGN.md
├── ROLE_MATRIX.md
├── AGENT_FLOW_DESIGN.md
├── frontend/
├── backend/
│   ├── main.py
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   ├── router.py
│   │   │   └── endpoints/
│   │   │       ├── ai_configs.py
│   │   │       ├── auth.py
│   │   │       ├── health.py
│   │   │       └── practice.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── exceptions.py
│   │   │   ├── response.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── init_db.py
│   │   │   └── session.py
│   │   ├── models/
│   │   │   ├── ai_config.py
│   │   │   ├── answer.py
│   │   │   ├── practice_record.py
│   │   │   ├── prompt_template.py
│   │   │   ├── question.py
│   │   │   ├── review.py
│   │   │   ├── role.py
│   │   │   ├── user.py
│   │   │   └── user_role.py
│   │   ├── schemas/
│   │   │   ├── ai_config.py
│   │   │   ├── auth.py
│   │   │   ├── admin_user.py
│   │   │   └── common.py
│   │   ├── repositories/
│   │   │   ├── ai_config_repo.py
│   │   │   ├── practice_repo.py
│   │   │   └── user_repo.py
│   │   └── services/
│   │       ├── ai_config_service.py
│   │       ├── auth_service.py
│   │       ├── practice_service.py
│   │       └── user_service.py
│   ├── scripts/
│   │   └── init_db.py
│   └── sql/
│       └── schema.sql
├── PROJECT.md
└── PROGRESS.md
```

---

## 关联资源

- 申论真题与练习题库：待补充
- AI 模型提供方：支持用户自定义接入
- 本地/私有部署环境：待补充

---

## 核心内容

### 1. 产品定位

- 面向申论刷题者
- 开源、可自部署、可扩展
- 支持用户自由选择 AI 模型与配置
- 以 Agent 工作流组织训练、批改和复盘

### 2. 核心能力

- 题目解析与要求拆解
- 作答思路生成
- 提纲/框架输出
- 答案批改与点评
- 改写优化建议
- 错题本与训练记录
- 界面化模型切换
- 用户自定义系统提示词与参数

### Agent 主链设计

项目当前围绕两条主链组织能力，完整设计见 [AGENT_FLOW_DESIGN.md](../05_AI与批改流程/AGENT_FLOW_DESIGN.md)：

1. **批改链**
	- 题目解析
	- 参考答案要点抽取
	- 用户答案要点抽取
	- 要点比对
	- 结构分析
	- 语言分析
	- 规则校验
	- 分数计算
	- 生成批改报告
	- 保存结果

2. **答疑链**
	- 用户追问
	- 问题分类
	- 检索对应批改证据
	- 进入对应子链
	- 生成回答
	- 保存会话

### 3. 设计原则

- **模型无绑定**：不依赖单一 AI 厂商
- **配置可迁移**：用户可以导入/导出自己的 AI 设置，系统默认配置由管理员统一维护
- **流程可扩展**：后续可加入更多训练 Agent
- **本地优先**：尽量支持本地运行与私有部署

### 4. 建议技术架构

- 前端：Vue 3 + Vite
- 后端：Python + FastAPI
- AI 编排：LangChain
- 数据层：MySQL
- 配置层：用户级 AI 设置、管理员级系统默认配置、项目级 Prompt 模板
- 后续增强：复杂流程可引入 LangGraph

### 5. MVP 范围

- 输入申论题目
- 自动分析题型与作答要求
- 输出作答框架
- 支持基础批改
- 支持批改结果追问解释
- 支持界面化模型切换
- 支持管理员配置系统默认 AI
- 支持用户自定义个人 AI 配置

---

## 备注

- 当前已经不是纯初始化阶段，核心鉴权链路与 AI 配置链路已经可以联调验证。
- 接下来应优先补充：题目分析、提纲生成、答案批改的真实业务实现，以及练习记录与复盘页面。
- 前端视觉设计统一遵循 [前端视觉风格规范](../06_前端设计/FRONTEND_VISUAL_STYLE_GUIDE.md)，每次新增或重构页面前先阅读。
- 技术架构说明已单独整理到 [ARCHITECTURE.md](../02_架构与目录/ARCHITECTURE.md)。
- 目录结构已单独整理到 [DIRECTORY_STRUCTURE.md](../02_架构与目录/DIRECTORY_STRUCTURE.md)。
- MVP 开发计划已单独整理到 [MVP_PLAN.md](../03_功能规划与进度/MVP_PLAN.md)。
- 接口设计已单独整理到 [API_DESIGN.md](../04_接口与数据/API_DESIGN.md)。
- 数据模型已单独整理到 [DATA_MODEL.md](../04_接口与数据/DATA_MODEL.md)。
- 数据库表设计已单独整理到 [DB_SCHEMA.md](../04_接口与数据/DB_SCHEMA.md)。
- 建表说明文档已单独整理到 [DB_SCHEMA_DOC.md](../04_接口与数据/DB_SCHEMA_DOC.md)。
- 索引优化版说明已单独整理到 [DB_INDEX_OPTIMIZATION.md](../04_接口与数据/DB_INDEX_OPTIMIZATION.md)。
- 角色设计已单独整理到 [ROLE_DESIGN.md](../07_角色权限/ROLE_DESIGN.md)。
- 权限矩阵已单独整理到 [ROLE_MATRIX.md](../07_角色权限/ROLE_MATRIX.md)。
- 数据库初始化脚本与自动初始化逻辑已补充。
- 登录、注册、当前用户查询与基础鉴权接口已实现。
- 已支持个人信息更新与修改密码。
- 已从数据模型开始落地 AI 配置的 schema 与接口，支持用户个人配置和管理员系统默认配置。
- ORM model 层已按目录拆分，避免单文件堆叠。
- 前端已补充个人信息、密码和 AI 配置接口封装。
- 已补充管理员用户增删改查接口与测试。
- 已完成模块化分层落地（`modules`、`workflows`、`ai/capabilities`），后续按边界继续扩展。
- 当前已初始化前后端基础骨架，后续可直接进入功能实现。

---

## 进度记录

| 日期 | 说明 |
|------|------|
| 2026-04-16 | 项目创建，完成项目文档初始化 |
| 2026-04-17 | 完成登录、鉴权、AI 配置与前端联调能力落地 |
