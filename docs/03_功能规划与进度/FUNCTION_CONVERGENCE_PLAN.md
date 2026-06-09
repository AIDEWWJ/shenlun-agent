# 前台功能收敛与页面补齐计划

> 制定日期：2026-06-09  
> 当前范围：先完善前台用户侧，不优先改后台，不优先做异步批改任务。  
> 执行原则：一个部分一个部分推进；每完成一个部分先验收，再进入下一部分。

## 一、确认原则

1. **题库统一**：试卷和单独题目放在同一个“题库 / 练习库”体系里。
2. **AI 配置归属个人资料**：AI 配置属于个人资料，不做独立主入口。
3. **先前台后后台**：本轮先整理用户侧主链路，不优先做后台 Prompt、系统配置和题库管理页。
4. **后端谨慎改动**：除非发现前台展示所需字段明显不足，否则本轮先不改后端。

## 二、前台一期目标

把用户侧主链路整理顺：

```text
首页 → 题库 → 试卷 / 单题 → 练习 → 报告 → 记录 / 复盘 → 个人资料 / AI 配置
```

本期不优先做：

- 后台 Prompt 管理页面。
- 后台系统运行配置页面。
- 后台题库管理页面。
- 异步批改任务系统。
- 数据库迁移工具。

## 三、本地验收账号

> 仅用于本地开发环境和功能验收，不用于生产环境。

| 角色 | 用户名 | 密码 | 用途 |
|---|---|---|---|
| 普通用户 | `aide` | `123456` | 验收用户侧题库、练习、报告、复盘和个人资料链路 |
| 管理员 | `admin` | `admin123456` | 验收管理员权限、后台入口和用户侧兼容表现 |

## 四、执行分期

### 第一部分：前台路由和导航收敛

**目标**

- 保留侧边栏“题库”入口，但它表达统一题库，而不是只表达试卷。
- `/papers` 保留为现有题库主入口。
- 不保留前台 `/questions` 路由，题库入口统一使用 `/papers`。
- `/ai-config` 重定向到 `/profile/ai-config`，不再跳到 `/profile/basic`。
- 个人导航增加“AI 配置”，和“个人资料 / 安全设置”并列。

**涉及文件**

- `frontend/src/app/router/routes/paper.ts`
- `frontend/src/app/router/routes/question.ts`
- `frontend/src/app/router/routes/profile.ts`
- `frontend/src/layouts/SidebarLayout.vue`

**验收点**

- 侧边栏“题库”仍能进入 `/papers`。
- 前台页面和导航不再链接 `/questions`。
- 访问 `/ai-config` 会进入 `/profile/ai-config`。
- 侧边栏个人分组出现“AI 配置”。
- 刷新页面不出现死链。

### 第二部分：统一题库页面

**目标**

- 把当前 `/papers` 页面改成统一题库页。
- 页面分两个 Tab：`套卷练习` 和 `单题练习`。
- 套卷练习展示试卷。
- 单题练习展示 `paper_id = null` 的独立题目。
- 套卷卡片可进入试卷详情或开始 / 继续练习。
- 单题卡片可进入 `/practice/:questionId`。
- 空状态区分“暂无套卷”“暂无独立题目”“当前筛选无结果”。

**涉及文件**

- `frontend/src/modules/paper/pages/PaperListPage.vue`
- `frontend/src/modules/paper/services/paper.service.ts`
- `frontend/src/modules/question/services/question.service.ts`

**验收点**

- 题库页能同时表达套卷和单题。
- `/papers` 内补齐“套卷练习 / 单题练习”两个 Tab。
- 筛选、加载、空状态不混乱。

### 第三部分：试卷详情和单题入口补齐

**目标**

- 挂载 `/papers/:paperId` 到已有 `PaperDetailPage.vue`。
- 试卷列表卡片按钮分清：`查看详情`、`开始练习`、`继续练习`。
- 试卷详情页展示材料、题目列表、题型、作答要求、建议时间。
- 单题入口直接进入 `/practice/:questionId`。

**涉及文件**

- `frontend/src/app/router/routes/paper.ts`
- `frontend/src/modules/paper/pages/PaperDetailPage.vue`
- `frontend/src/modules/practice/pages/PracticeSessionPage.vue`

**验收点**

- 套卷卡片能进入详情。
- 详情页能开始套卷练习。
- 单题卡片能进入单题练习。

### 第四部分：练习记录按设计文档重排

**目标**

- 按 `docs/08_练习系统设计/practice-system-design.md` 的思路展示练习记录。
- 记录分两块：`试卷练习` 和 `单题练习`。
- 试卷练习按 `paper_id` 分组，再按练习批次 / 时间聚合。
- 单题练习展示 `paper_id = null` 的记录。
- 试卷记录显示试卷标题、总题数、平均分 / 总分、每题报告入口。

**涉及文件**

- `frontend/src/modules/practice/pages/HistoryPage.vue`
- `frontend/src/modules/practice/services/records.service.ts`

**验收点**

- 练习记录能区分试卷练习和单题练习。
- 试卷练习不再只显示 `#paperId`。
- 每道题报告入口可用。

### 第五部分：个人资料内的 AI 配置

**目标**

- `/profile/basic` 保持个人资料。
- `/profile/security` 保持安全设置。
- `/profile/ai-config` 挂载个人 AI 配置页。
- `/ai-config` 只做兼容重定向到 `/profile/ai-config`。

**涉及文件**

- `frontend/src/app/router/routes/profile.ts`
- `frontend/src/modules/profile/pages/ProfileAiConfigPage.vue`
- `frontend/src/features/ai-config/components/AiConfigEditor.vue`

**验收点**

- 侧边栏能进入 AI 配置。
- 个人 AI 配置页能正常加载、创建、更新、设默认。
- 旧地址 `/ai-config` 不死链。

### 第六部分：前台联调验收

**验收清单**

1. 登录后侧边栏能进入首页、题库、练习记录、错题本、学习计划、个人资料、AI 配置。
2. 题库页能同时展示套卷和独立题。
3. 套卷能进入详情、开始练习、继续练习。
4. 独立题能进入单题练习。
5. 练习记录能区分试卷练习和单题练习。
6. 报告页、追问、收藏、错题本、学习计划入口不受影响。
7. 刷新页面和旧路由 `/ai-config` 不出现死链；前台不再承诺 `/questions` 可访问。

## 五、执行顺序

1. 第一部分：路由和导航收敛。
2. 第二部分：统一题库页面。
3. 第三部分：试卷详情和练习入口。
4. 第四部分：练习记录重排。
5. 第五部分：个人资料 AI 配置入口。
6. 第六部分：前台联调验收。

每完成一个部分，先记录结果和问题，再决定是否进入下一部分。

## 六、当前执行状态

| 部分 | 状态 | 说明 |
|---|---|---|
| 第一部分：前台路由和导航收敛 | 已完成 | 已移除前台 `/questions` 页面路由承诺，完成 `/ai-config` 重定向和侧边栏 AI 配置入口 |
| 第二部分：统一题库页面 | 已完成 | 已按支线方案接入 `/api/library/items`，支持全部 / 套卷 / 单题混合题库 |
| 第三部分：试卷详情和单题入口补齐 | 已完成 | 已挂载 `/papers/:paperId`，套卷可查看详情，单题可进入 `/practice/:questionId` |
| 第四部分：练习记录按设计文档重排 | 待开始 | 第三部分验收后执行 |
| 第五部分：个人资料内的 AI 配置 | 待开始 | 可在第一部分完成入口，页面细节后续验收 |
| 第六部分：前台联调验收 | 待开始 | 前五部分完成后执行 |

## 七、执行记录

### 2026-06-09：第一部分完成

**已改动**

- 移除 `/questions` 前台页面路由承诺，题库入口统一使用 `/papers`。
- 调整 `/ai-config` 兼容路由，重定向到 `/profile/ai-config`。
- 挂载 `/profile/ai-config` 到个人 AI 配置页。
- 侧边栏个人分组增加“AI 配置”。

**校验结果**

- 已执行 `npm run build`。
- 构建通过，未发现前端编译错误。
- 已使用 Playwright 进行浏览器验收。
- 普通用户 `aide / 123456` 登录成功，侧边栏显示“题库、练习记录、错题本、学习计划、个人资料、安全设置、AI 配置”。
- 管理员 `admin / admin123456` 登录成功，侧边栏显示后台入口和个人分组中的“AI 配置”。
- 前台页面级题库链接已统一改为 `/papers`。
- `/ai-config` 已正确重定向到 `/profile/ai-config`。
- `/profile/ai-config` 页面可正常打开。

**本地环境修复**

- 验收时发现 AI 配置接口返回 500，原因是本地 MySQL 表 `ai_configs` 缺少代码模型已声明的 `repair_system_prompt` 字段。
- 该字段已存在于 `backend/sql/schema.sql` 和 `backend/sql/review_chain_upgrade.sql`，属于本地数据库未同步升级。
- 已仅对本地数据库补列：`ALTER TABLE ai_configs ADD COLUMN repair_system_prompt TEXT NULL`。
- 补列后 `/api/ai-configs/system-default` 和 `/api/ai-configs/me` 均返回 200，浏览器控制台不再出现接口错误。

### 2026-06-09：第二、三部分按支线方案完成

**已改动**

- 新增 `/api/library/items` 和 `/api/library/filters` 聚合接口。
- `/papers` 页面改为统一题库页，支持“全部 / 套卷练习 / 单题练习”。
- 套卷和独立题统一渲染为题库条目，但底层仍保留 `/api/papers` 与 `/api/questions` 资源接口。
- 套卷卡片支持继续练习、开始练习和查看详情；独立题卡片进入单题练习。
- 挂载 `/papers/:paperId` 到已有试卷详情页。

**校验结果**

- 已执行 `uv run python -m unittest tests.test_library_api -v`。
- 已执行 `uv run python -m compileall -q app tests`。
- 已执行 `npm run build`。
- 以上均通过。

**下一步**

- 进入第四部分前，建议先浏览器验收 `/papers` 混合题库页和 `/papers/:paperId` 详情页。
