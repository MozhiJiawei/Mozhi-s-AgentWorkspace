# CCN任务服务

本目录只包含CCN任务接口的业务实现、数据库迁移和业务测试。Docker、网关、发布、备份与恢复位于仓库根目录的`deploy/resource-server/`。

## 接口

所有业务接口使用`Authorization: Bearer <API_KEY>`。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `POST` | `/api/v1/tasks` | 添加任务 |
| `GET` | `/api/v1/tasks/{task_id}` | 按编号获取任务 |
| `GET` | `/api/v1/tasks?status=pending` | 按状态分页获取 |
| `POST` | `/api/v1/tasks/{task_id}/results` | 追加处理结果 |
| `DELETE` | `/api/v1/tasks/{task_id}` | 删除任务及其历史结果 |
| `DELETE` | `/api/v1/tasks` | 批量删除最多200个任务及其历史结果 |

两个POST接口接受`Idempotency-Key`。任务状态为`pending`、`completed`或`failed`；查询同时接受“未领取”“已完成”“失败”别名。
任务列表还支持`q`、`hotspot_id`和`period`筛选参数。

## 任务状态台

`GET /dashboard`提供表格化任务状态页面。页面外壳不包含业务数据；使用统一API Key
登录后，浏览器才会调用受保护的任务列表接口。密钥只保存在当前标签页的
`sessionStorage`，关闭标签页即清除。

页面内的“API 接口文档”页签无需登录即可查看，提供五个主要接口的PowerShell调用示例。
示例只使用`<API_KEY>`代号，使用者必须替换为实际密钥，
且不得把真实密钥提交到版本库或放入URL、截图和公开日志。

结果请求示例：

```json
{
  "outcome": "completed",
  "artifact_urls": [
    "https://github.com/MozhiJiawei/ccn-report/tree/main/开源软件分析/Example/20260805-example-source-understanding-codex"
  ]
}
```

完成记录只提交`outcome`和`artifact_urls`。`artifact_urls`必须且只能包含一个URL：报告在GitHub默认分支上的目录直达地址；不传仓库根地址、本地路径、临时预览地址、`summary`或`metadata`。

服务端接受中文路径和 percent-encoded UTF-8 路径，并在校验后统一以可读的中文 IRI 形式计算幂等哈希和返回。数据库保留客户端提交时的原始 URL，不迁移或重写历史记录；幂等检查会同时兼容历史请求哈希和规范化哈希。ASCII 保留字符的转义保持不变，因此编码形式不同但语义相同的中文报告 URL 会命中同一幂等请求。

只有报告完成归档、通过仓库门禁、Pull Request 已实际合入默认分支且远端路径确认存在后，才能提交 `completed` 结果。

## 测试

```powershell
python -m pip install -e ".\loops\ccn-brief-report\task_service[test]"
python -m pytest loops/ccn-brief-report/task_service/tests
```

真实PostgreSQL和Redis验证使用`deploy/resource-server/compose.local.yml`。
