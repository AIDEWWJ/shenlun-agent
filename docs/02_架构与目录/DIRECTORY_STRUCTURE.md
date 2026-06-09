# 申论 Agent 仓库目录结构

## 目标

这个仓库的目录设计原则是：

- 业务按模块内聚，不再保留顶层 `models / repositories / schemas`。
- AI 能力与业务工作流分层，避免把推理逻辑散落在接口层。
- 目录职责清晰，任何新增文件都能快速判断“应该放哪里”。

## 当前实际目录结构

```text
20260416_shenlun-agent/
├── README.md
├── CLAUDE.md
├── docs/
│   ├── 文档索引.md
│   ├── 01_项目总览/
│   ├── 02_架构与目录/
│   ├── 03_功能规划与进度/
│   ├── 04_接口与数据/
│   ├── 05_AI与批改流程/
│   ├── 06_前端设计/
│   ├── 07_角色权限/
│   ├── 08_练习系统设计/
│   ├── 09_研发协作/
│   └── 99_本地备忘/
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.ts
│       ├── app/
│       │   ├── App.vue
│       │   ├── main.ts
│       │   └── router/
│       ├── features/
│       ├── layouts/
│       ├── modules/
│       ├── shared/
│       └── styles/
├── backend/
│   ├── main.py
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── app/
│   │   ├── ai/
│   │   ├── core/
│   │   ├── db/
│   │   ├── infra/
│   │   ├── modules/
│   │   ├── shared/
│   │   └── workflows/
│   ├── scripts/
│   ├── sql/
│   ├── materials/
│   └── tests/
└── scripts/
```

## 目录边界说明

### 仓库根目录

根目录只保留仓库入口文档、工具配置和少量仓库级脚本，不放业务实现代码。详细文档统一进入 `docs/` 下的中文分类目录。

### frontend/

前端只负责页面展示、状态管理、接口调用与交互体验。

#### frontend/src/app/

应用级入口层，放路由初始化、全局配置、应用装配逻辑。

#### frontend/src/features/

跨模块但有明确业务组合含义的功能片段，例如多个模块共同使用的筛选器、表单流程、联动逻辑。

#### frontend/src/layouts/

页面壳和布局容器，例如顶部导航布局、专注模式布局、双栏布局。

#### frontend/src/modules/

按业务域组织前端页面、组件、服务和类型，例如 auth、question、practice、review、admin、ai-config。

#### frontend/src/shared/

真正通用、与业务域无关的基础能力，例如通用组件、通用工具、公共样式、基础类型。

### backend/

后端负责 API、业务编排、AI 工作流、数据访问、权限控制与基础设施接入。

#### backend/main.py 与 backend/app/modules/*/api.py

当前后端没有独立的 `backend/app/api/` 聚合目录。`backend/main.py` 负责创建 FastAPI 应用、注册中间件和挂载各业务模块路由；每个业务模块自己的 HTTP 入口放在 `backend/app/modules/<domain>/api.py`。

#### backend/app/core/

全局基础能力层，只放配置、安全、异常、统一响应、鉴权辅助等基础组件。

#### backend/app/infra/

基础设施适配层，只放数据库连接、LLM 客户端、缓存、第三方服务封装等外部能力接入。

#### backend/app/shared/

跨模块共享层，只放枚举、常量、通用类型、公共工具、通用模型，不放业务域专属逻辑。

#### backend/app/modules/

业务域主承载层。每个子目录对应一个业务域，例如 auth、question、practice、review、ai_config、email、admin。

模块内通常按自己的需要组织：

- `api.py`：模块接口
- `service.py`：模块业务服务
- `repository.py`：模块数据访问
- `schemas.py`：模块请求/响应 DTO
- `models.py`：模块 ORM 实体

#### backend/app/workflows/

多步骤流程编排层，适合放批改链、提纲链、问答链等跨能力的串联逻辑。

#### backend/app/ai/

AI 能力层，优先放可复用的细粒度能力单元。当前核心目录是 `capabilities/`，用于承载题目分析、要点抽取、比对、结构分析、语言分析、规则校验、提纲生成等能力。

#### backend/app/db/

数据库基础层，只放 `Base`、`session`、`init_db` 之类和 SQLAlchemy/初始化相关的基础设施代码。

#### backend/scripts/

仓库内运维脚本、初始化脚本、一次性数据处理脚本。

#### backend/sql/

数据库建表脚本、升级脚本、索引脚本。

#### backend/tests/

后端测试代码，包括 API 测试、服务测试、仓储测试。

## 当前和旧结构的关系

- 顶层 `backend/app/models`、`backend/app/repositories`、`backend/app/schemas` 已删除。
- 当前后端主链路是 `main.py / modules/*/api.py -> modules -> workflows / ai -> shared / infra -> db`。
- 练习、题库、认证、AI 配置、邮件、管理员、批改结果查询都已经归入模块边界。

## 目录使用原则

1. 先判断归属业务域，再决定是否进入 `modules/`。
2. 需要多步骤推理时，优先进入 `workflows/`。
3. 需要复用的细粒度 AI 能力，放入 `ai/capabilities/`。
4. 与业务无关的公共能力，放入 `shared/` 或 `core/`。
5. 外部依赖封装放入 `infra/`，不要散落在业务代码里。
