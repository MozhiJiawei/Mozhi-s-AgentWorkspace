# 文档发布

文档站的远端更新采用“本地打包、远端替换”的方式。

远端服务器不直接 `git pull`，也不在服务器上手工改文件。发布包由本地仓库生成，只包含 Git 已跟踪内容；`.tmp/`、`node_modules/`、本地缓存和其他 gitignored 文件不会进入发布包。

## 默认发布命令

在主仓根目录执行：

```powershell
python scripts\release_docs_package.py --remote root@39.105.78.135 --push-tag
```

这条命令会完成：

1. 检查主仓工作区是否干净。
2. 创建一个 `docs-YYYYMMDD-HHMMSS` 格式的发布 tag。
3. 推送 tag 到 GitHub。
4. 用主仓和各 skill 子仓的 `git ls-files` 生成干净源码包。
5. 上传源码包到远端 `/tmp/mozhi-agent-workspace-releases/`。
6. 清理并替换远端 `/opt/mozhi-agent-workspace-docs/`。
7. 重启 `mozhi-agent-workspace-docs` 文档容器。
8. 检查首页和静态 HTML 展示页是否可访问。

## 指定 tag

如果需要使用固定版本号：

```powershell
python scripts\release_docs_package.py --tag docs-20260605-001 --remote root@39.105.78.135 --push-tag
```

tag 已存在时，脚本会复用已有 tag。

## 只打包不部署

```powershell
python scripts\release_docs_package.py --tag docs-local-check --skip-tag
```

发布包会生成到：

```text
.tmp/releases/
```

## 发布包规则

发布包不是普通目录复制，而是由 Git 索引生成：

- 主仓只收录 `git ls-files` 返回的文件。
- 每个 skill 子仓只收录该子仓自己的 `git ls-files` 文件。
- submodule 指针文件不作为内容复制，子仓内容会展开进发布包。
- 发布包内会生成 `RELEASE.txt`，记录主仓 commit 和各子仓 commit。
- 发布包不携带 `.git/`，远端部署目录是发布结果目录，不再承担 Git clone 的职责。

## 远端目录

默认远端部署目录：

```text
/opt/mozhi-agent-workspace-docs
```

默认远端临时包目录：

```text
/tmp/mozhi-agent-workspace-releases
```

发布时会删除旧的 `/opt/mozhi-agent-workspace-docs`，再把新源码包解压后的目录移动到该位置。

## 发布前检查

发布前建议先跑：

```powershell
npm run docs:build
python scripts\pre_commit_gate.py
```

脚本本身会拒绝 dirty working tree；如果还有未提交改动，先提交再发布。

## 发布后验证

脚本会自动验证两个地址：

```text
http://127.0.0.1:8888/
http://127.0.0.1:8888/skill-static/ppt-deep-search/showcase/rtx-spark-agent-pc/review/source_understanding_review.htm
```

如果需要人工复查，可以登录服务器执行：

```bash
docker compose -f /opt/mozhi-agent-workspace-docs/compose.docs.yml ps
curl -I http://127.0.0.1:8888/
```
