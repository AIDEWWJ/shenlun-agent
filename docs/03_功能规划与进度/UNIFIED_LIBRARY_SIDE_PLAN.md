# 混合题库统一支线计划

> 制定日期：2026-06-09  
> 计划性质：支线计划，不改变当前 `FUNCTION_CONVERGENCE_PLAN.md` 的主线执行顺序。  
> 当前结论：前台不保留 `/questions` 页面路由；后端 `/api/questions` 作为题目资源接口继续保留。  
> 当前执行状态：阶段 0、阶段 1、阶段 2 已落地；阶段 3 已完成套卷草稿状态收敛，单题草稿状态等待单题练习会话持久化恢复后再补。

## 一、为什么这是支线计划

当前主线已经确定先把用户侧入口收敛到 `/papers`，并暂停继续推进第二部分。这个文档只回答一个更长期的问题：如果希望“题库”真正混合展示套卷和单题，应该怎么统一。

本支线不立刻要求改动现有页面，也不要求现在删除任何接口。它提供的是后续可采纳的设计路线。

## 二、目标状态

用户只感知一个“题库”入口，但题库里可以混合出现两类训练对象：

- **套卷**：一张试卷，包含多道小题，进入整套练习。
- **单题**：不隶属于试卷的独立题目，进入单题练习。

目标页面形态：

```text
/papers 题库

类型：全部 / 套卷 / 单题
范围：系统题库 / 我的题库
筛选：地区 / 年份 / 难度 / 题型 / 关键词

[套卷] 2024 国考副省申论卷
      5 道小题 · 150 分钟 · 查看详情 · 开始整套练习

[单题] 基层治理中的“最后一公里”协同
      概括题 · 建议 45 分钟 · 开始单题练习
```

核心原则：

1. **前台入口统一**：用户侧只从 `/papers` 进入题库。
2. **展示对象统一**：前台列表只渲染统一的 `LibraryItem`。
3. **资源域不合并**：后端仍保留 `papers` 和 `questions` 两种底层资源。
4. **不展示套卷小题重复项**：套卷内的小题不在混合列表中单独出现。
5. **后端聚合优先**：长期不建议前端分别拉 `/api/papers` 和 `/api/questions` 后自行混排。

## 三、统一概念

| 概念 | 说明 |
|---|---|
| `Paper` | 试卷资源，来自 `papers` 表和 `/api/papers` 接口 |
| `Question` | 题目资源，来自 `questions` 表和 `/api/questions` 接口 |
| 独立题 | `paper_id = null` 的题目，可作为单题练习入口 |
| 套卷小题 | `paper_id != null` 的题目，只通过所属试卷进入 |
| `LibraryItem` | 面向前台题库列表的统一展示条目 |
| `item_type` | `paper` 或 `question`，决定卡片样式和跳转行为 |

## 四、推荐接口设计

新增一个聚合模块，不替代原资源接口：

```text
GET /api/library/items
GET /api/library/filters
```

保留底层资源接口：

```text
GET /api/papers
GET /api/papers/{paper_id}
GET /api/questions
GET /api/questions/{question_id}
GET /api/questions/{question_id}/workspace
```

### 4.1 `GET /api/library/items`

用途：返回可在题库页混合展示的统一条目列表。

建议查询参数：

| 参数 | 说明 |
|---|---|
| `item_type` | `all` / `paper` / `question`，默认 `all` |
| `scope` | `system` / `user`，沿用当前题库范围口径 |
| `keyword` | 标题、来源、标签关键词 |
| `region` | 地区筛选 |
| `year` | 年份筛选 |
| `difficulty` | 难度筛选 |
| `question_type` | 题型筛选，只对单题必然有值 |
| `page` | 页码 |
| `page_size` | 每页条数 |
| `sort_by` | `created_at` / `updated_at` / `year` / `title` |
| `sort_order` | `desc` / `asc` |

建议响应结构：

```json
{
  "items": [
    {
      "item_key": "paper:12",
      "item_type": "paper",
      "resource_id": 12,
      "title": "2024 国考副省申论卷",
      "source": "国考",
      "year": 2024,
      "region": "全国",
      "difficulty": "中等",
      "question_type": null,
      "question_count": 5,
      "suggested_minutes": 150,
      "scope": "system",
      "tags": ["真题", "综合训练"],
      "has_draft": true,
      "primary_action": {
        "label": "继续练习",
        "path": "/practice/paper/12?resume=1"
      },
      "secondary_action": {
        "label": "查看详情",
        "path": "/papers/12"
      }
    },
    {
      "item_key": "question:101",
      "item_type": "question",
      "resource_id": 101,
      "title": "基层治理中的“最后一公里”协同",
      "source": "专项训练",
      "year": 2025,
      "region": "全国",
      "difficulty": "进阶",
      "question_type": "概括题",
      "question_count": null,
      "suggested_minutes": 45,
      "scope": "system",
      "tags": ["基层治理", "概括归纳"],
      "has_draft": false,
      "primary_action": {
        "label": "开始练习",
        "path": "/practice/101"
      },
      "secondary_action": null
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20
}
```

字段说明：

- `item_key` 用于前端列表 key，避免 `paper.id` 和 `question.id` 冲突。
- `resource_id` 是真实资源 ID，跳转和详情接口仍使用它。
- `primary_action` 和 `secondary_action` 让前端不必到处判断跳转路径。
- `has_draft` 用于替代当前题库页逐个请求 `/api/paper-sessions/{paper_id}` 的方式。

### 4.2 `GET /api/library/filters`

用途：返回混合题库页可用筛选项。

建议响应结构：

```json
{
  "item_types": ["paper", "question"],
  "scopes": ["system", "user"],
  "regions": ["全国", "华东"],
  "years": [2026, 2025, 2024],
  "difficulties": ["简单", "中等", "困难", "进阶", "冲刺"],
  "question_types": ["概括题", "对策题", "大作文"]
}
```

筛选项应同时从 `papers` 和独立题 `questions.paper_id is null` 中聚合。

## 五、后端落地方案

建议新增模块：

```text
backend/app/modules/library/
├── __init__.py
├── api.py
├── schemas.py
└── service.py
```

职责划分：

| 文件 | 职责 |
|---|---|
| `api.py` | 定义 `/library/items` 和 `/library/filters` 路由 |
| `schemas.py` | 定义 `LibraryItemRead`、`LibraryItemListResponse`、筛选响应结构 |
| `service.py` | 查询 `papers` 和独立 `questions`，归一化为 `LibraryItem` |

### 5.1 查询规则

`paper` 条目来源：

- 查询 `papers`。
- 按当前用户、角色和 `scope` 过滤可见范围。
- 统计或读取 `question_count`。
- 合并当前用户的试卷草稿状态。

`question` 条目来源：

- 查询 `questions`。
- 只取 `paper_id is null` 的独立题。
- 按当前用户、角色和 `scope` 过滤可见范围。
- 合并当前用户的单题练习会话状态。

### 5.2 混排与分页策略

第一版可以采用服务层归一化后混排：

1. 分别查询符合条件的 `papers` 和独立 `questions`。
2. 统一转换为 `LibraryItem`。
3. 按 `sort_by` / `sort_order` 排序。
4. 再做分页切片。

数据量变大后再升级为 SQL `UNION ALL` 或单独的题库索引视图，避免内存分页。

### 5.3 建议索引

如果当前表里还没有类似索引，后续可以补：

```sql
CREATE INDEX idx_questions_paper_scope_year ON questions(paper_id, scope, year);
CREATE INDEX idx_questions_scope_difficulty ON questions(scope, difficulty);
CREATE INDEX idx_papers_scope_year ON papers(scope, year);
CREATE INDEX idx_papers_scope_difficulty ON papers(scope, difficulty);
```

具体字段名以当前 ORM 和 SQL 脚本为准，不能为了支线计划直接假设生产库已存在。

## 六、前端落地方案

页面路由继续使用当前入口：

```text
/papers
```

建议新增或调整：

```text
frontend/src/modules/library/
├── services/library.service.ts
├── types/library.ts
└── components/LibraryItemCard.vue
```

也可以先放在 `frontend/src/modules/paper/` 内，等稳定后再拆 `library` 模块。

### 6.1 页面状态

`PaperListPage.vue` 从“试卷列表页”演进为“统一题库页”：

- `itemType`: `all` / `paper` / `question`
- `scope`: `system` / `user`
- `keyword`
- `region`
- `year`
- `difficulty`
- `questionType`
- `items`
- `total`
- `loading`

### 6.2 卡片行为

前端不直接写死所有跳转规则，优先使用后端返回的 action：

| `item_type` | 主按钮 | 次按钮 |
|---|---|---|
| `paper` | 继续练习 / 开始整套练习 | 查看详情 |
| `question` | 继续练习 / 开始单题练习 | 可为空，或后续进入题目详情 |

如果后端暂不返回 action，前端兜底规则为：

- `paper`：`/practice/paper/{resource_id}` 或 `/papers/{resource_id}`。
- `question`：`/practice/{resource_id}`。

## 七、与当前主线的关系

当前主线第二部分写的是“套卷练习 / 单题练习两个 Tab”。本支线更进一步，建议最终默认支持“全部混排”。两者不是冲突关系：

- 主线短期可以用两个 Tab 快速补齐单题入口。
- 支线长期用 `/api/library/items` 把“全部 / 套卷 / 单题”做成统一数据源。
- 如果决定直接采用支线方案，可以把主线第二部分的接口来源改为 `/api/library/items`。

建议决策点：在继续主线第二部分前确认是否要直接做聚合层。如果暂时不想改后端，就先按主线双 Tab；如果希望一次到位，就走本支线。

## 八、执行分期

### 阶段 0：口径确认

状态：已完成。

目标：不动代码，只确认统一边界。

验收点：

- 确认前台 `/questions` 页面路由不恢复。
- 确认后端 `/api/questions` 继续作为题目资源接口。
- 确认 `/papers` 是用户侧题库入口。
- 确认混排列表只展示独立题，不展示套卷内小题。

### 阶段 1：后端聚合接口

状态：已完成。

目标：新增 `/api/library/items` 和 `/api/library/filters`。

涉及文件：

- `backend/main.py`
- `backend/app/modules/library/api.py`
- `backend/app/modules/library/service.py`
- `backend/app/modules/library/schemas.py`
- `backend/tests/test_library_api.py`

验收点：

- [x] `item_type=all` 能同时返回套卷和独立题。
- [x] `item_type=paper` 只返回套卷。
- [x] `item_type=question` 只返回 `paper_id = null` 的独立题。
- [x] 筛选项同时覆盖套卷和独立题。
- [x] 返回 `item_key`，避免前端 key 冲突。

### 阶段 2：前端题库页切换数据源

状态：已完成。

目标：`/papers` 页面从 `/api/papers` 切到 `/api/library/items`。

涉及文件：

- `frontend/src/modules/paper/pages/PaperListPage.vue`
- `frontend/src/modules/library/services/library.service.ts`
- `frontend/src/modules/library/types/library.ts`

验收点：

- [x] 默认“全部”能混排套卷和单题。
- [x] 类型筛选能切换“全部 / 套卷 / 单题”。
- [x] 套卷卡片进入整套练习或详情。
- [x] 单题卡片进入单题练习。
- [x] 页面不调用前台 `/questions` 路由。

### 阶段 3：继续练习状态收敛

状态：部分完成。

目标：减少当前题库页逐个查试卷草稿的 N+1 请求。

验收点：

- [x] `LibraryItem.has_draft` 能正确展示套卷“继续练习”。
- [ ] 单题草稿状态等待单题练习会话持久化恢复后补齐。
- [x] 题库列表首屏不再为每个套卷额外请求 session。

已落地说明：当前 `practice_sessions` 单题会话表在代码中为兼容 stub，无法可靠识别单题草稿；因此第一版只在聚合层合并 `paper_practice_sessions` 的套卷草稿状态。

### 2026-06-09：支线落地记录

**已改动**

- 新增后端 `backend/app/modules/library/` 聚合模块。
- 在 `backend/main.py` 挂载 `/api/library/items` 和 `/api/library/filters`。
- 新增 `backend/tests/test_library_api.py`，覆盖混排、类型筛选、范围筛选、套卷小题不重复展示、筛选项聚合和管理员个人范围边界。
- 新增前端 `frontend/src/modules/library/services/library.service.ts` 与 `frontend/src/modules/library/types/library.ts`。
- 将 `frontend/src/modules/paper/pages/PaperListPage.vue` 从试卷列表切换为混合题库页。
- 挂载 `/papers/:paperId` 到已有 `PaperDetailPage.vue`，供套卷“查看详情”使用。

**校验结果**

- 已执行 `uv run python -m unittest tests.test_library_api -v`，通过。
- 已执行 `uv run python -m compileall -q app tests`，通过。
- 已执行 `npm run build`，通过。

### 阶段 4：文档与主线合并决策

目标：决定是否把本支线并入主线第二部分。

验收点：

- 更新 `FUNCTION_CONVERGENCE_PLAN.md` 的第二部分接口口径。
- 更新 `API_DESIGN.md` 的 `library` 聚合接口说明。
- 更新 `LAYOUT_DESIGN.md` 的题库页面数据来源。
- 如果不合并，保留本文件为后续升级参考。

## 九、风险与待决策点

| 问题 | 风险 | 建议 |
|---|---|---|
| 是否新增 `library` 模块 | 会增加一个聚合层 | 值得做，能避免前端混排和分页复杂化 |
| 是否默认混排 | 用户可能分不清套卷和单题 | 卡片增加明显类型标识，提供类型筛选 |
| 是否保留 `/api/papers` 与 `/api/questions` | 如果误删会影响详情、练习、后台 | 必须保留底层资源接口 |
| 是否前端临时双接口合并 | 短期快，长期分页/排序麻烦 | 仅可作为临时方案，不作为长期目标 |
| 是否创建 `/library` 前台路由 | 会改变既有入口 | 暂不需要，继续使用 `/papers` |

## 十、非目标

本支线不做以下事情：

- 不恢复前台 `/questions` 页面路由。
- 不删除后端 `/api/questions`。
- 不把 `papers` 和 `questions` 强行合成一张表。
- 不重做练习系统状态机。
- 不优先做后台题库管理页。
- 不优先做异步批改任务。

## 十一、最终判断

如果目标是“题库混合展示试卷和单题”，最稳的统一方式是新增 `library` 聚合层：

```text
前台入口：/papers
前台列表对象：LibraryItem
聚合接口：/api/library/items
底层资源：/api/papers + /api/questions
```

这样既能统一用户体验，又不会破坏后端清晰的资源边界。
