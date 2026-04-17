# 申论 Agent 仓库目录结构

## 目标

让项目目录和当前开发阶段保持一致，先支撑 MVP 落地，再为后续扩展页面模块、业务服务、Agent 流程和测试体系预留位置。

## 当前实际目录结构

```text
20260416_shenlun-agent/
├── frontend/                         # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── assets/                   # 静态资源
│   │   ├── components/               # 通用组件
│   │   ├── pages/                    # 页面级组件
│   │   ├── router/                   # 路由配置
│   │   ├── services/                 # 前端接口请求封装
│   │   ├── stores/                   # 状态管理
│   │   ├── utils/                    # 前端工具函数
│   │   ├── App.vue                   # 根组件
│   │   ├── main.ts                   # 前端入口
│   │   └── styles.css                # 全局样式
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── backend/                          # FastAPI 后端
│   ├── .env                          # 本地环境变量
│   ├── app/
│   │   ├── api/                      # 路由聚合、依赖注入与接口模块
│   │   │   ├── endpoints/
│   │   │   │   ├── ai_configs.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── health.py
│   │   │   │   ├── practice.py
│   │   │   │   └── __init__.py
│   │   │   ├── deps.py
│   │   │   ├── router.py
│   │   │   └── __init__.py
│   │   ├── agents/                   # Agent 编排预留目录
│   │   │   └── __init__.py
│   │   ├── core/                     # 配置与安全相关逻辑
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── db/                       # 数据库连接、Base、会话与初始化
│   │   │   ├── base.py
│   │   │   ├── init_db.py
│   │   │   ├── session.py
│   │   │   ├── __init__.py
│   │   ├── models/                   # ORM 实体模型
│   │   │   ├── ai_config.py
│   │   │   ├── answer.py
│   │   │   ├── practice_record.py
│   │   │   ├── prompt_template.py
│   │   │   ├── question.py
│   │   │   ├── review.py
│   │   │   ├── role.py
│   │   │   ├── user.py
│   │   │   ├── user_role.py
│   │   │   └── __init__.py
│   │   ├── schemas/                  # 请求与响应数据结构
│   │   │   ├── ai_config.py
│   │   │   ├── auth.py
│   │   │   └── __init__.py
│   │   └── services/                 # 业务服务预留目录
│   │       └── __init__.py
│   ├── scripts/
│   │   └── init_db.py
│   ├── sql/
│   │   └── schema.sql
│   ├── tests/                        # 后端测试预留目录
│   ├── main.py
│   └── requirements.txt
├── docs/                             # 补充设计文档与后续沉淀
├── scripts/                          # 根级辅助脚本预留目录
├── .env.example
├── API_DESIGN.md
├── ARCHITECTURE.md
├── DATA_MODEL.md
├── DB_INDEX_OPTIMIZATION.md
├── DB_SCHEMA.md
├── DB_SCHEMA_DOC.md
├── DIRECTORY_STRUCTURE.md
├── MVP_PLAN.md
├── PROGRESS.md
├── PROJECT.md
├── README.md
├── ROLE_DESIGN.md
└── ROLE_MATRIX.md
```

## 目录说明

- `frontend/src/components/`：放可复用组件，例如题目卡片、批改结果面板、模型选择器。
- `frontend/src/pages/`：放页面级视图，例如登录页、练习页、复盘页。
- `frontend/src/services/`：放前端请求封装，避免页面里直接写接口调用。
- `frontend/src/stores/`：放用户状态、练习状态、模型配置等全局状态。
- `backend/app/api/router.py`：统一注册所有接口路由。
- `backend/app/api/endpoints/`：按业务域拆分接口文件，避免所有路由堆在一个文件。
- `backend/app/api/deps.py`：放鉴权、数据库会话等通用依赖。
- `backend/app/core/`：放配置、安全、鉴权等基础能力。
- `backend/app/db/`：放数据库连接、Base、会话和初始化逻辑。
- `backend/app/models/`：放按实体拆分的 ORM 模型。
- `backend/app/services/`：建议集中放题目分析、提纲生成、批改等业务逻辑。
- `backend/app/agents/`：建议集中放多步骤 Agent 流程编排。
- `backend/tests/`：建议后续补 API、权限、数据库初始化等测试。

## 当前建议

- 后端 ORM 模型已统一收敛到 `backend/app/models/`，`backend/app/db/` 只保留数据库基础设施代码。
- 前端目录已经补齐，但目前仍只有基础入口文件，后续可以按页面和功能模块逐步落代码。
- 根目录 `docs/` 与 `scripts/` 已创建，后续新增补充资料或自动化脚本时建议优先放入对应目录。
