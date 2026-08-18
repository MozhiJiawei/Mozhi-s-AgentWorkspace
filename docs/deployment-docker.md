# Docker 资料服务器部署

资料服务器的Docker配置统一位于`deploy/resource-server/`，同时管理文档站、统一网关和CCN任务接口。

## 本地文档站

```powershell
.\deploy\resource-server\scripts\docs-local.ps1 -Port 8080
```

打开`http://127.0.0.1:8080/`，健康检查地址为`http://127.0.0.1:8080/healthz`。

## 本地CCN接口

```powershell
docker compose -f deploy/resource-server/compose.local.yml up --build -d postgres redis
docker compose -f deploy/resource-server/compose.local.yml build ccn-api
docker compose -f deploy/resource-server/compose.local.yml run --rm ccn-api alembic upgrade head
docker compose -f deploy/resource-server/compose.local.yml up -d ccn-api
```

默认地址为`http://127.0.0.1:18000`。本地Compose中的测试密钥不得用于服务器。

## 生产部署

```powershell
python deploy/resource-server/scripts/release.py deploy --component all
```

也可以只发布一个组件：

```powershell
python deploy/resource-server/scripts/release.py deploy --component docs
python deploy/resource-server/scripts/release.py deploy --component ccn
python deploy/resource-server/scripts/release.py deploy --component edge
python deploy/resource-server/scripts/release.py deploy-edge-source
```

生产部署、密钥、备份与恢复说明见`deploy/resource-server/README.md`。

`deploy-edge-source`只发布统一网关的 Compose 与 edge 文件，可在工作区存在其他未提交业务改动时使用；命令仍要求所有 edge 发布文件已经提交。InferenceViz 由其自身仓库发布并加入`mozhi-agent-services-edge`，统一网关上游为`inferenceviz-web:8080`。
