# Docker 文档站部署

本文档说明如何用 Docker / Compose 启动在线文档站。

## 架构

镜像只提供运行环境：

- Node.js / VitePress
- Python
- Nginx
- 文档同步与构建入口

仓库内容通过 volume 挂载到容器内：

```text
./ -> /workspace:ro
```

容器启动时会：

1. 将 `/workspace` 复制到容器临时构建目录。
2. 运行 `python3 scripts/sync_skill_docs.py`，真实加载各子仓 `docs.manifest.yml` 声明的文档。
3. 运行 VitePress 构建静态 HTML。
4. 用 Nginx 从 `/site` 提供访问。

因此，文档内容更新后只需要在宿主机执行：

```bash
git pull
git submodule update --init --recursive
docker compose -f compose.docs.yml restart docs
```

不需要重新构建镜像，除非 Dockerfile、Node 依赖或站点运行环境发生变化。

## 本地启动

```powershell
.\scripts\docs_compose.ps1 -Port 8080
```

或直接运行：

```powershell
docker compose -f compose.docs.yml up --build
```

访问：

```text
http://127.0.0.1:8080/
```

健康检查：

```text
http://127.0.0.1:8080/healthz
```
