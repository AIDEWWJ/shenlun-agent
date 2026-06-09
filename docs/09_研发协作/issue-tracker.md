# Issue 追踪器：GitHub

本项目的 Issue 和 PRD 以 GitHub Issues 形式存储，所有操作通过 `gh` CLI 完成。

## 常用操作

- **创建 issue**：`gh issue create --title "..." --body "..."`，多行内容用 heredoc
- **查看 issue**：`gh issue view <编号> --comments`，可配合 `jq` 过滤评论和标签
- **列出 issues**：`gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`
- **评论**：`gh issue comment <编号> --body "..."`
- **添加/移除标签**：`gh issue edit <编号> --add-label "..."` / `--remove-label "..."`
- **关闭**：`gh issue close <编号> --comment "..."`

`gh` 会自动从 `git remote -v` 推断仓库，无需手动指定。

## Skill 如何使用

- 当 skill 说"发布到 issue 追踪器"时 → 创建 GitHub issue
- 当 skill 说"获取相关 ticket"时 → 执行 `gh issue view <编号> --comments`
