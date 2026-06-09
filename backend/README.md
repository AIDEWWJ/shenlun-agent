# 后端说明

## 目录边界

后端当前采用以下边界：

- `app/core/`：配置、安全、异常、统一响应
- `app/infra/`：数据库、LLM、缓存等基础设施适配
- `app/shared/`：跨模块共享的枚举、常量、类型、工具
- `app/modules/`：业务域入口，例如 auth、question、practice、review、ai_config、email、admin
- `app/workflows/`：批改链、提纲链、问答链等多步骤流程
- `app/ai/capabilities/`：题目分析、要点抽取、比对、结构分析、语言分析、规则校验、提纲生成等能力
- `app/db/`：Base、session、init_db 等数据库基础代码
- `scripts/`：初始化与运维脚本
- `sql/`：建表与升级脚本
- `tests/`：自动化测试

## 运行约定

- API 路由通过 `backend/main.py` 挂载。
- 模块内部优先自洽，不从顶层共享 `models / repositories / schemas` 取代码。
- 新增 AI 推理能力优先进入 `app/ai/capabilities/`，流程串联优先进入 `app/workflows/`。
