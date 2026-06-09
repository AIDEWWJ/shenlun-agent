# 申论 Agent 功能进度盘点

> 盘点日期：2026-06-08  
> 盘点方式：基于当前代码、接口、前端路由/服务和测试文件的静态检查；未在本次盘点中启动服务或执行全量联调。  
> 进度口径：`90%+` 表示主链路基本闭合；`70%~89%` 表示可用但仍有入口、联调或质量缺口；`50%~69%` 表示后端或前端一侧明显缺失；`<50%` 表示仍偏规划或原型。

## 一、总体结论

项目已经具备一个比较完整的“申论训练闭环”：用户登录后进入试卷/题目，进行答题练习，提交 AI 审题、提纲或批改，查看批改报告，并围绕报告做历史复盘、追问、错题本和学习计划。

当前更像是“功能覆盖已经铺开、稳定性和入口一致性待收敛”的阶段。后端模块和数据模型比较完整，前端主要页面也已搭建，但仍存在部分页面未挂路由、后台链接指向失效路由、测试夹具分散、异步批改任务未落地等问题。

### 当前完成度概览

| 模块 | 完成度 | 判断 |
|---|---:|---|
| 账号、鉴权、个人资料 | 90% | 后端、前端、测试基本闭合 |
| 邮箱验证码与邮件后台 | 85% | 注册/找回密码链路完整，SMTP 真实环境需验收 |
| AI 配置、Prompt、运行规则 | 80% | 配置能力较完整，后台前端入口不完全 |
| 试卷与题库 | 75% | 后端能力完整，前端入口和题目管理页需收敛 |
| 答案草稿与练习会话 | 85% | 单题和试卷练习都已实现，前端有本地兜底 |
| 审题、提纲、批改链 | 85% | 编排和持久化完整，异步任务未实现 |
| 批改报告、追问、历史复盘 | 80% | 报告/QA/对比接口已落地，部分交互仍需优化 |
| 首页统计、推荐、错题本、学习计划 | 70% | 后端和页面均有，算法和体验仍偏轻量 |
| 管理后台 | 75% | 用户、AI、邮件完成度高，题库/Prompt/系统配置前端入口不足 |
| 测试与工程化 | 70% | 后端关键链路有测试，前端和集成验收缺失 |

## 二、功能进度明细

### 1. 账号与身份认证

**当前能力**

- 支持注册验证码发送、注册确认、登录、当前用户查询、个人资料更新、密码修改、找回密码验证码、密码重置。
- 支持 Bearer Token 鉴权、角色校验和管理员权限拦截。
- 前端有登录/注册/找回密码页面，并支持本地 token 恢复登录状态。

**代码落点**

- 后端接口：`backend/app/modules/auth/api.py`
- 后端服务：`backend/app/modules/auth/service.py`
- 用户/角色模型：`backend/app/modules/auth/models.py`
- 前端页面：`frontend/src/modules/auth/pages/AuthPage.vue`
- 前端状态：`frontend/src/modules/auth/store/index.ts`
- 前端路由守卫：`frontend/src/app/router/guards.ts`
- 测试覆盖：`backend/tests/test_auth_api.py`

**进度判断：90%**

主流程已经闭合，且有注册登录、失败登录、资料冲突、密码修改、忘记密码和管理员权限边界测试。后续主要是补充刷新 token、登出服务端失效、登录风控等产品增强。

**下一步建议**

- 增加 token 过期后的前端统一跳转和错误提示。
- 增加管理员禁用用户后 token 仍可用场景的回归测试。
- 生产环境必须替换 `JWT_SECRET_KEY`，避免沿用开发默认值。

### 2. 邮箱验证码与邮件配置

**当前能力**

- 注册和找回密码均通过邮箱验证码确认。
- 邮件验证码包含过期、用途、上下文和已使用状态。
- 管理后台支持 SMTP 配置和邮件模板的增删改查。
- 数据库初始化会写入默认邮件模板。

**代码落点**

- 邮件接口：`backend/app/modules/email/api.py`
- 邮件服务：`backend/app/modules/email/service.py`
- 邮件模型：`backend/app/modules/email/models.py`
- 后台页面：`frontend/src/modules/admin/pages/AdminEmailSettingsPage.vue`
- 前端服务：`frontend/src/modules/admin/services/admin-email.service.ts`
- 测试覆盖：`backend/tests/test_auth_api.py`

**进度判断：85%**

后台管理和注册/找回密码链路已可用，测试覆盖了发送失败回滚和重复校验。缺口在真实 SMTP 环境联调、发送日志、重试策略和验证码频控。

**下一步建议**

- 增加验证码频率限制，防止同邮箱高频请求。
- 增加邮件发送日志，便于排查 SMTP 失败。
- 补一个“测试发送邮件”后台操作，降低部署调试成本。

### 3. 个人资料与账户安全

**当前能力**

- 用户可查看当前资料、修改用户名/邮箱、修改密码。
- 前端个人中心拆成基本资料和安全页。
- 管理员可维护用户状态和角色。

**代码落点**

- 当前用户接口：`backend/app/modules/auth/api.py`
- 后台用户接口：`backend/app/modules/admin/api.py`
- 前端资料页：`frontend/src/modules/profile/pages/ProfileBasicPage.vue`
- 前端安全页：`frontend/src/modules/profile/pages/ProfileSecurityPage.vue`
- 后台用户页：`frontend/src/modules/admin/pages/AdminUsersPage.vue`

**进度判断：85%**

用户资料主链路可用，后台用户管理也有测试覆盖。当前缺少更细的安全能力，例如登录设备管理、密码强度前后端一致校验、敏感操作二次验证。

**下一步建议**

- 统一密码复杂度规则，并补充前端提示。
- 增加用户状态变更后会话处理策略。
- 如果面向真实用户，增加登录/密码修改审计记录。

### 4. AI 模型配置

**当前能力**

- 用户可维护个人模型配置。
- 管理员可维护系统模型配置，并设置系统默认模型。
- 批改链可读取“用户配置优先、系统默认兜底”的有效配置。
- 配置包含 provider、model、api key、base url、temperature、默认标记。

**代码落点**

- 接口：`backend/app/modules/ai_config/api.py`
- 服务：`backend/app/modules/ai_config/service.py`
- 模型：`backend/app/modules/ai_config/models.py`
- 用户配置服务：`frontend/src/modules/ai-config/services/ai-config.service.ts`
- 配置编辑组件：`frontend/src/features/ai-config/components/AiConfigEditor.vue`
- 后台系统配置页：`frontend/src/modules/admin/pages/AdminAiConfigsPage.vue`
- 测试覆盖：`backend/tests/test_auth_api.py`

**进度判断：85%**

后端和后台管理较完整，批改链已能读取有效模型配置。前端存在一个需要统一的入口问题：`frontend/src/modules/ai-config/pages/AiConfigPage.vue` 存在，但当前 `/ai-config` 和 `/profile/ai-config` 都重定向到 `/profile/basic`，说明独立 AI 配置页可能已经被个人中心吸收，路由和目录需要整理。

**下一步建议**

- 明确 AI 配置入口到底是个人中心内嵌，还是独立页面。
- 增加“测试模型连接”接口和按钮。
- 对 API Key 做脱敏展示和更新策略说明。

### 5. Prompt 与运行时规则配置

**当前能力**

- 后端有系统 Prompt 模板管理接口。
- 后端有系统运行配置接口，用于要点比对阈值、结构分析、语言分析、规则校验和兜底策略。
- 初始化逻辑会写入默认 Prompt 和默认系统配置。
- AI 能力单元已经读取配置进行分析或校验。

**代码落点**

- Prompt 接口：`backend/app/modules/prompt/api.py`
- Prompt 服务：`backend/app/modules/prompt/service.py`
- 运行配置接口：`backend/app/modules/system_config/api.py`
- 运行配置服务：`backend/app/modules/system_config/service.py`
- 配置说明：`AI_CONFIG_TUNING_GUIDE.md`
- 测试覆盖：`backend/tests/test_ai_prompt_templates.py`、`backend/tests/test_ai_runtime_config.py`

**进度判断：75%**

后端和测试较完整，但前端后台只挂了用户、AI、邮件三个管理页，未看到 Prompt 管理和系统运行配置的独立前端路由入口。因此这部分更像“后端可维护、前端入口不足”。

**下一步建议**

- 在后台增加 Prompt 模板管理页。
- 在后台增加系统运行配置页，支持 JSON 编辑和配置校验。
- 增加配置修改后的“试跑一次批改链”校验入口。

### 6. 试卷库

**当前能力**

- 支持试卷列表、筛选项、试卷详情、创建、导入、删除。
- 试卷包含材料和题目，适合按真实申论套卷组织练习。
- 前端有试卷列表页，支持按范围、地区、年份、难度筛选，并可进入试卷练习。

**代码落点**

- 试卷接口：`backend/app/modules/paper/api.py`
- 试卷服务：`backend/app/modules/paper/service.py`
- 试卷模型：`backend/app/modules/paper/models.py`
- 试卷列表页：`frontend/src/modules/paper/pages/PaperListPage.vue`
- 试卷详情页：`frontend/src/modules/paper/pages/PaperDetailPage.vue`
- 前端服务：`frontend/src/modules/paper/services/paper.service.ts`
- 路由：`frontend/src/app/router/routes/paper.ts`

**进度判断：75%**

后端能力完整，前端试卷列表和试卷练习入口可用。但当前路由只挂了 `/papers`，没有挂 `PaperDetailPage.vue` 的详情路由，导致“试卷详情页存在但不可直接访问”。

**下一步建议**

- 增加 `/papers/:paperId` 路由，挂载 `PaperDetailPage.vue`。
- 明确试卷详情页与试卷练习页的入口关系。
- 给试卷导入增加前端页面或后台入口。

### 7. 题库与题目管理

**当前能力**

- 后端支持题目列表、筛选、详情、工作台、创建、批量导入、更新、删除、收藏。
- 题目字段比较丰富，包含材料引用、答题要求、题型、难度、主题、标签、参考答案、优化示例等。
- 前端保留了题目相关 service 和工作台 service；不再保留前台 `/questions` 路由，独立题入口将在统一题库页 `/papers` 中补齐。

**代码落点**

- 题目接口：`backend/app/modules/question/api.py`
- 题目服务：`backend/app/modules/question/service.py`
- 题目模型：`backend/app/modules/question/models.py`
- 前端服务：`frontend/src/modules/question/services/question.service.ts`
- 题目工作台服务：`frontend/src/modules/question/services/workspace.service.ts`
- 题目路由：`frontend/src/app/router/routes/question.ts`
- 测试覆盖：`backend/tests/test_auth_api.py`

**进度判断：70%**

后端较完整，前端题库入口正在收敛到统一题库页 `/papers`。当前不再保留 `/questions` 前台路由，“独立题展示与入口”属于前台第二部分待补齐内容。

**下一步建议**

- 在 `/papers` 统一题库页中补齐“套卷练习 / 单题练习”两个 Tab。
- 让单题卡片进入 `/practice/:questionId`，让套卷卡片进入详情或练习。
- 增加题目导入预检、题库状态管理、题库统计等后台能力。

### 8. 答案草稿与单题练习会话

**当前能力**

- 支持答案创建、更新、详情、按题目查询、复制旧答案生成新版本。
- 支持当前练习会话查询、创建、更新、提交。
- 提交练习会话后可生成答案、批改结果和练习记录。
- 前端单题练习页使用题目工作台、练习会话和答案服务。

**代码落点**

- 练习接口：`backend/app/modules/practice/api.py`
- 练习服务：`backend/app/modules/practice/service.py`
- 答案/练习模型：`backend/app/modules/practice/models.py`
- 单题练习页：`frontend/src/modules/practice/pages/PracticeSessionPage.vue`
- 答案服务：`frontend/src/modules/practice/services/answer.service.ts`
- 练习会话服务：`frontend/src/modules/practice/services/practice.service.ts`
- 测试覆盖：`backend/tests/test_practice_api.py`

**进度判断：85%**

单题练习主链路完整，并覆盖了草稿版本、工作台、练习会话、已批改答案锁定和重新批改生成新版本等场景。前端仍存在若干 `any` 类型和静默 `catch {}`，体验和类型安全可继续加强。

**下一步建议**

- 补齐前端类型，减少 `any`。
- 对保存失败、提交失败增加明确 UI 提示。
- 增加自动保存状态提示和离线恢复说明。

### 9. 试卷练习会话

**当前能力**

- 支持按试卷保存多题答案、当前题索引、计时状态和草稿状态。
- 前端试卷练习页可加载试卷详情、保存本地和服务端草稿、恢复未完成会话、提交整套试卷。

**代码落点**

- 试卷练习模型：`backend/app/modules/practice/models.py`
- 试卷练习服务：`backend/app/modules/practice/service.py`
- 试卷会话接口：`backend/app/modules/practice/api.py`
- 试卷练习页：`frontend/src/modules/practice/pages/PaperPracticePage.vue`
- 前端会话服务：`frontend/src/modules/practice/services/paper-session.service.ts`

**进度判断：80%**

试卷练习已经从“单题练习”扩展到“套卷练习”。当前需要进一步确认提交后的多题批改结果展示方式，以及本地草稿与服务端草稿冲突时的合并策略。

**下一步建议**

- 设计整套试卷提交后的结果页：按题展示得分、问题、建议和总览。
- 增加草稿冲突提示，例如“本地草稿较新/服务端草稿较新”。
- 给计时器状态增加异常恢复测试。

### 10. 审题分析与提纲生成

**当前能力**

- 支持题目分析接口。
- 支持基于题目、材料和作答要求生成提纲。
- Prompt 可通过系统模板调整。
- 前端批改服务中已封装 analyze 和 outline 请求。

**代码落点**

- 接口：`backend/app/modules/practice/api.py`
- 服务：`backend/app/modules/practice/service.py`
- 审题能力：`backend/app/ai/capabilities/analyzers/question_analyzer.py`
- 提纲能力：`backend/app/ai/capabilities/generators/outline_generator.py`
- 前端服务：`frontend/src/modules/review/services/review-api.service.ts`
- 测试覆盖：`backend/tests/test_ai_prompt_templates.py`

**进度判断：80%**

后端能力已经拆成独立 AI capability，适合后续复用。当前缺口主要是前端交互：审题分析和提纲生成在页面中的可见入口、结果状态和失败重试需要继续打磨。

**下一步建议**

- 在练习页明确展示“审题分析”和“生成提纲”两个动作。
- 保存用户采纳/修改提纲的行为，作为后续复盘数据。
- 增加 LLM 不可用时的本地兜底说明。

### 11. AI 批改链

**当前能力**

- 批改链包含题目解析、参考要点抽取、用户答案要点抽取、要点比对、AI 综合批改。
- 批改结果包含总分、维度得分、优点、问题、建议、摘要、要点命中/遗漏、结构/语言/规则分析和原始报告 JSON。
- 批改步骤会持久化，便于报告解释和后续排查。
- 支持从已有答案批改，也支持从答案内容直接批改。

**代码落点**

- 批改编排：`backend/app/workflows/review/orchestrator.py`
- 批改 DTO：`backend/app/workflows/review/dto.py`
- 批改能力：`backend/app/ai/capabilities/generators/reviewer.py`
- 要点抽取：`backend/app/ai/capabilities/extractors/reference_point_extractor.py`、`backend/app/ai/capabilities/extractors/user_point_extractor.py`
- 练习批改服务：`backend/app/modules/practice/service.py`
- 测试覆盖：`backend/tests/test_review_workflow.py`、`backend/tests/test_reviewer_agent.py`

**进度判断：85%**

批改主链路已经是项目最核心、最有论文/答辩价值的部分，具备多步骤编排和可追踪结果。当前缺口是异步批改任务尚未落地，长耗时 LLM 调用仍主要依赖同步或流式接口。

**下一步建议**

- 增加异步批改任务表和任务查询接口。
- 增加每个批改步骤的耗时、模型调用 token、失败原因记录。
- 为报告 JSON 增加版本号，避免后续结构变更影响旧报告展示。

### 12. 流式批改与流式答疑

**当前能力**

- 后端提供流式批改、从内容流式批改、报告追问流式答疑接口。
- 使用 `sse-starlette` 支撑服务端事件流。

**代码落点**

- 流式接口：`backend/app/modules/practice/streaming.py`
- 依赖：`backend/pyproject.toml`

**进度判断：70%**

后端入口存在，但本次静态盘点未看到前端 service 对 `/review/stream`、`/review/from-content/stream`、`/reviews/{review_id}/qa/stream` 的稳定封装和页面使用证据，因此暂按“后端已起步，前端联调待确认”。

**下一步建议**

- 前端增加 SSE 客户端封装。
- 在批改页展示步骤级进度，而不是只等待最终报告。
- 对流式中断、重连、重复提交做保护。

### 13. 批改报告与历史复盘

**当前能力**

- 支持批改报告列表、详情、重新批改、报告对比。
- 报告详情前端展示评分摘要、维度分、建议、改写面板和追问区域。
- 练习历史支持列表、详情和收藏标记。

**代码落点**

- 报告接口：`backend/app/modules/review/api.py`
- 报告服务：`backend/app/modules/review/service.py`
- 报告模型：`backend/app/modules/review/models.py`
- 报告页面：`frontend/src/modules/review/pages/ReviewReportPage.vue`
- 报告组件：`frontend/src/features/review-report/components/ScoreSummary.vue`、`frontend/src/features/review-report/components/DimensionScoreList.vue`、`frontend/src/features/review-report/components/SuggestionPanel.vue`、`frontend/src/features/review-report/components/RewritePanel.vue`
- 历史页面：`frontend/src/modules/practice/pages/HistoryPage.vue`
- 测试覆盖：`backend/tests/test_practice_api.py`

**进度判断：80%**

报告主展示能力已经可用，报告对比和重新批改接口也已存在。当前需要加强的是报告页面的异常状态、追问消息类型、报告对比 UI、二次训练入口。

**下一步建议**

- 增加报告对比前端页面或弹窗。
- 增加“基于本报告再练一版”的二次训练入口。
- 对 `report_json`、`score_breakdown` 做更严格的前端类型定义。

### 14. 报告追问与答疑

**当前能力**

- 用户可针对某份批改报告提问。
- 后端会按问题内容做简单分类，例如分数、要点、结构、语言、规则、改写。
- 支持会话 ID、父消息 ID、轮次和证据引用字段。
- 前端报告页有 Q&A 输入和消息展示逻辑。

**代码落点**

- 追问接口：`backend/app/modules/review/api.py`
- 追问服务：`backend/app/modules/review/service.py`
- 追问模型：`backend/app/modules/review/models.py`
- 前端报告页：`frontend/src/modules/review/pages/ReviewReportPage.vue`
- 前端服务：`frontend/src/modules/review/services/review-api.service.ts`

**进度判断：75%**

基础问答链路可用，数据模型也预留了会话和证据字段。当前答疑分类仍是关键词规则，证据引用和多轮上下文体验需要继续增强。

**下一步建议**

- 增加基于报告结构化字段的证据引用展示。
- 增加追问历史分页和会话切换 UI。
- 将关键词分类升级为可配置规则或 LLM 分类。

### 15. 首页统计、推荐与学习概览

**当前能力**

- 支持个人学习概览、按题型统计、得分趋势、随机抽题、推荐题目、最近答案查询、批改对比。
- 前端首页服务已经封装 dashboard、stats、trend、random、recommendations。

**代码落点**

- 统计接口：`backend/app/modules/dashboard/api.py`
- 统计服务：`backend/app/modules/dashboard/service.py`
- 统计仓储：`backend/app/modules/dashboard/repository.py`
- 首页服务：`frontend/src/modules/home/services/dashboard.service.ts`
- 首页页面：`frontend/src/modules/home/pages/HomePage.vue`

**进度判断：70%**

统计接口组比较完整，但推荐逻辑和弱项分析大概率仍偏规则化/轻量化。前端是否完整展示所有统计能力，需要进一步做页面级联调验收。

**下一步建议**

- 明确首页核心指标：练习次数、批改次数、平均分、最高分、连续练习天数、弱项题型。
- 为推荐题目增加推荐理由和弱项关联。
- 增加无数据状态下的新手引导。

### 16. 错题本

**当前能力**

- 支持查询错题本、从低分批改结果生成错题、标记已解决。
- 错题条目包含错误类型、错误摘要、遗漏要点、薄弱维度和解决备注。
- 前端有错题本页面和 service。

**代码落点**

- 错题接口：`backend/app/modules/notebook/api.py`
- 错题服务：`backend/app/modules/notebook/service.py`
- 错题模型：`backend/app/modules/notebook/models.py`
- 前端页面：`frontend/src/modules/practice/pages/ErrorNotebookPage.vue`
- 前端服务：`frontend/src/modules/practice/services/error-notebook.service.ts`

**进度判断：70%**

错题本已经具备“从批改结果归集”的基本能力，但错误类型、生成规则、复习闭环仍可深化。

**下一步建议**

- 将错题生成规则配置化，例如分数阈值、维度阈值、题型维度。
- 增加错题复练入口，复练后自动对比前后两次报告。
- 增加错题状态流转：待复盘、已复练、已解决。

### 17. 学习计划

**当前能力**

- 支持查询个人学习计划、生成学习计划。
- 计划包含天数、题型、训练重点、关联题目、目标分和备注。
- 前端有学习计划页面和 service。

**代码落点**

- 学习计划接口：`backend/app/modules/notebook/api.py`
- 学习计划服务：`backend/app/modules/notebook/service.py`
- 学习计划模型：`backend/app/modules/notebook/models.py`
- 前端页面：`frontend/src/modules/practice/pages/StudyPlanPage.vue`
- 前端服务：`frontend/src/modules/practice/services/study-plan.service.ts`

**进度判断：65%**

学习计划有数据结构和生成入口，但仍偏“结果生成”，缺少执行、打卡、完成度、复盘反馈等完整闭环。

**下一步建议**

- 增加计划任务完成状态。
- 将学习计划与错题本、推荐题目、弱项题型联动。
- 增加计划执行后的自动总结。

### 18. 管理后台

**当前能力**

- 管理员首页、用户管理、系统 AI 配置、邮件配置页面已挂路由。
- 用户管理支持列表、详情、创建、更新、删除。
- 系统 AI 配置支持列表、创建、更新、删除、设默认。
- 邮件配置支持 SMTP 和模板管理。

**代码落点**

- 管理员路由：`frontend/src/app/router/routes/admin.ts`
- 管理员首页：`frontend/src/modules/admin/pages/AdminHomePage.vue`
- 用户管理：`frontend/src/modules/admin/pages/AdminUsersPage.vue`
- 系统 AI 配置：`frontend/src/modules/admin/pages/AdminAiConfigsPage.vue`
- 邮件设置：`frontend/src/modules/admin/pages/AdminEmailSettingsPage.vue`
- 后端用户接口：`backend/app/modules/admin/api.py`
- 后端 AI 配置接口：`backend/app/modules/ai_config/api.py`
- 后端邮件接口：`backend/app/modules/email/api.py`

**进度判断：75%**

后台基础管理能力可用，但后台首页链接和实际路由存在不一致，且 Prompt、系统运行配置、题库/试卷导入管理尚未形成完整后台页面。

**下一步建议**

- 清理前台页面级 `/questions` 链接，统一改为 `/papers`。
- 补后台 Prompt 管理页和系统运行配置页。
- 增加题库/试卷导入管理入口。

### 19. 数据库初始化与数据模型

**当前能力**

- 启动时会创建表并写入默认角色、邮件模板、Prompt 模板和系统运行配置。
- 模型覆盖用户、角色、邮件、题目、试卷、答案、练习记录、批改、批改步骤、追问、错题本、学习计划、AI 配置等核心实体。
- SQL 文件包含建表、索引优化和升级脚本。

**代码落点**

- 初始化：`backend/app/db/init_db.py`
- 数据库会话：`backend/app/db/session.py`
- SQL：`backend/sql/schema.sql`、`backend/sql/index_optimization.sql`、`backend/sql/migrate_add_scope_and_new_tables.sql`、`backend/sql/review_chain_upgrade.sql`
- 数据模型：`backend/app/modules/*/models.py`

**进度判断：80%**

模型覆盖面已经很完整，但仍以 `create_all` 和 SQL 脚本为主，没有看到 Alembic 这类迁移工具。随着功能继续增加，数据库版本管理会成为风险点。

**下一步建议**

- 引入正式迁移流程，避免生产环境依赖 `create_all`。
- 给关键 JSON 字段补结构版本和兼容策略。
- 梳理 MySQL 与 SQLite 测试环境的字段类型差异。

### 20. 测试与质量保障

**当前能力**

- 后端已有认证、练习、批改工作流、Reviewer Agent、Prompt 模板、运行时配置等测试。
- 练习测试覆盖草稿版本、工作台、会话、批改记录、已批改答案锁定和重新批改。
- AI 测试覆盖 Prompt 使用、配置阈值、批改修复和失败场景。

**代码落点**

- 测试目录：`backend/tests/`
- 代表性测试：`backend/tests/test_auth_api.py`、`backend/tests/test_practice_api.py`、`backend/tests/test_review_workflow.py`、`backend/tests/test_reviewer_agent.py`

**进度判断：70%**

后端关键链路已有测试，但测试夹具重复度较高，未看到统一 `conftest.py`。前端没有看到单元测试或 E2E 测试配置，端到端验收仍需补齐。

**下一步建议**

- 抽取统一后端测试夹具，减少多个测试文件重复搭库。
- 增加前端基础组件测试或 Playwright E2E。
- 增加一条完整 E2E：注册/登录 → 选择试卷 → 答题 → 批改 → 查看报告 → 追问。

## 三、当前最值得优先修的缺口

### P0：继续补齐统一题库页面

- `/ai-config` 已重定向到 `/profile/ai-config`，侧边栏 AI 配置入口已补齐；前台不保留 `/questions` 页面路由。
- 当前最主要缺口是 `/papers` 仍主要展示套卷，还没有实现“套卷练习 / 单题练习”统一题库 Tab。
- `PaperDetailPage.vue` 存在，但仍未挂 `/papers/:paperId` 路由。

### P1：补齐后台配置类页面

- Prompt 管理后端已实现，但缺前端后台入口。
- 系统运行配置后端已实现，但缺前端后台入口。
- 题库/试卷导入管理需要后台入口，否则后端导入能力不易使用。

### P1：把批改从同步/流式推进到异步任务

- `BACKEND_API_BACKLOG.md` 中规划过 `review-jobs`，当前代码未看到对应接口和模型。
- 对长耗时 LLM 批改，建议增加任务状态、重试、失败原因和结果查询。

### P2：强化前端类型与错误处理

- 多个页面和 service 使用 `any`，报告结构、练习记录、错题本、学习计划应补类型。
- 多处 `catch {}` 静默吞错，会影响用户感知和问题排查。

### P2：收敛测试和部署工程

- 后端测试建议抽统一夹具。
- 前端建议增加 E2E 测试。
- 数据库建议引入迁移工具，减少生产升级风险。

## 四、建议后续迭代顺序

1. **补统一题库页**：在 `/papers` 内实现套卷练习和单题练习 Tab。
2. **补详情和入口**：挂 `/papers/:paperId`，区分查看详情、开始练习、继续练习。
3. **重排练习记录**：按试卷练习和单题练习分组展示。
4. **补后台配置页**：Prompt、系统运行配置、题库/试卷导入，释放已有后端能力。
5. **强化批改体验**：流式进度、异步任务、失败重试、步骤耗时与错误记录。

## 五、可用于论文/答辩的功能亮点

- **多步骤 AI 批改链**：题目解析、参考要点抽取、用户要点抽取、要点比对、综合批改，具备清晰的流程编排和可解释性。
- **训练闭环设计**：从题库/试卷、作答、批改、报告、追问、错题本到学习计划，功能链条完整。
- **配置化 AI 能力**：模型配置、Prompt 模板、运行时阈值均可维护，适合论述系统可扩展性。
- **模块化工程结构**：后端按 `modules / workflows / ai/capabilities` 拆分，前端按 `app / modules / features / shared` 拆分，便于讲架构演进。
- **持久化批改证据**：批改步骤、结构化报告、追问消息、错题条目均可落库，支持复盘和后续数据分析。
