# 能力展示

`gh-issue-comment-monitor` 把 GitHub Issue 评论区转成相对本地 checkpoint 的新增评论结果，让 Agent 只处理新回复，不反复读取完整讨论历史。

| 输入 | 输出 | 最关键效果 |
| --- | --- | --- |
| 仓库、Issue 编号、本地 checkpoint | 新增评论列表、处理摘要、更新后的 checkpoint | 每次只看上次之后的新评论 |

![GitHub Issue 新回复跟进展示](./assets/issue-monitor-showcase.png)

这张图展示的是一次真实 Issue 跟进：本轮只处理 2 条新评论，没有把旧讨论重新塞进上下文。

## 适合场景

- 跟进某个 GitHub Issue 有没有新评论。
- 只读取上次处理之后的新回复。
- 从新回复里提炼要求、结论或阻塞点。
- 处理完成后记录进度，方便下次继续。

## 使用方式

你可以直接说：

```text
请检查这个 Issue 有没有新的回复，只处理上次之后的新评论。
```

或者：

```text
请读取这个 GitHub Issue 的最新 5 条评论，并在处理完成后记住进度。
```

## 处理过程

1. 读取 issue 的本地 checkpoint。
2. 拉取评论区里比 checkpoint 更新的新评论。
3. 输出新增评论和轻量摘要。
4. 用户或 Agent 处理这些新增内容。
5. 处理成功后更新 checkpoint。

## 交付物

| 交付物 | 用途 |
| --- | --- |
| updates JSON | 本轮新增评论列表 |
| 处理摘要 | 判断是否需要继续行动 |
| state checkpoint | 下次从正确位置继续 |

## 展示覆盖

| Case | 输入 | 输出 | 证明的能力 |
| --- | --- | --- | --- |
| Issue 新回复跟进 | GitHub Issue 和本地 checkpoint | 2 条新增评论、处理状态 | 避免重复读取完整 issue 历史 |
