# 依赖说明

使用这个 skill 前，请先让 Agent 跑依赖检查。依赖状态以子仓根目录的 `verify_dependencies.py` 输出为准；文档只说明它会检查什么。

## 让 Agent 先做什么

你可以直接这样说：

```text
我要使用 grobid-docling-pdf，请先检查 PDF 解析依赖；如果 GROBID 服务或 Python 包没有就绪，请帮我处理到可用。
```

## 检查命令

只检查本地 Python 依赖：

```powershell
python skills/grobid_pdf_skill/verify_dependencies.py --skip-services
```

连同 GROBID 服务一起检查：

```powershell
python skills/grobid_pdf_skill/verify_dependencies.py --grobid-url http://localhost:8070
```

## 它会检查什么

| 类型 | 说明 |
| --- | --- |
| Python 包 | `docling`、`lxml`、`torch` |
| GROBID 服务 | 默认检查 `http://localhost:8070/api/isalive` |
| 可选硬件 | CUDA 是否可用；不可用时可以走 CPU |

## 判断标准

本地包检查通过后，skill 可以处理结构化解析流程；如果任务需要 GROBID 学术结构抽取，必须让服务检查也通过。
