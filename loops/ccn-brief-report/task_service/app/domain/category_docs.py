"""Compact category guidance using the API shared registry."""
from html import escape

from .category_data import CATEGORY_DETAILS


def category_documentation() -> str:
    options = ['<option value="">由 AI 自动分类</option>']
    options.extend(
        f'<option value="{escape(item["value"], quote=True)}">{escape(item["value"])}</option>'
        for item in CATEGORY_DETAILS
    )
    return """<div aria-labelledby="category-title">
<h4 id="category-title">category 填写规则（可选）</h4>
<p class="docs-copy">不传或填 <code>null</code>：AI 自动分类。指定时填写带编号的完整目录路径：<code>一级</code> 或 <code>一级/二级</code>。指定一级时 AI 在其内选择二级，综述可直接归一级；指定二级时严格归入该目录。不要填空字符串或自行编造名称（返回 422）。</p>
<label for="create-category">选择分类，自动填入下方命令</label>
<select id="create-category">""" + ''.join(options) + '</select></div>'
