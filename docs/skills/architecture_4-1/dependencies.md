# 依赖说明

使用这个 skill 前，请先让 Agent 跑依赖检查。依赖状态以子仓根目录的 `verify_dependencies.py` 输出为准；文档只说明它会检查什么。

## 让 Agent 先做什么

你可以直接这样说：

```text
我要使用 [beta] generate-3plus1-diagrams，请先检查它的依赖；如果缺少 Python 包、浏览器或 draw.io 运行环境，请帮我处理到可用。
```

## 检查命令

在 workspace 根目录运行：

```powershell
python skills/architecture_4-1/verify_dependencies.py
```

如果需要确认远程 diagrams.net embed 运行环境也可访问：

```powershell
python skills/architecture_4-1/verify_dependencies.py --check-network
```

## 它会检查什么

| 类型 | 说明 |
| --- | --- |
| Python 包 | `pillow`、`playwright` |
| 浏览器 | Playwright Chromium 能否启动 |
| draw.io 运行环境 | 优先使用本地 VS Code draw.io webapp；必要时回退到 diagrams.net embed |

## 判断标准

看到 `PASS` 表示对应依赖可用；看到 `FAIL` 时，不要继续生成架构图，先让 Agent 根据错误信息安装或修复依赖。
