# 练习系统设计方案

> 文档性质：目标设计方案。  
> 当前代码状态：后端已经有 `paper_practice_sessions`、`answers.paper_id`、`reviews.paper_id`、`practice_records.paper_id` 等字段和套卷练习链路，但单题练习仍保留 `/practice-sessions/*` 接口和单题会话服务；前台正在按“试卷 + 独立题统一题库”方向逐步收敛。

## 背景

当前系统存在单题练习会话接口和试卷练习会话接口，需要逐步统一为以试卷 / 题库为主体的练习体系，同时支持独立题目。

## 题目分类

```
题库
├── 试卷题目（paper_id 有值）
│   └── 属于某套试卷，整套练习
│
└── 独立题目（paper_id = null）
    └── 后续系统导入或用户自己导入，单题练习
```

## 数据库改动

### 1. 删除 practice_sessions 表（目标）

目标状态下，旧的单题练习会话表不再使用，统一用 `paper_practice_sessions` 或统一练习会话模型。当前代码仍保留单题 `/practice-sessions/*` 接口，暂不在前台一期中删除。

### 2. paper_practice_sessions 表（保留）

存储整套试卷的练习草稿。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键 |
| user_id | bigint | 用户ID |
| paper_id | bigint | 试卷ID |
| answers_json | text | 各题答案 JSON: {"question_id": "answer"} |
| current_index | int | 当前题目索引 |
| timer_seconds | int | 累计作答秒数 |
| status | varchar | drafting / submitted |
| started_at | datetime | 开始时间 |
| updated_at | datetime | 更新时间 |

### 3. answers 表（新增 paper_id）

| 字段 | 改动 |
|------|------|
| paper_id | **新增**，可为 NULL（独立题目） |

### 4. reviews 表（新增 paper_id）

| 字段 | 改动 |
|------|------|
| paper_id | **新增**，可为 NULL（独立题目） |

### 5. practice_records 表（新增 paper_id）

| 字段 | 改动 |
|------|------|
| paper_id | **新增**，可为 NULL（独立题目） |

## 数据流

### 试卷练习流程

```
1. 用户进入试卷 → 创建/恢复 paper_practice_sessions
2. 用户作答 → 实时保存到 answers_json（草稿）
3. 用户提交试卷 → 遍历每道题：
   a. 创建 answers 记录（带 paper_id）
   b. 触发 AI 批改（带 paper_id）
   c. 创建 reviews 记录（带 paper_id）
   d. 创建 practice_records（带 paper_id）
4. 跳转到批改结果页
```

### 独立题目练习流程（目标）

```
1. 用户进入独立题目 → 创建练习会话
2. 用户作答 → 保存草稿
3. 用户提交 → 创建 answers（paper_id=null）→ 批改 → reviews → practice_records
```

## 查询方式

### 练习记录查询

```python
# 按试卷查询（试卷内的所有题）
GET /practice-records?paper_id=10
→ 返回该试卷所有题目的练习记录，前端按题目分组展示

# 按单题查询（独立题目）
GET /practice-records?question_id=123
→ 返回该题的练习记录

# 用户全部记录
GET /practice-records
→ 返回所有记录，前端按 paper_id 分组展示
```

### 前端展示

```
练习记录页面
├── 试卷练习
│   ├── 2026年国考申论（2次练习）
│   │   ├── 第1次: 总分 280/400
│   │   │   ├── 第1题: 72分 [查看]
│   │   │   ├── 第2题: 65分 [查看]
│   │   │   ├── 第3题: 68分 [查看]
│   │   │   ├── 第4题: 75分 [查看]
│   │   │   └── 第5题: 80分 [查看]
│   │   └── 第2次: ...
│   └── 2026年广东省考（1次练习）
│       └── ...
│
└── 单题练习
    ├── 独立题目6: 70分 [查看]
    └── 独立题目7: 65分 [查看]
```

## 实施步骤

1. **数据库**：answers、reviews、practice_records 新增 paper_id 字段
2. **后端**：逐步减少对单题 `practice_sessions` 链路的依赖，提交批改时带 `paper_id`
3. **前端**：练习记录页面按试卷 / 独立题分组展示

## 影响范围

- 目标删除：`practice_sessions` 表及相关代码（当前暂保留）
- 修改：`answers`、`reviews`、`practice_records` 表及查询逻辑
- 新增：整套试卷提交批改的后端逻辑
- 修改：练习记录前端页面
