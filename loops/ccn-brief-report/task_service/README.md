# CCN任务服务

本目录只包含CCN任务接口的业务实现、数据库迁移和业务测试。Docker、网关、发布、备份与恢复位于仓库根目录的`deploy/resource-server/`。

## 接口

所有业务接口使用`Authorization: Bearer <API_KEY>`。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `POST` | `/api/v1/tasks` | 添加任务 |
| `POST` | `/api/v1/tasks/batch` | 原子批量添加 1–200 个任务 |
| `GET` | `/api/v1/tasks/{task_id}` | 按编号获取任务 |
| `GET` | `/api/v1/tasks?status=pending` | 按状态分页获取 |
| `POST` | `/api/v1/tasks/{task_id}/results` | 追加处理结果 |
| `DELETE` | `/api/v1/tasks/{task_id}` | 删除任务及其历史结果 |
| `DELETE` | `/api/v1/tasks` | 批量删除最多200个任务及其历史结果 |

创建任务、批量创建和结果POST接口接受`Idempotency-Key`。任务状态为`pending`、`completed`或`failed`；查询同时接受“未领取”“已完成”“失败”别名。

`POST /api/v1/tasks` 支持可选 `category`：完整中文分类目录枚举，覆盖13个一级和50个二级。不传或null为AI自动分类；指定一级时继续在其范围内判断二级或综述直归，指定二级时严格归入该二级。空字符串、错误名称、无编号路径和非法组合返回422。创建响应、详情与列表均返回该字段，历史任务为null；不支持创建后修改，同一task_id改分类返回409。

例如 `"category": "04-AI模型"` 或 `"category": "04-AI模型/多模态模型与模型架构"`。网站 `/dashboard` 的“API接口文档”提供简短填写规则和一条可复制的创建命令；分类下拉框包含全部63个合法值，选择后自动填入命令，与API校验共用生成的分类注册表。运行时无需访问归档仓库。
任务列表还支持`q`、`hotspot_id`和`period`筛选参数。

## 任务状态台

`GET /dashboard`提供表格化任务状态页面。页面外壳不包含业务数据；输入独立状态台密码
登录后，浏览器才会调用受保护的任务列表接口。服务端只保存
`CCN_DASHBOARD_PASSWORD_HASH`中的PBKDF2-SHA256密码哈希，浏览器只接收HttpOnly、
SameSite=Strict的限时会话Cookie，不保存密码。机器调用仍使用原有Bearer API Key。

页面内的“API 接口文档”页签无需登录即可查看，提供主要接口的PowerShell调用示例。
示例只使用`<API_KEY>`代号，使用者必须替换为实际密钥，
且不得把真实密钥提交到版本库或放入URL、截图和公开日志。

结果请求示例：

```json
{
  "outcome": "completed",
  "artifact_urls": [
    "https://github.com/MozhiJiawei/ccn-report/tree/main/开源软件分析/Example/20260805-example-source-understanding-codex",
    "https://media.githubusercontent.com/media/MozhiJiawei/ccn-report/refs/heads/main/开源软件分析/Example/20260805-example-source-understanding-codex/source_understanding_review.html?download=true",
    "https://github.com/MozhiJiawei/ccn-report/raw/refs/heads/main/开源软件分析/Example/20260805-example-source-understanding-codex/single_page_tech_report.pptx?download=1"
  ]
}
```

完成记录只提交`outcome`和`artifact_urls`。新记录的`artifact_urls`按顺序包含报告目录直达地址、HTML Git LFS实体地址和PPTX Git LFS下载地址；HTML使用`media.githubusercontent.com/media/...?...download=true`，供浏览器读取Blob并保留`.html`文件名；PPTX继续使用GitHub raw下载地址。不传仓库根地址、本地路径、临时预览地址、`summary`或`metadata`。状态台保留目录结果链接，并在下载地址存在时显示“下载报告”和“下载PPT”按钮。历史记录可少于三个URL，页面会隐藏缺失交付件的按钮。

服务端接受中文路径和 percent-encoded UTF-8 路径，并在校验后统一以可读的中文 IRI 形式计算幂等哈希和返回。数据库保留客户端提交时的原始 URL，不迁移或重写历史记录；幂等检查会同时兼容历史请求哈希和规范化哈希。ASCII 保留字符的转义保持不变，因此编码形式不同但语义相同的中文报告 URL 会命中同一幂等请求。

只有报告完成归档、通过仓库门禁、Pull Request 已实际合入默认分支且远端路径确认存在后，才能提交 `completed` 结果。

## 测试

```powershell
python -m pip install -e ".\loops\ccn-brief-report\task_service[test]"
python -m pytest loops/ccn-brief-report/task_service/tests
```

真实PostgreSQL和Redis验证使用`deploy/resource-server/compose.local.yml`。


## 批量创建与安全重试

```json
{"tasks":[{"task_id":"sample-001","content":"技术线索正文","url":"https://example.com/article","hotspot_id":"topic-001","period":"202609","category":null}]}
```

向 `POST /api/v1/tasks/batch` 提交上述 JSON，使用原有鉴权，可附 `Idempotency-Key`。限制 1–200 条和 10 MiB（10,485,760 个实际请求字节，含中文 UTF-8 编码），应用和 CCN 网关均执行；超过体积返回 413。分类使用 `category`，与单条完全相同。

存在新增返回 201，全部已存在且相同返回 200；响应为 `{"status":"success","data":{"requested":1,"created":1,"existing":0,"items":[{"index":0,"task_id":"sample-001","disposition":"created"}]}}`。输入顺序不变，不返回正文。批内重复 ID、非法字段返回带输入位置的 422；任一已有 ID 原始创建载荷不同返回含 ID/index 的 409。失败整批零新增，已有任务状态和结果不重置。

同 key、相同规范化有序请求重放原成功响应及状态码；同 key 不同载荷或顺序返回 409。无 key 按 task_id 安全去重。批量 key 独立于单条/结果 key。`batch_creations` 无自动 TTL，不随任务删除；任务删除后原 key 仍重放，不重新创建。并发竞争回滚重查，持续竞争返回 `concurrent_creation` 409 和 `Retry-After: 1`，可原样重试。每批仅计一次写请求限流。

发布时先运行 `alembic upgrade head`，包含分类迁移及 `0003_batch_creation`，再启动新服务；同步发布 CCN 网关体积配置。回退应用可保留新增表及审计列，避免丢失幂等记录。

## 当前页批量下载

筛选后勾选当前页任务，或点击“全选当前页”，最多 200 个；不会选择其他页。翻页、每页条数变化、刷新、应用/清除筛选及退出会清空选择。选择 HTML、PPTX 或默认“全部”后点击“批量下载”。

浏览器先核对任务详情，再直接从目标 GitHub 仓库获取 completed 报告，不经过服务端中转。支持既定 main 分支 media 地址和 GitHub raw 地址映射；不下载目录页面，不泛化开放 CSP。不支持的地址、历史缺链接、非完成任务和已删除任务均有明细。

并发 3、每次超时 60 秒；网络瞬时错误、429、5xx 最多自动重试两次，遵守 Retry-After。单文件 50 MiB，累计输入 200 MiB（重试收到的字节也计入），缺失 Content-Length 仍执行；超限请缩小选择。ZIP 中使用 `<task_id>/<原文件名>`，保留中文，并附 `manifest.json`。部分失败仍导出成功项；全失败不导出空包。“重试失败项”重新核对失败目标并生成补充 ZIP，不重新下载已成功文件。

取消立即停止请求且不生成 ZIP；运行时禁止重复启动及删除本批任务。成功表示“已生成 ZIP 并触发浏览器保存”，不表示已写入用户磁盘。完成和取消释放下载缓存，文件仍消耗浏览器本地内存；关闭页面不会继续下载。

ZIP 库使用本地托管 fflate 0.8.2 UMD，来源 `https://cdn.jsdelivr.net/npm/fflate@0.8.2/umd/index.js`，许可证随 `app/web/fflate-LICENSE.txt` 保存。Docker 与源码发布均包含整个 app 目录，无运行时 CDN 依赖。

额外测试：`node --test loops/ccn-brief-report/task_service/tests/downloads.test.mjs`。真实 PostgreSQL 测试设置 `CCN_TEST_POSTGRES_URL` 指向专用测试实例后运行服务 pytest；测试创建隔离 schema 并在结束时清理，不使用生产数据库。

fflate 0.8.2 UMD SHA-256：`c3b34f2e9f5e74d4d7d64e01cac7a0c01954c6c406414d42185c7b53d6875ddf`。
