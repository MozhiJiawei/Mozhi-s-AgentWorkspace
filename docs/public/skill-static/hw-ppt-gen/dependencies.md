# 依赖说明

使用这个 skill 前，请先让 Agent 跑依赖检查。依赖状态以子仓根目录的 `verify_dependencies.py` 输出为准；文档只说明它会检查什么。

## 让 Agent 先做什么

你可以直接这样说：

```text
我要使用 huawei-pptx-generator，请先检查 PPT 生成依赖；如果 Node、Node 包或 PPTX 渲染环境缺失，请帮我处理到可用。
```

## 检查命令

在 workspace 根目录运行：

```powershell
python skills/hw-ppt-gen/verify_dependencies.py
```

## 它会检查什么

| 类型 | 说明 |
| --- | --- |
| Node.js | `node`、`npm` 是否可用 |
| Node 包 | `pptxgenjs`、`jszip`、`roughjs`、`sharp` 是否已安装并能加载 |
| PPTX 渲染 | Windows 使用 Microsoft PowerPoint COM；macOS / Linux 依赖 LibreOffice 和 Poppler |

## 判断标准

检查通过后再生成正式 PPT。若失败，不要先绕过导出或视觉 QA；请让 Agent 根据失败项安装依赖，直到检查脚本通过。
