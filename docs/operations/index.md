# 运维

运维页面说明如何运行、发布和维护工作区基础设施。

## 常见运维任务

| 任务 | 页面 |
| --- | --- |
| 运行或构建文档站 | [文档服务器](./docs-server) |
| 发布文档站到远端 | [文档发布](./release-docs) |
| 初始化或更新 skill submodules | [Submodules](./submodules) |
| 运行仓库检查 | [Pre-Commit Gates](./pre-commit-gates) |
| 使用 Docker 部署 | [Docker 部署](/deployment-docker) |

## 运维原则

主仓应该让工作区维护变得可预测。每个重复操作都应有一个清晰入口；skill 专属的运维细节应留在对应 skill 子仓。
