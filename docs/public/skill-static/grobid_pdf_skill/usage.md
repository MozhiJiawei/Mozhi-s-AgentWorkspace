# 使用方式

这个 skill 适合在“论文阅读、技术 PDF 解析、后续 PPT 或报告生成”之前调用。你可以直接把 PDF 路径交给 Agent，让它生成结构化 XML 包，而不是让 Agent 直接从 PDF 页面里硬读内容。

## 典型 Prompt

- `请解析这篇论文 PDF，输出结构化 XML 和图表图片索引，用于后续分析。`
- `请把这篇论文 PDF 的正文、引用、参考文献、图和表整理成 agent 可消费的结构化结果。`
- `请先把这个技术 PDF 转成 XML 包，保留最终 XML 路径、图片目录和校验结果。`

## 推荐流程

1. 确认 PDF 是 born-digital 还是扫描版。
2. 确认 GROBID 服务可用，默认地址是 `http://localhost:8070`。
3. 将输出目录放在主工作区 `.tmp/pdf_xml/<paper-name>/` 下。
4. 运行混合解析流水线。
5. 检查最终 XML、图片目录、归档 zip 和校验状态。

## 脚本入口

```powershell
python scripts/run_hybrid_pipeline.py `
  --pdf path/to/paper.pdf `
  --out .tmp/pdf_xml/<paper-name> `
  --grobid-url http://localhost:8070 `
  --docling-device auto
```

扫描版 PDF 才加：

```powershell
--ocr
```

确认 CUDA PyTorch 可用后才指定：

```powershell
--docling-device cuda
```

## 交付汇报

Agent 完成后应汇报：

- 最终 XML 路径。
- 最终图片目录和图片数量。
- 中间结果归档路径。
- 校验状态，包括缺失图片引用、未索引图片、body-linked 图片数量。

## 依赖检查

```powershell
python verify_dependencies.py
```

只检查本地 Python 依赖、不检查 GROBID 服务时：

```powershell
python verify_dependencies.py --skip-services
```
