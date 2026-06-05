# GROBID + Docling PDF 解析

`grobid-docling-pdf` 用来把论文或技术 PDF 解析成一个下游 Agent 可消费的 XML 包：GROBID 负责学术文本结构，Docling 负责图表图片真值，最终合并成一个干净的 TEI/XML 交付目录。

## 架构概览

这个 skill 的架构是一条固定流水线：

| 阶段 | 脚本 | 职责 |
| --- | --- | --- |
| 文本结构解析 | `scripts/grobid_parse_pdf.py` | 调用 GROBID，提取标题、摘要、正文、引用和参考文献结构。 |
| 视觉内容导出 | `scripts/docling_export.py` | 调用 Docling，导出 PDF 中的图片、表格和 Docling JSON。 |
| 结果合并 | `scripts/merge_docling_into_grobid_tei.py` | 将 Docling 图片索引写入 GROBID TEI，移除不可靠的 GROBID 图表记录。 |
| 包校验 | `scripts/validate_hybrid_outputs.py` | 检查 XML 中引用的图片是否存在、最终图片是否全部被索引。 |
| 编排与归档 | `scripts/run_hybrid_pipeline.py` | 串联以上阶段，归档中间结果，只保留最终 XML 包。 |

## 数据流

```text
PDF
  -> GROBID TEI
  -> Docling JSON + images
  -> merged TEI/XML + final/images
  -> validation report
  -> intermediate_parse_results.zip
```

## 最终目录

```text
.tmp/pdf_xml/<paper-name>/
|-- final/
|   |-- <paper-name>.xml
|   `-- images/
|       |-- picture_*.png
|       `-- table_*.png
`-- <paper-name>.intermediate_parse_results.zip
```

## 设计边界

- born-digital 论文默认不开 OCR；扫描版 PDF 才启用 `--ocr`。
- 最终 XML 只以 Docling 导出的图表图片作为视觉真值。
- 中间 GROBID / Docling / merge / validation 文件默认打包进 zip 后移除。
- 校验失败意味着 XML 包不完整，不能作为成功交付。

## 校验关注点

`validate_hybrid_outputs.py` 会检查最终 XML 包是否完整，重点包括：

- XML 中引用的图片是否都存在。
- 图片目录中的最终图片是否都被 XML 索引。
- 正文中的图表引用是否能连到 Docling 图片。
- 最终 XML 中是否残留不可靠的 GROBID 图表记录。

通过校验后，`final/<paper-name>.xml` 才应作为下游 Agent 的正式输入。
