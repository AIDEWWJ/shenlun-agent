# AI 配置与调参说明

## 一、文档目标

这份文档专门说明当前仓库里两类 AI 相关配置：

1. `prompts`
2. `system_configs`

目标是让后续调参时不需要再翻代码，能够快速知道：

- 每一类配置项叫什么
- 默认值是什么
- 会影响哪条链路
- 推荐怎么调
- 由谁来修改

当前约定是：

- **Prompt 类**：仅管理员维护
- **运行时规则类**：仅管理员维护
- 普通用户只负责选择模型、温度、API 接口等“运行参数”，不直接控制系统级批改逻辑

---

## 二、配置分类

## 2.1 Prompt 类

存储位置：

- 表：`prompt_templates`
- 代码默认值：[backend/app/modules/prompt/service.py](/C:/Users/aide/Desktop/ai/20260416_shenlun-agent/backend/app/modules/prompt/service.py)

管理员接口：

- `GET /api/admin/prompts`
- `PUT /api/admin/prompts/{template_type}`

## 2.2 运行时规则类

存储位置：

- 表：`system_configs`
- 代码默认值：[backend/app/modules/system_config/service.py](/C:/Users/aide/Desktop/ai/20260416_shenlun-agent/backend/app/modules/system_config/service.py)

管理员接口：

- `GET /api/admin/system-configs`
- `PUT /api/admin/system-configs/{config_key}`

---

## 三、Prompt 类说明

## 3.1 批改链 Prompt

### `review_system`

作用：

- AI 主批改提示词
- 控制总评分、分维度评价、修改建议、批改解释和提纲建议的输出风格

默认方向：

- 强调语义理解，不机械依赖字数和死规则
- 要求完整输出 `dimensions / score_breakdown / comparison_analysis / suggestions`
- 面向最终批改报告页展示

什么时候调：

- AI 批改风格不稳定
- 总结过空、建议不具体
- 分维度输出不完整

推荐调法：

- 优先改“输出要求”和“字段完整性要求”
- 尽量不要在这里堆太多题型细节

### `review_repair`

作用：

- 当第一次 AI 批改结果结构不完整时，第二次调用的修正提示词

默认方向：

- 不是重写结论，而是补齐结构
- 优先补 `dimensions / score_breakdown / comparison_analysis / suggestions / summary / analysis_explanation`

什么时候调：

- 第一次批改经常缺字段
- 第二次修正会改偏原结论

推荐调法：

- 明确“保留原结论方向，只修结构”
- 明确“核心字段优先级”

### `review_qa`

作用：

- 围绕批改结果进行追问答疑的提示词

默认方向：

- 只能基于已有批改证据回答
- 支持结合历史追问上下文
- 强调“为什么这样批改、怎么改”

什么时候调：

- 答疑太空泛
- 答疑容易编造证据
- 答疑不够像老师讲解

推荐调法：

- 收紧“证据边界”
- 强调“可执行修改建议”

## 3.2 分析与抽取 Prompt

### `question_analysis_system`

作用：

- 题目分析的系统角色提示

影响：

- 题型识别
- 任务要求拆解
- 评分重点提炼
- 结构提示输出

### `question_analysis_user`

作用：

- 题目分析的用户输入模板

当前变量：

- `{question_title}`
- `{question_content}`
- `{question_type}`
- `{reference_points}`

### `reference_point_extract_system`

作用：

- 参考要点抽取的系统角色提示

### `reference_point_extract_user`

作用：

- 参考要点抽取的用户输入模板

当前变量：

- `{reference_points_text}`
- `{question_type}`
- `{scoring_focus}`
- `{question_analysis_json}`

### `user_point_extract_system`

作用：

- 用户答案要点抽取的系统角色提示

### `user_point_extract_user`

作用：

- 用户答案要点抽取的用户输入模板

当前变量：

- `{question_title}`
- `{question_content}`
- `{question_type}`
- `{question_analysis_json}`
- `{reference_points_text}`
- `{answer_content}`

### `outline_generate_system`

作用：

- 提纲生成的系统角色提示

### `outline_generate_user`

作用：

- 提纲生成的用户输入模板

当前变量：

- `{question_type}`
- `{scoring_focus}`
- `{missing_points}`
- `{matched_points}`
- `{question_analysis_json}`
- `{comparison_json}`

---

## 四、运行时规则类说明

## 4.1 `point_compare`

作用：

- 控制要点比对时“命中 / 部分命中 / 漏答”的判断阈值

默认值：

```json
{
  "exact_match_threshold": 0.82,
  "partial_match_threshold": 0.45,
  "max_keyword_length": 12,
  "max_keywords_per_point": 12
}
```

字段说明：

- `exact_match_threshold`：达到这个相似度才算命中
- `partial_match_threshold`：达到这个相似度但不足命中时算部分命中
- `max_keyword_length`：关键词最大长度
- `max_keywords_per_point`：每个要点最多保留多少关键词

推荐调法：

- 命中过严：适当降低 `exact_match_threshold`
- 部分命中过多：提高 `partial_match_threshold`

## 4.2 `structure_analysis`

作用：

- 控制结构分析器的词表和加分逻辑

默认值：

```json
{
  "markers": ["首先", "其次", "再次", "最后", "一是", "二是", "三是", "第一", "第二", "第三", "综上", "因此", "总之", "一方面", "另一方面"],
  "min_paragraphs_for_bonus": 2,
  "low_coverage_threshold": 0.5,
  "base_score": 10,
  "paragraph_bonus": 6,
  "marker_bonus_unit": 2,
  "marker_bonus_cap": 5,
  "bullet_bonus_unit": 2,
  "bullet_bonus_cap": 4,
  "applied_doc_bonus": 2
}
```

什么时候调：

- 结构分普遍偏高或偏低
- 某类题目结构判断不合适

## 4.3 `language_analysis`

作用：

- 控制语言分析器的词表、标点阈值和短文惩罚

默认值：

```json
{
  "formal_markers": ["因此", "综上", "建议", "需要", "应当", "必须", "要", "应该", "首先", "其次", "再次", "最后", "一是", "二是", "三是", "一方面", "另一方面"],
  "punctuation_targets": ["，", "。", "；"],
  "punctuation_threshold": 5,
  "formal_marker_threshold": 2,
  "formal_marker_bonus_unit": 2,
  "formal_marker_bonus_cap": 8,
  "min_paragraphs_for_bonus": 2,
  "short_answer_threshold": 80,
  "short_answer_penalty": 2,
  "base_score": 10,
  "punctuation_bonus": 5,
  "paragraph_bonus": 2
}
```

什么时候调：

- 语言分过于依赖连接词
- 短答案惩罚太重或太轻

## 4.4 `rule_validation`

作用：

- 控制规则校验器的阈值和惩罚分

说明：

- 当前主批改链已经是 AI 主导
- 这组配置主要用于兼容性规则校验，不建议继续强化它的主导作用

默认值：

```json
{
  "min_answer_length": 80,
  "min_answer_penalty": 6,
  "max_answer_length": 3000,
  "max_answer_penalty": 3,
  "zero_coverage_penalty": 8,
  "summary_question_max_length": 1200,
  "summary_overlength_penalty": 4,
  "applied_doc_min_paragraphs": 2,
  "applied_doc_structure_penalty": 4,
  "penalty_cap": 25,
  "summary_question_type_hints": ["概括", "归纳", "提炼"],
  "applied_doc_type_hints": ["贯彻执行", "应用文", "公文"]
}
```

## 4.5 `practice_fallback`

作用：

- 控制无 LLM 或异常回退时的题型推断和结构提示

默认值：

```json
{
  "question_type_mapping": [["概括", "概括题"], ["对策", "对策题"], ["公文", "公文题"], ["写作", "大作文"], ["作文", "大作文"], ["综合分析", "综合分析"]],
  "structured_question_types": ["对策题", "概括题", "大作文"],
  "structured_hints": ["总分总", "分点作答"],
  "default_hints": ["分层展开"]
}
```

什么时候调：

- fallback 识别题型不准
- fallback 结构提示过于单一

---

## 五、推荐调参顺序

如果你要调 AI 效果，不建议一次全改，推荐顺序是：

1. `review_system`
2. `review_repair`
3. `review_qa`
4. `question_analysis_*`
5. `reference_point_extract_*`
6. `user_point_extract_*`
7. `outline_generate_*`
8. `point_compare`
9. `structure_analysis`
10. `language_analysis`
11. `rule_validation`
12. `practice_fallback`

原则：

- 先调 prompt，再调阈值
- 先调主链，再调 fallback
- 规则类配置优先保持克制，避免重新把主链拉回“规则批改”

---

## 六、运维建议

### Prompt 类修改

通过管理员接口：

- `GET /api/admin/prompts`
- `PUT /api/admin/prompts/{template_type}`

### 运行时规则类修改

通过管理员接口：

- `GET /api/admin/system-configs`
- `PUT /api/admin/system-configs/{config_key}`

### 调参建议

- 每次只改一个配置项
- 每次调整后至少拿固定样例回归一次
- 记录“改前问题、改后效果、是否回滚”

---

## 七、当前代码落点

Prompt 默认值：

- [backend/app/modules/prompt/service.py](/C:/Users/aide/Desktop/ai/20260416_shenlun-agent/backend/app/modules/prompt/service.py)

运行时默认值：

- [backend/app/modules/system_config/service.py](/C:/Users/aide/Desktop/ai/20260416_shenlun-agent/backend/app/modules/system_config/service.py)

能力模块读取位置：

- [question_analyzer.py](/C:/Users/aide/Desktop/ai/20260416_shenlun-agent/backend/app/ai/capabilities/analyzers/question_analyzer.py)
- [reference_point_extractor.py](/C:/Users/aide/Desktop/ai/20260416_shenlun-agent/backend/app/ai/capabilities/extractors/reference_point_extractor.py)
- [user_point_extractor.py](/C:/Users/aide/Desktop/ai/20260416_shenlun-agent/backend/app/ai/capabilities/extractors/user_point_extractor.py)
- [outline_generator.py](/C:/Users/aide/Desktop/ai/20260416_shenlun-agent/backend/app/ai/capabilities/generators/outline_generator.py)
- [point_comparator.py](/C:/Users/aide/Desktop/ai/20260416_shenlun-agent/backend/app/ai/capabilities/comparators/point_comparator.py)
- [structure_analyzer.py](/C:/Users/aide/Desktop/ai/20260416_shenlun-agent/backend/app/ai/capabilities/analyzers/structure_analyzer.py)
- [language_analyzer.py](/C:/Users/aide/Desktop/ai/20260416_shenlun-agent/backend/app/ai/capabilities/analyzers/language_analyzer.py)
- [rule_validator.py](/C:/Users/aide/Desktop/ai/20260416_shenlun-agent/backend/app/ai/capabilities/validators/rule_validator.py)
- [practice/service.py](/C:/Users/aide/Desktop/ai/20260416_shenlun-agent/backend/app/modules/practice/service.py)
