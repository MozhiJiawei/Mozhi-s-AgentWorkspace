# 依赖说明

使用这个 skill 前，请先让 Agent 跑依赖检查。依赖状态以子仓根目录的 `verify_dependencies.py` 输出为准；文档只说明它会检查什么。

## 让 Agent 先做什么

你可以直接这样说：

```text
我要使用 ppt-deep-search，请先检查它的外部依赖；如果 Python 版本不满足，请帮我处理到可用。
```

## 检查命令

在 workspace 根目录运行：

```powershell
python skills/ppt-deep-search/verify_dependencies.py
```

## 它会检查什么

| 类型 | 说明 |
| --- | --- |
| Python 版本 | Python 3.9+ |
| 外部网络 | 默认不需要；只有任务本身要求补充网页资料时才需要联网 |

## 判断标准

看到 Python 版本检查通过后即可进入 PPT 深度研究。如果后续运行中出现仓库文件缺失、validator self-test 失败等问题，那不是用户依赖配置问题，应让 Agent 检查 submodule 是否完整或仓库内容是否损坏。
