# 依赖说明

使用这个 skill 前，请先让 Agent 跑依赖检查。依赖状态以子仓根目录的 `verify_dependencies.py` 输出为准；文档只说明它会检查什么。

## 让 Agent 先做什么

你可以直接这样说：

```text
我要使用 ppt-deep-search，请先检查它的依赖；如果校验器或网页证据包工具缺失，请帮我处理到可用。
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
| 仓库文件 | 深度研究、HTML review、web evidence 相关脚本和参考文档是否存在 |
| 自检 | `ppt_content_brief`、HTML review、web evidence package 等校验器是否能通过 self-test |
| 外部服务 | 默认不需要外部服务；只有任务本身要求补充网页资料时才需要联网 |

## 判断标准

看到所有 `[OK]` 后再进入 PPT 深度研究。若某个 self-test 失败，请先让 Agent 修复校验器或缺失文件，再继续研究任务。
