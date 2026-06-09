# 申论 Agent 布局设计

## 一、设计前提

这份布局设计**不再以当前前端页面为依据**，而是直接以 [API_DESIGN.md](../04_接口与数据/API_DESIGN.md) 和后端实际接口分组为依据，从接口能力反推：

> 当前前台收敛口径：用户侧题库入口统一使用 `/papers`，用于承载套卷练习和独立题目；不保留 `/questions` 页面路由。个人 AI 配置归入 `/profile/ai-config`，旧 `/ai-config` 重定向到个人 AI 配置页。

1. 用户会进入哪些页面
2. 每个页面需要承载哪些数据和动作
3. 哪些布局是后端已经支撑的
4. 哪些布局其实被后端接口缺口卡住了

结论先说：

- 现在前端的信息架构不应该继续作为主依据
- 页面布局应该围绕 `auth / questions / practice / reviews / ai-config / admin` 这些接口域来设计
- “历史记录”页面不能按泛化学习中心来设计，因为后端当前只稳定提供了 `reviews` 记录，不是完整 practice history
- “练习页”不能假设前端可以自由保存草稿，因为后端当前没有独立的答案创建/保存接口

---

## 二、后端接口域

## 2.1 认证与账户域

接口：

- `POST /api/auth/register/send-code`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `PUT /api/auth/me`
- `POST /api/auth/me/password`
- `POST /api/auth/forgot-password/send-code`
- `POST /api/auth/forgot-password`

对应前端页面能力：

- 登录
- 注册
- 找回密码
- 当前用户信息展示
- 修改资料
- 修改密码

## 2.2 题库域

接口：

- `GET /api/questions`
- `GET /api/questions/{question_id}`
- `POST /api/questions`
- `POST /api/questions/import`
- `PUT /api/questions/{question_id}`
- `DELETE /api/questions/{question_id}`

对应前端页面能力：

- 题库列表
- 题目详情
- 新建题目
- 批量导入
- 编辑题目
- 删除题目

## 2.3 练习链路域

接口：

- `POST /api/analyze`
- `POST /api/outline`
- `POST /api/review`

对应前端页面能力：

- 审题分析
- 提纲生成
- 发起批改

注意：

- `review` 依赖 `question_id + answer_id`
- 后端当前没有独立公开的 `answer create / answer update / answer list` 接口
- 所以“练习页”在信息架构上存在接口缺口，不能简单按完整写作平台来设计

## 2.4 批改记录域

接口：

- `GET /api/reviews`
- `GET /api/reviews/{review_id}`

对应前端页面能力：

- 批改记录列表
- 批改报告详情

## 2.5 用户 AI 配置域

接口：

- `GET /api/ai-configs/me`
- `POST /api/ai-configs/me`
- `PUT /api/ai-configs/me/{config_id}`
- `DELETE /api/ai-configs/me/{config_id}`
- `POST /api/ai-configs/me/{config_id}/default`
- `GET /api/ai-configs/system-default`

对应前端页面能力：

- 查看当前用户模型方案
- 新建模型方案
- 编辑模型方案
- 删除模型方案
- 设为默认
- 查看系统默认模型说明

## 2.6 管理后台域

接口：

- `GET /api/admin/users`
- `GET /api/admin/users/{user_id}`
- `POST /api/admin/users`
- `PUT /api/admin/users/{user_id}`
- `DELETE /api/admin/users/{user_id}`
- `GET /api/admin/ai-configs/system`
- `POST /api/admin/ai-configs/system`
- `PUT /api/admin/ai-configs/system/{config_id}`
- `DELETE /api/admin/ai-configs/system/{config_id}`
- `POST /api/admin/ai-configs/system/{config_id}/default`
- `GET /api/admin/email/configs`
- `POST /api/admin/email/configs`
- `PUT /api/admin/email/configs/{config_id}`
- `DELETE /api/admin/email/configs/{config_id}`
- `GET /api/admin/email/templates`
- `POST /api/admin/email/templates`
- `PUT /api/admin/email/templates/{template_key}`
- `DELETE /api/admin/email/templates/{template_key}`

对应前端页面能力：

- 用户管理
- 系统模型配置管理
- 邮件发送配置管理
- 邮件模板管理

---

## 三、按接口反推的信息架构

如果完全按后端接口组织前端，建议信息架构收敛成四套壳。

## 3.1 Auth Shell

承接：

- 登录
- 注册
- 找回密码

特点：

- 单独入口
- 不混入站内复杂导航
- 适合双栏或居中结构

## 3.2 User Workspace Shell

承接：

- 题库
- 批改记录
- AI 配置
- 个人资料

特点：

- 是登录后普通用户的主壳
- 顶部导航稳定
- 适合列表、详情、配置类页面

## 3.3 Practice Workbench Shell

承接：

- 审题
- 提纲
- 批改发起

特点：

- 强任务型
- 强上下文
- 页面内部自带工具条和侧栏

注意：

- 这个壳的中间编辑区能否完全成立，取决于后端是否补齐答案接口

## 3.4 Admin Console Shell

承接：

- 用户管理
- 系统 AI 配置
- 邮件配置
- 邮件模板

特点：

- 左侧菜单 + 右侧工作区
- 密集操作型，不需要首页式视觉铺陈

---

## 四、推荐导航结构

## 4.1 普通用户主导航

登录后顶层导航建议只保留 4 个主入口：

- `题库`
- `批改记录`
- `AI 配置`
- `账户`

右上角保留：

- `开始练习`
- 用户头像菜单

不建议把“关于”“首页展示”“后台入口”等和主训练路径并列。

## 4.2 管理员导航

管理员在普通用户导航之外，增加后台入口。

后台左侧菜单建议固定为：

- `用户管理`
- `系统模型`
- `邮件配置`
- `邮件模板`
- `题库管理`

说明：

- 虽然当前后端没有单独的 `/api/admin/questions`
- 但 `questions` 的创建、修改、删除已经具备，管理员可基于同一题库接口做管理界面

---

## 五、接口驱动的页面布局

## 5.1 认证中心

后端接口决定这不是简单登录页，而是一个三态认证中心：

- 登录
- 注册
- 找回密码

### 推荐布局

- 左侧：表单区
- 右侧：流程说明区

左侧表单区按状态切换：

- 登录：用户名、密码、提交
- 注册：用户名、邮箱、验证码、密码、发送验证码、注册
- 找回密码：用户名、邮箱、验证码、新密码、发送验证码、确认重置

右侧流程说明区固定显示：

- 当前流程说明
- 验证码规则
- 账号安全提示

### 线框

```text
+---------------------------------------------------------------+
| Brand                                                         |
+-------------------------------+-------------------------------+
| 登录/注册/找回密码表单        | 流程说明 / 验证码提示         |
| 用户名                        | 注册需要邮箱验证               |
| 邮箱 / 验证码 / 密码          | 找回密码也走验证码             |
| 提交按钮                      | 登录后进入题库工作区           |
+-------------------------------+-------------------------------+
```

## 5.2 题库工作区

后端 `questions` 域支持：

- 列表查询
- 条件筛选
- 新建
- 导入
- 详情查看
- 编辑
- 删除

所以题库页不能只是浏览页，必须是“浏览 + 管理”混合工作区。

### 推荐布局

- 左侧：筛选栏
- 中间：题目列表
- 右侧：上下文操作区

左侧筛选栏对应接口参数：

- `keyword`
- `question_type`
- `tag`
- `source`
- `user_id`（仅管理员或特殊视角）

中间列表对应接口返回：

- `title`
- `question_type`
- `tags`
- `source`
- `created_at`

右侧操作区对应接口动作：

- `新建题目`
- `批量导入`
- `编辑当前题目`
- `删除当前题目`
- `查看详情`

### 线框

```text
+--------------------------------------------------------------------------+
| 题库 | 搜索 | 新建题目 | 批量导入                                       |
+----------------+--------------------------------------+------------------+
| 筛选栏         | 题目列表                             | 操作区           |
| 关键词         | 标题 / 题型 / 标签 / 来源 / 时间     | 查看详情         |
| 题型           | [选择当前行]                         | 开始分析         |
| 标签           |                                      | 编辑             |
| 来源           |                                      | 删除             |
+----------------+--------------------------------------+------------------+
```

### 设计重点

- 题库是后端最完整的业务域之一，布局上必须给足操作能力
- 不要把“新建/导入/编辑/删除”拆到过多独立页面，优先抽屉或弹窗

## 5.3 题目详情页

后端 `GET /api/questions/{question_id}` 返回的是完整题目实体，题目详情页应当是“阅读 + 进入练习链路”的跳板。

### 推荐布局

- 主内容区：题干全文
- 右侧动作区：基于 practice 接口的动作入口

右侧动作区只放和现有接口匹配的动作：

- `审题分析`
- `生成提纲`
- `进入练习工作台`

如果用户对题目有编辑权限，额外显示：

- `编辑题目`
- `删除题目`

### 设计重点

- 题干正文优先，不要在详情页堆叠过多训练结果
- 训练结果应当进入独立的 practice / review 工作面

## 5.4 练习工作台

这个页面必须完全按 `analyze / outline / review` 三个接口来设计，而不是按“当前前端已经有什么组件”设计。

### 当前接口现实

- `analyze` 只需要 `question_id`
- `outline` 只需要 `question_id`
- `review` 需要 `question_id + answer_id`

因此练习工作台应该拆成两层：

### A. 当前后端可稳定支撑的布局

- 左栏：题目上下文
- 中栏：作答区
- 右栏：AI 辅助区

但中栏当前只能承担：

- 本地写作
- 显示当前文本
- 预留未来答案保存能力

右栏可稳定接后端的只有：

- 审题分析
- 提纲生成

`提交批改` 必须建立在已有 `answer_id` 的前提下。

### B. 推荐的真实产品布局

如果后端补齐答案接口后，练习页应当固定成三栏：

- 左栏：题目区
- 中栏：写作编辑区
- 右栏：AI 训练辅助区

### 当前阶段推荐布局

```text
+--------------------------------------------------------------------------+
| 题目标题 | 审题 | 提纲 | 批改 | 状态提示                                 |
+-------------------+---------------------------+---------------------------+
| 题目上下文        | 写作区                    | AI 辅助区                |
| 标题/题干/题型    | 当前答案文本              | 审题分析结果             |
| 参考要点          | 本地草稿状态              | 提纲生成结果             |
|                   | 批改按钮状态说明          | 批改前提示               |
+-------------------+---------------------------+---------------------------+
```

### 批改按钮的正确布局逻辑

因为后端接口要求 `answer_id`，所以按钮区必须明确三种状态：

- `不可用`：还没有可用 answer_id
- `可批改`：已有 answer_id，可以请求 `/api/review`
- `需补接口`：提醒当前链路后端未闭合

这比假装“随时可提交批改”更真实。

## 5.5 批改记录页

这里不应再叫“历史记录中心”，而应叫“批改记录”或“批改报告列表”。

原因：

- 后端当前提供的是 `GET /api/reviews`
- 它返回的是 review list item，不是完整的练习 history

### 推荐布局

- 顶部筛选工具条
- 中间报告记录列表
- 右侧摘要面板

列表应以这些字段为主：

- `question_title`
- `question_type`
- `score`
- `summary`
- `model_provider`
- `model_name`
- `created_at`

### 线框

```text
+--------------------------------------------------------------------------+
| 批改记录 | 搜索 | 题型筛选 | 时间排序                                   |
+------------------------------------------+-------------------------------+
| 记录列表                                 | 选中项摘要                    |
| 标题 / 分数 / 摘要 / 时间                | 总分                          |
| [查看报告]                               | 模型                          |
|                                          | 时间                          |
|                                          | 进入详情                      |
+------------------------------------------+-------------------------------+
```

## 5.6 批改报告详情页

这个页面应严格围绕 `ReviewDetail` 结构来设计。

后端返回字段包含：

- `question_content`
- `answer_content`
- `reference_points`
- `question_analysis`
- `reference_point_analysis`
- `user_point_analysis`
- `comparison`
- `structure_analysis`
- `language_analysis`
- `rule_analysis`
- `score_breakdown`
- `report`
- `strengths`
- `issues`
- `suggestions`
- `steps`

所以报告详情页应该是“结构化证据页”，而不是单一长文页。

### 推荐布局

- 顶部摘要条
- 左侧章节导航
- 中间报告正文
- 右侧证据/动作栏

左侧章节导航：

- 总评
- 分项得分
- 命中/漏答
- 结构分析
- 语言分析
- 规则校验
- 建议
- 步骤证据

右侧动作栏：

- 返回题目
- 返回批改记录
- 基于建议重新作答
- 预留答疑入口

### 设计重点

- `steps` 是很强的后端资产，必须可视化
- 不要只展示最终分数，必须体现批改过程证据

## 5.7 AI 配置页

后端 `ai-configs` 域天然适合“双栏配置工作区”。

### 推荐布局

- 左栏：配置列表
- 右栏：配置编辑器

顶部加一条系统默认配置说明：

- 来自 `GET /api/ai-configs/system-default`

左栏显示：

- 配置名
- 模型名
- 默认标记
- 创建时间

右栏表单直接对应 schema：

- `provider`
- `model_name`
- `api_key`
- `base_url`
- `temperature`
- `system_prompt`

动作：

- 保存
- 设为默认
- 删除

## 5.8 账户页

账户页只服务两组接口：

- `GET /api/auth/me`
- `PUT /api/auth/me`
- `POST /api/auth/me/password`

所以它不应该是大而全的学习中心，而应该是窄而清晰的账户维护页。

### 推荐布局

- 左侧：账户菜单
- 右侧：基本信息 / 修改密码两个工作面

账户菜单：

- 基本资料
- 修改密码

右侧面板：

- 当前账户摘要
- 可编辑表单

## 5.9 管理后台

后台布局必须严格按后台接口分组来设计，不要做成普通用户页面的翻版。

### 后台一级菜单

- 用户管理
- 系统模型
- 邮件配置
- 邮件模板
- 题库管理

### 用户管理页

因为后端支持列表、详情、创建、更新、删除，所以推荐：

- 左侧用户列表
- 右侧详情编辑面板

### 系统模型页

推荐：

- 左侧配置列表
- 右侧编辑器
- 顶部主按钮：新建配置

### 邮件页

邮件配置和邮件模板建议分两个标签页：

- `发送配置`
- `模板管理`

不要塞在一个滚动巨页里。

---

## 六、当前前台路由结构

这里记录当前前台收敛后的实际路由口径和后续建议。

### 公共区

- `/auth`：登录、注册、找回密码
- `/`：首页
- `/about`：关于页

### 用户工作区

- `/papers`：统一题库入口，承载套卷练习和独立题目
- `/history`：练习记录
- `/reports/:reportId`：批改报告详情
- `/profile/basic`：个人资料
- `/profile/security`：安全设置
- `/profile/ai-config`：个人 AI 配置
- `/error-notebook`：错题本
- `/study-plan`：学习计划

### 练习工作台

- `/practice/paper/:paperId`：套卷练习
- `/practice/:questionId`：单题练习

### 管理后台

- `/admin`：后台总览
- `/admin/users`：用户管理
- `/admin/ai-configs`：系统 AI 配置
- `/admin/email`：邮件配置

说明：

- 后台题库 / Prompt / 系统运行配置页面暂不在当前前台收敛阶段实现。
- 后端 `/api/questions` 仍保留为题目数据接口，不等于前台保留 `/questions` 页面路由。

---

## 七、接口状态对布局的影响

这是当前最关键的纠偏部分。早期文档中提到的答案、练习记录、答疑接口已经在当前代码中补齐，前台布局应从“接口缺失”转为“入口收敛与展示优化”。

## 7.1 答案接口当前状态

当前代码已经有答案相关接口：

- `POST /api/answers`
- `GET /api/questions/{question_id}/answers`
- `GET /api/answers/{answer_id}`
- `PUT /api/answers/{answer_id}`
- `POST /api/answers/{answer_id}/duplicate`

后续影响：

- 需要继续改善前端保存失败提示、自动保存状态和答案版本展示。
- 练习记录页需要更清晰地区分试卷练习和单题练习。

## 7.2 练习记录接口当前状态

当前代码已经有练习记录相关接口：

- `GET /api/practice-records`
- `GET /api/practice-records/{record_id}`
- `PATCH /api/practice-records/{record_id}/favorite`

后续影响：

- 前端可以做完整练习历史中心。
- 下一步重点是按 `paper_id` 区分试卷练习和独立题练习。

## 7.3 报告答疑接口当前状态

当前代码已经有报告答疑相关接口：

- `POST /api/reviews/{review_id}/qa`
- `GET /api/reviews/{review_id}/qa`
- `POST /api/reviews/{review_id}/qa/stream`

后续影响：

- 报告详情页可以将追问答疑作为真实功能。
- 下一步重点是优化消息状态、失败提示和证据引用展示。

---

## 八、建议先补的后端接口

如果要让布局真正成立，建议优先补下面 4 组接口：

### 1. 答案接口

- `POST /api/answers`
- `PUT /api/answers/{answer_id}`
- `GET /api/questions/{question_id}/answers`
- `GET /api/answers/{answer_id}`

### 2. 练习记录接口

- `GET /api/practice-records`
- `GET /api/practice-records/{record_id}`

### 3. 批改发起优化

当前 `POST /api/review` 依赖 `answer_id`。建议补一个更贴近前端的接口形态：

- `POST /api/review/from-content`

这样练习页可以直接提交：

- `question_id`
- `answer_content`
- `reference_points`

### 4. 答疑接口

- `POST /api/reviews/{review_id}/qa`
- `GET /api/reviews/{review_id}/qa`

---

## 九、最终布局结论

如果严格按后端接口来定布局，最正确的结论是：

1. 普通用户主壳应该围绕 `题库 / 批改记录 / AI 配置 / 账户` 四个接口域展开。
2. 题库页必须是“查询 + 创建 + 导入 + 编辑”的工作区，因为 `questions` 接口本身就是完整 CRUD。
3. 批改记录页应该明确叫“批改记录”，不要抽象成“历史中心”。
4. 报告详情页必须围绕 `ReviewDetail` 的结构化字段和 `steps` 证据来做。
5. 练习页当前只能做成“审题/提纲工作台 + 受限批改入口”，因为后端答案接口还没闭环。

这才是基于后端接口设计出来的真实布局，不会再被当前前端实现牵着走。
