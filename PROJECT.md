# 申论 Agent — PROJECT.md

## 项目概述

一个面向申论刷题者的开源 AI Agent 平台。项目目标是把申论训练从单次问答扩展为可持续的 Agent 流程，支持题目分析、提纲生成、答案批改、复盘记录，以及通过界面自由切换模型、由管理员统一维护系统默认 AI 配置、用户自定义个人 AI 配置。

**创建日期**：2026-04-16
**状态**：进行中

---

## 文件结构

```
20260416_shenlun-agent/
├── .env.example        # 环境变量示例（仅系统运行参数）
├── .gitignore          # 忽略文件
├── README.md          # 项目介绍
├── ARCHITECTURE.md    # 技术架构说明
├── DIRECTORY_STRUCTURE.md # 仓库目录结构
├── API_DESIGN.md      # 接口设计说明
├── DATA_MODEL.md      # 数据模型说明
├── MVP_PLAN.md        # MVP 开发计划
├── DB_SCHEMA.md       # 数据库表设计
├── DB_SCHEMA_DOC.md   # 建表说明文档
├── DB_INDEX_OPTIMIZATION.md # 索引优化说明
├── ROLE_DESIGN.md     # 角色设计
├── ROLE_MATRIX.md     # 权限矩阵表
├── frontend/           # Vue 3 前端骨架
├── backend/            # Python + FastAPI 后端骨架
│   ├── app/db/init_db.py    # 数据库初始化逻辑
│   ├── app/models/          # ORM model 层（按实体拆分）
│   ├── app/api/router.py    # API 总路由入口
│   ├── app/api/endpoints/   # 按业务域拆分的接口模块
│   ├── app/api/deps.py      # 登录鉴权依赖
│   ├── app/core/security.py # 密码与 JWT 工具
│   └── sql/schema.sql       # MySQL 初始化脚本（索引优化版）
├── PROJECT.md         # 项目文档（本文件）
└── PROGRESS.md        # 进度追踪
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
- 支持界面化模型切换
- 支持管理员配置系统默认 AI
- 支持用户自定义个人 AI 配置

---

## 备注

- 当前为项目初始化阶段，重点是先明确产品边界与最小可用版本。
- 后续如需进入实现阶段，应优先补充：功能拆分、页面结构、模型适配方案与数据结构设计。
- 技术架构说明已单独整理到 [ARCHITECTURE.md](ARCHITECTURE.md)。
- 目录结构已单独整理到 [DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md)。
- MVP 开发计划已单独整理到 [MVP_PLAN.md](MVP_PLAN.md)。
- 接口设计已单独整理到 [API_DESIGN.md](API_DESIGN.md)。
- 数据模型已单独整理到 [DATA_MODEL.md](DATA_MODEL.md)。
- 数据库表设计已单独整理到 [DB_SCHEMA.md](DB_SCHEMA.md)。
- 建表说明文档已单独整理到 [DB_SCHEMA_DOC.md](DB_SCHEMA_DOC.md)。
- 索引优化版说明已单独整理到 [DB_INDEX_OPTIMIZATION.md](DB_INDEX_OPTIMIZATION.md)。
- 角色设计已单独整理到 [ROLE_DESIGN.md](ROLE_DESIGN.md)。
- 权限矩阵已单独整理到 [ROLE_MATRIX.md](ROLE_MATRIX.md)。
- 数据库初始化脚本与自动初始化逻辑已补充。
- 登录、注册、当前用户查询与基础鉴权接口已实现。
- 已从数据模型开始落地 AI 配置的 schema 与接口，支持用户个人配置和管理员系统默认配置。
- ORM model 层已按目录拆分，避免单文件堆叠。
- 当前已初始化前后端基础骨架，后续可直接进入功能实现。

---

## 进度记录

| 日期 | 说明 |
|------|------|
| 2026-04-16 | 项目创建，完成项目文档初始化 |
