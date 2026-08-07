# 文档发布

文档站已经并入资料服务器统一部署，部署源码位于`deploy/resource-server/`。发布采用“本地按Git索引打包、SSH上传、远端原子替换”的方式，服务器不直接维护源码。

## 默认发布命令

```powershell
python deploy/resource-server/scripts/release.py deploy --component docs
```

默认SSH目标为`root@39.105.78.135`，统一部署目录为：

```text
/opt/mozhi-agent-workspace-services
```

发布包写入本地`.tmp/releases/`，只包含Git已跟踪文件以及展开后的skill子仓内容。工作区不干净时发布会拒绝执行；调试打包可以显式使用`--allow-dirty`，但未跟踪文件仍不会进入发布包。

## 只打包

```powershell
python deploy/resource-server/scripts/release.py package
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
