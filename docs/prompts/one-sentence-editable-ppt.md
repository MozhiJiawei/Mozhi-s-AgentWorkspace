# 一句话生成一页可编辑 PPT

```text
基于以下一句话和 HTML 报告，制作 1 页中文、16:9、可编辑的 PPTX。

一句话：{{ONE_SENTENCE_BRIEF}}
HTML 报告：{{SOURCE_HTML_PATH}}
输出目录：{{OUTPUT_DIR}}

要求：
- 一页讲清“问题—方案—效果”，方案是视觉中心；效果数字注明比较基线和实验条件。
- 优先使用报告中的 2–3 幅论文原图；密集多子图只裁切与结论直接相关的部分，并保证坐标、图例和标签可读。
- 除论文原图外，标题、文字、数字、箭头和结构图均使用可编辑的 PowerPoint 元素；所有文本框启用 PowerPoint 自动换行（`wrap=square`），不用手工换行或 `fit/shrink` 伪装。
- 使用华为风格：微软雅黑；白/浅灰底；朱红 #C7000B 为主色，蓝 #1E6FD9、黄 #F2C94C 为辅助色；简洁克制，不使用渐变、装饰插画和卡片墙。
- 同时生成同版式 HTML 和 PPTX，分别渲染检查，修复裁切、重叠、换行、黑边和不可读原图。
- 完成后只启动 1 个独立视觉 QA agent；若失败，修正后让同一个 agent 复检。

交付：index.html、editable.pptx、HTML/PPTX 渲染图和 visual-qa.md。
```
