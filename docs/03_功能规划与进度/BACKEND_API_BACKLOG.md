# 申论练习平台后端接口 Backlog

> 文档性质：历史规划与扩展清单。  
> 当前状态：其中一部分接口已经实现，例如题目工作台、练习会话、练习记录、收藏、统计、错题本、学习计划、报告追问等；另一部分仍未实现，例如异步 `review-jobs`、报告后二次训练、导入预检、题库状态管理等。执行前应以当前代码和 `FUNCTION_PROGRESS.md` 为准。

## 1. 现状判断

当前后端已经覆盖了主链路：

- 认证与个人资料
- 题库列表、题目详情、题目录入
- 答案版本
- 审题分析、提纲生成
- AI 批改
- 批改报告详情
- 历史练习记录
- 批改答疑
- AI 配置与后台管理

真正还缺的不是零散 CRUD，而是三层能力：

1. 练习会话层：让“开始练习 -> 保存草稿 -> 继续练习 -> 提交批改”成为一个完整对象。
2. 复盘统计层：让首页、个人中心、错题本、薄弱项分析有稳定接口来源。
3. 二次训练层：让报告不止停在“看完”，而是能直接进入下一稿训练。

## 2. 第一优先级

这一组接口建议优先做，因为它们直接决定前端是否能从 mock 数据切到真实后端。

### 2.1 题目工作台接口

#### `GET /api/questions/{question_id}/workspace`

用途：
统一返回练习页需要的题目完整结构，而不是让前端自己拼多个接口。

建议响应：

```json
{
  "question": {
    "id": 101,
    "title": "基层治理中的“最后一公里”协同",
    "category": "真题",
    "source": "2024 国考副省",
    "year": 2024,
    "region": "全国",
    "question_type": "概括题",
    "difficulty": "进阶",
    "theme": "基层治理",
    "suggested_minutes": 45,
    "tags": ["治理协同", "概括归纳"],
    "cover_note": "练概括问题和提炼措施",
    "intro": "聚焦基层协同堵点",
    "overview": "适合训练问题抽象与概括作答",
    "tasks": ["概括主要堵点", "提炼优化方向"],
    "instructions": ["先分类再归纳"],
    "notices": ["建议先列提纲再作答"]
  },
  "materials": [
    {
      "id": 1,
      "title": "材料一：社区网格协同",
      "summary": "多个治理主体各自为战",
      "content": "..."
    }
  ],
  "answer_sections": [
    {
      "id": 1,
      "section_key": "a1",
      "title": "问题概括",
      "prompt": "请概括主要堵点",
      "word_limit_label": "建议 250-350 字",
      "min_words": 220,
      "placeholder": "先概括问题类型，再归纳具体表现"
    }
  ],
  "reference_answer": "...",
  "optimized_example": "...",
  "latest_draft": {
    "session_id": 12,
    "answer_id": 33,
    "status": "drafting",
    "answers": {
      "a1": "...",
      "a2": "..."
    },
    "updated_at": "2026-05-07T14:00:00"
  },
  "latest_review": {
    "review_id": 90,
    "score": 74,
    "created_at": "2026-05-06T20:15:00"
  }
}
```

补充说明：

- 这个接口会直接替换前端当前的 `questionCatalog` mock 数据源。
- 比起扩展 `GET /api/questions/{id}`，单独做 `workspace` 更清晰，因为它返回的是练习上下文，不只是题目信息。

### 2.2 练习会话接口

当前前端草稿只存在 localStorage。建议把练习过程抽象为 `practice_session`。

#### `GET /api/practice-sessions/current?question_id=101`

用途：
获取某题当前可继续的会话，没有则返回 `null`。

#### `POST /api/practice-sessions`

建议请求：

```json
{
  "question_id": 101
}
```

建议响应：

```json
{
  "id": 12,
  "question_id": 101,
  "status": "drafting",
  "answers": {
    "a1": "",
    "a2": ""
  },
  "started_at": "2026-05-07T14:00:00",
  "updated_at": "2026-05-07T14:00:00"
}
```

#### `PATCH /api/practice-sessions/{session_id}`

用途：
云端自动保存草稿。

建议请求：

```json
{
  "answers": {
    "a1": "...",
    "a2": "..."
  },
  "elapsed_seconds": 1260
}
```

#### `POST /api/practice-sessions/{session_id}/submit`

用途：
提交当前会话，自动落答案版本并发起批改任务。

建议请求：

```json
{
  "use_llm": true,
  "reference_points": []
}
```

建议响应：

```json
{
  "session_id": 12,
  "answer_id": 33,
  "review_job_id": 108,
  "status": "reviewing"
}
```

### 2.3 异步批改任务接口

现在 `POST /api/review` 是同步返回。只要模型响应慢一些，就会拖慢整体体验。

#### `POST /api/review-jobs`

建议请求：

```json
{
  "question_id": 101,
  "answer_id": 33,
  "use_llm": true,
  "reference_points": []
}
```

建议响应：

```json
{
  "job_id": 108,
  "status": "queued"
}
```

#### `GET /api/review-jobs/{job_id}`

建议响应：

```json
{
  "job_id": 108,
  "status": "running",
  "progress": {
    "current_step": "language_analysis",
    "current_step_name": "语言分析",
    "percent": 72
  }
}
```

#### `GET /api/review-jobs/{job_id}/result`

建议响应：

```json
{
  "job_id": 108,
  "status": "succeeded",
  "review_id": 90
}
```

这样前端可以做：

1. 提交答案
2. 跳到“批改中”状态页
3. 轮询任务状态
4. 完成后跳转报告页

## 3. 第二优先级

这一组接口不阻塞主链路，但能让“练完一次”变成“持续训练”。

### 3.1 报告后二次训练接口

#### `POST /api/reviews/{review_id}/rewrite-outline`

用途：
根据本次报告生成“下一稿答题提纲”。

建议请求：

```json
{
  "focus": ["内容覆盖", "结构组织"],
  "use_llm": true
}
```

#### `POST /api/reviews/{review_id}/rewrite-draft`

用途：
根据报告建议直接生成参考改写稿。

建议请求：

```json
{
  "mode": "full",
  "use_llm": true
}
```

建议响应：

```json
{
  "outline": "...",
  "rewritten_answer": "...",
  "revision_notes": [
    "补齐了对策维度",
    "重组了总分结构"
  ]
}
```

#### `POST /api/reviews/{review_id}/create-next-answer`

用途：
把改写稿直接落成下一版答案，进入下一轮练习。

建议请求：

```json
{
  "content": "...",
  "source": "rewrite_draft"
}
```

### 3.2 首页与个人中心统计接口

#### `GET /api/me/dashboard`

用途：
给首页和个人中心一次性返回高频信息。

建议响应：

```json
{
  "stats": {
    "total_practices": 18,
    "total_reviews": 16,
    "avg_score": 72.4,
    "improvement_delta": 6.5,
    "streak_days": 4
  },
  "recent_questions": [],
  "recent_practices": [],
  "weak_dimensions": [
    {
      "dimension": "内容覆盖",
      "avg_score_rate": 0.58
    }
  ]
}
```

#### `GET /api/me/stats`

用途：
提供更完整的统计页数据。

建议支持查询参数：

- `date_from`
- `date_to`
- `question_type`

#### `GET /api/me/weaknesses`

用途：
返回按维度、题型、标签聚合后的薄弱项。

### 3.3 题目收藏接口

你现在只有 `practice_record.favorite`，没有“题目收藏”。

#### `PATCH /api/questions/{question_id}/favorite`

#### `GET /api/questions/favorites`

这两个接口很适合支撑：

- 收藏题目
- 待练题单
- 高频复训题单

## 4. 第三优先级

这一组更偏平台化能力，适合第二阶段做。

### 4.1 错题本 / 复盘洞察

#### `GET /api/insights/wrong-notes`

用途：
按“常见问题类型”聚合历史问题。

建议支持维度：

- `question_type`
- `tag`
- `dimension`
- `date_from`
- `date_to`

建议响应：

```json
{
  "items": [
    {
      "dimension": "结构组织",
      "issue_count": 9,
      "common_issues": [
        "分点不稳",
        "总分关系不清"
      ],
      "related_reviews": [90, 91, 95]
    }
  ]
}
```

### 4.2 报告对比接口

#### `GET /api/reviews/compare?left_review_id=90&right_review_id=96`

用途：
比较同一题或同类题的两次训练结果。

建议响应：

```json
{
  "score_delta": 8,
  "dimension_deltas": [
    {
      "dimension": "内容覆盖",
      "left_score": 16,
      "right_score": 22,
      "delta": 6
    }
  ],
  "improved_points": [],
  "remaining_issues": []
}
```

### 4.3 训练推荐接口

#### `GET /api/training-plans/recommendations`

用途：
按用户薄弱项推荐题目。

建议响应：

```json
{
  "basis": {
    "weak_question_types": ["概括题"],
    "weak_dimensions": ["内容覆盖"]
  },
  "recommended_questions": [
    {
      "question_id": 101,
      "reason": "适合训练概括题的内容覆盖"
    }
  ]
}
```

## 5. 后台侧建议补的接口

### 5.1 导入预检

#### `POST /api/questions/import/preview`

用途：
先校验导入文件，再正式提交。

建议响应：

```json
{
  "valid_count": 18,
  "invalid_count": 2,
  "errors": [
    {
      "row": 6,
      "message": "title 为空"
    }
  ]
}
```

### 5.2 题库状态管理

#### `PATCH /api/questions/{question_id}/status`

用途：
支持题目上架、下架、归档，而不是只能删除。

### 5.3 题库管理统计

#### `GET /api/admin/questions/stats`

建议返回：

- 题目总数
- 按题型分布
- 按来源分布
- 本周新增数量

## 6. 为了支撑这些接口，数据层建议补什么

当前 `questions` 表对练习页支撑明显不够。建议不要把所有内容继续塞进一个 `content` 字段里。

### 6.1 题目结构补充

可以选两种方式：

#### 方案 A：按结构拆表，推荐

- `question_materials`
- `question_answer_sections`
- `question_favorites`

并扩展 `questions`：

- `category`
- `year`
- `region`
- `difficulty`
- `theme`
- `suggested_minutes`
- `cover_note`
- `intro`
- `overview`
- `reference_answer`
- `optimized_example`
- `status`

#### 方案 B：先用 JSON 过渡

给 `questions` 增加：

- `meta_json`
- `materials_json`
- `answer_sections_json`

如果你现在想先快一点跑通前后端联调，可以先用 B，再在下一轮拆表。

### 6.2 练习会话表

建议新增 `practice_sessions`：

- `id`
- `user_id`
- `question_id`
- `answer_id`
- `status`
- `answers_json`
- `elapsed_seconds`
- `started_at`
- `submitted_at`
- `updated_at`

状态建议：

- `drafting`
- `submitted`
- `reviewing`
- `completed`
- `abandoned`

### 6.3 批改任务表

建议新增 `review_jobs`：

- `id`
- `user_id`
- `question_id`
- `answer_id`
- `review_id`
- `status`
- `current_step`
- `progress_percent`
- `error_message`
- `created_at`
- `updated_at`
- `finished_at`

### 6.4 题目收藏表

建议新增 `question_favorites`：

- `id`
- `user_id`
- `question_id`
- `created_at`

并做唯一约束：

- `(user_id, question_id)`

## 7. 路由组织建议

当前 `practice` 模块接口是平铺的：

- `/api/answers`
- `/api/outline`
- `/api/review`
- `/api/practice-records`

接口数量再涨下去会越来越散。建议新增接口开始统一归组：

- `/api/questions/*`
- `/api/practice-sessions/*`
- `/api/review-jobs/*`
- `/api/reviews/*`
- `/api/me/*`
- `/api/insights/*`

老接口先不动，新增接口按新分组走，后面逐步迁移。

## 8. 推荐开发顺序

### 第一批

1. `GET /api/questions/{id}/workspace`
2. `practice_sessions` 表和 4 个会话接口
3. 题目结构字段补齐

目标：
把练习页从 mock 数据和 localStorage 切到真实后端。

### 第二批

1. `review_jobs` 表和 3 个异步批改接口
2. 提交后跳转“批改中”
3. 批改完成再进入报告页

目标：
解决同步批改阻塞问题。

### 第三批

1. `GET /api/me/dashboard`
2. `GET /api/me/weaknesses`
3. 收藏题目
4. 错题本

目标：
补齐平台的长期训练价值。

### 第四批

1. 报告对比
2. 二次改写
3. 训练推荐

目标：
把“批改工具”升级成“训练闭环平台”。

## 9. 结合当前代码的最小实现路径

从现有代码看，第一批并不需要重写批改核心，更多是“包装”和“聚合”。

### 9.1 可以直接复用的能力

当前已经有这些现成能力：

- `PracticeService.analyze_question`
- `PracticeService.generate_outline`
- `PracticeService.review_answer`
- `PracticeService.review_answer_from_content`
- `ReviewService.get_review_detail`
- `PracticeService.list_practice_records`

所以新增接口时建议这样复用：

#### `GET /api/questions/{id}/workspace`

可以由以下几部分组装：

- 题目主体：复用 `question` 模块查询
- 最近草稿：查 `practice_sessions`
- 最近一次报告：查 `practice_records` 或 `reviews`
- 题目结构化内容：来自新增字段或新增子表

#### `POST /api/practice-sessions/{id}/submit`

内部不必重新写批改逻辑，可以直接调用：

- `PracticeService.review_answer_from_content`

只是把它放到“会话提交”动作后面，并把返回值转换成：

- `answer_id`
- `review_job_id` 或 `review_id`
- `status`

#### `GET /api/me/dashboard`

可以先做轻量版：

- 最近题目：复用 `questions` 列表
- 最近练习：复用 `list_practice_records`
- 统计值：直接基于 `practice_records` 和 `reviews` 聚合

先跑通首页和个人中心，再决定是否拆更复杂的统计服务。

### 9.2 第一批建议的最小切法

如果你想尽快从 mock 切到真实接口，建议只做下面这些：

1. 给 `questions` 扩展必要字段
2. 增加 `question_materials` 和 `question_answer_sections`
3. 增加 `practice_sessions`
4. 新增 `GET /api/questions/{id}/workspace`
5. 新增 `GET/POST/PATCH /api/practice-sessions*`
6. 提交时先继续走同步批改

这样第一阶段的收益已经很大：

- 题库详情不再是简化版
- 练习页不再依赖本地草稿
- 多端可继续练习
- 前后端可以彻底脱离 mock 数据

### 9.3 异步批改可以第二批再做

现在的 `PracticeService._execute_review` 已经把批改主链组织好了：

- 校验题目和答案
- 读取模型配置
- 构造 `ReviewRequest`
- 执行 review workflow
- 落 `review`
- 落 `review_steps`
- 落 `practice_record`

所以异步化时不应该改动这条链，而应该在外面包一层任务机制：

1. 接口创建 `review_job`
2. 后台 worker 调用 `_execute_review`
3. 将结果回写到 `review_job.review_id`
4. 前端轮询 job 状态

这样改动范围最小，风险最低。

### 9.4 二次改写接口也可以先做轻量版

`rewrite-outline` 和 `rewrite-draft` 不一定要一上来就做成复杂 agent。

第一版可以先：

- `rewrite-outline`：基于 `review.report.outline`、`suggestions`、`comparison.missing_points` 组装
- `rewrite-draft`：后续再接 LLM

这样你能先把“报告 -> 下一稿训练”入口打通。
