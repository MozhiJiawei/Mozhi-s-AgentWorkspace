# 资料服务器统一部署

本目录是资料服务器运行与恢复的唯一部署源码。业务代码仍由各自目录维护；CCN API 位于
`loops/ccn-brief-report/task_service/`。

## 服务入口

- `https://docs.haohaoxiaoyu.top`：文档站。
- `https://ccn-api.haohaoxiaoyu.top`：CCN任务接口。
- `https://ccn-api.haohaoxiaoyu.top/dashboard`：任务状态台，以及无需登录即可查看的API接口文档页签；任务数据仍受Bearer Key保护。
- `https://api.haohaoxiaoyu.top`：Red Flower Garden API。
- 80端口只负责HTTPS跳转或拒绝明文API。
- 8888端口只将旧文档地址308跳转到标准HTTPS地址。

## 本地验证

```powershell
.\deploy\resource-server\scripts\docs-local.ps1
docker compose -f deploy/resource-server/compose.local.yml up --build postgres redis ccn-api
docker compose -f deploy/resource-server/compose.local.yml run --rm ccn-api alembic upgrade head
```

本地API地址为`http://127.0.0.1:18000`，测试密钥只定义在本地Compose中，不得用于服务器。

## 打包与部署

```powershell
python deploy/resource-server/scripts/release.py package
python deploy/resource-server/scripts/release.py deploy --component all
python deploy/resource-server/scripts/release.py deploy --component docs
python deploy/resource-server/scripts/release.py deploy --component ccn
python deploy/resource-server/scripts/release.py deploy --component edge
python deploy/resource-server/scripts/release.py deploy-ccn-source
```

`deploy-ccn-source`只同步`task_service`源码并重启现有CCN容器，不构建镜像、不重建容器。
首次从镜像内源码切换到只读bind mount时，显式追加`--bootstrap-mount`；该首次切换会复用现有镜像重建一次容器，之后不得在普通源码发布中使用该参数。

远端无法访问镜像仓库时，可先用`docker load`预载Compose所需镜像，再以
`SKIP_IMAGE_BUILD=true`运行`install.sh`。安装脚本会逐一确认镜像存在，缺少
任何镜像都会在接管旧容器前失败。

默认SSH目标为`root@39.105.78.135`，远端安装目录为`/opt/mozhi-agent-workspace-services`。
部署包只收录Git已跟踪文件，因此正式发布前必须提交预期改动。

首次部署会将现有网关的FRP凭据迁移到`/etc/mozhi-agent-workspace/edge.env`，不会输出秘密值。
CCN密钥和数据库密码会写入`/etc/mozhi-agent-workspace/ccn-api.env`。

## 备份和恢复

```bash
bash /opt/mozhi-agent-workspace-services/deploy/resource-server/scripts/backup-ccn.sh
CONFIRM_RESTORE=restore bash /opt/mozhi-agent-workspace-services/deploy/resource-server/scripts/restore-ccn.sh /path/to/backup.dump
```

恢复操作会先生成安全备份、停止API、恢复PostgreSQL，再重新启动API。不要手工复制数据库数据目录。
