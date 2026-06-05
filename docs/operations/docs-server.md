# 文档服务器

文档服务器通过一个 VitePress 站点发布工作区文档和已注册 skill 文档。

## 本地开发

```powershell
npm run docs:dev
```

打开：

```text
http://127.0.0.1:5173/
```

## 静态构建

```powershell
npm run docs:build
```

构建命令会先刷新 skill 文档集成信息，再生成 VitePress 静态站点。

## 预览构建结果

```powershell
npm run docs:preview
```

## Skill 文档集成

每个已注册 skill 都暴露一个 `docs.manifest.yml`。工作区读取这些 manifest 来生成 Skills 和侧边栏。

当前 bootstrap 实现会在构建前准备 VitePress 可见的 skill 页面。无论具体实现如何演进，架构目标保持不变：skill 子仓仍然是自身文档的权威来源。

## Docker 部署

Docker 和 Compose 部署说明见 [Docker 部署](/deployment-docker)。
