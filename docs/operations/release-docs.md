# 文档发布

文档站已经并入资料服务器统一部署，部署源码位于`deploy/resource-server/`。发布在本地按 Git 跟踪清单读取工作区文件并打包，通过 SSH 上传后替换远端部署目录；服务器不直接维护源码。

以下命令均从工作区根目录运行。`<run-id>` 使用当前任务已经分配的工作根目录名称。

## 默认发布命令

```powershell
python deploy/resource-server/scripts/release.py deploy --component docs --output-dir .tmp/runs/<run-id>/release
```

默认SSH目标为`root@39.105.78.135`，统一部署目录为：

```text
/opt/mozhi-agent-workspace-services
```

发布包写入本次任务的 `.tmp/runs/<run-id>/release/`。默认要求工作区干净，收录主仓和各 submodule 的 Git 已跟踪文件，并展开子仓内容。

调试打包时，`--allow-dirty` 必须放在子命令之前：

```powershell
python deploy/resource-server/scripts/release.py --allow-dirty package --output-dir .tmp/runs/<run-id>/release
```

该选项会跳过干净工作区检查，并额外收录主仓中未被 Git 忽略的未跟踪文件；子仓仍只收录已跟踪文件。已跟踪文件读取的是当前工作区内容，包括未提交修改。打包前应核对收录内容，不要把凭据放入发布包。

## 只打包

```powershell
python deploy/resource-server/scripts/release.py package --output-dir .tmp/runs/<run-id>/release
```

## 发布后验证

文档正式入口：

```text
https://docs.haohaoxiaoyu.top/
```

旧的`http://docs.haohaoxiaoyu.top:8888/*`只保留308重定向，不再直接提供正文。

远端检查：

```bash
docker compose -f /opt/mozhi-agent-workspace-services/deploy/resource-server/compose.production.yml ps
curl -fsS https://docs.haohaoxiaoyu.top/ >/dev/null
curl -I http://docs.haohaoxiaoyu.top:8888/
```

完整的统一网关、CCN接口、备份和回滚操作见`deploy/resource-server/README.md`。
