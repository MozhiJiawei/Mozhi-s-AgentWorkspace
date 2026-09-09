from __future__ import annotations

from enum import Enum

from .category_data import CATEGORY_DETAILS

CATEGORY_VALUES = frozenset(item['value'] for item in CATEGORY_DETAILS)
Category = Enum('Category', {f'C{i:02d}': item['value'] for i, item in enumerate(CATEGORY_DETAILS, 1)}, type=str)


def normalize_category(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or value not in CATEGORY_VALUES:
        raise ValueError('category 必须为已注册的完整中文分类路径或 null')
    return value


def category_path_error(parent: str, category: object) -> str | None:
    selected = normalize_category(category)
    if selected is None:
        return None
    if parent not in CATEGORY_VALUES:
        return '报告父目录不是已注册分类'
    if parent == selected or ('/' not in selected and parent.startswith(selected+'/')):
        return None
    return f'报告归档分类 {parent} 不满足指定分类 {selected}'
