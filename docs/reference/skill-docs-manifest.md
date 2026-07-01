# Skill 文档 Manifest

`docs/skill-docs.yml` 是 skill 文档集成的唯一登记入口。它描述主仓如何把各 skill 子仓的文档同步到 VitePress 文档站。

## 顶层字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schema_version` | integer | manifest schema 版本。当前为 `1`。 |
| `description` | string | manifest 用途说明。 |
| `skills` | mapping | 以 skill 名称为 key 的文档发布登记表。 |

## Skill 条目字段

每个 `skills.<name>` 条目应包含：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `path` | string | skill 子仓在主仓中的路径，例如 `skills/ppt-deep-search`。 |
| `mount` | string | 文档同步到主仓 docs 下的位置，例如 `docs/skills/ppt-deep-search`。 |
| `status` | string | 文档接入状态。当前已接入条目使用 `bootstrap`。 |
| `publish.mode` | string | 发布模式。当前使用 `subrepo-manifest`。 |
| `publish.entry` | string | 发布后的入口文档路径。 |
| `publish.skill_manifest` | string | skill 子仓内的文档 manifest 路径，通常为 `docs.manifest.yml`。 |
| `docs_review.source_fingerprint` | string | 文档来源复核指纹。 |
| `docs_review.reviewed_at` | string | 复核日期，格式为 `YYYY-MM-DD`。 |
| `docs_review.reviewed_by` | string | 复核人或复核 agent。 |
| `docs_review.note` | string | 复核说明。 |

## 发布模式

当前稳定发布模式为 `subrepo-manifest`。

在该模式下，主仓构建文档前会读取 skill 子仓的 `docs.manifest.yml`，并由 `scripts/sync_skill_docs.py` 将子仓文档同步到 `mount` 指定目录。

同步后的 `docs/skills/` 与 `docs/public/skill-static/` 是生成产物，不应作为主仓手写源码维护。

## 指纹规则

`docs_review.source_fingerprint` 用来标记 skill 文档来源已被复核。相关文档来源变化后，应重新运行文档同步或复核流程，并刷新指纹。

发布站点的远端一致性由 `publish-state.json` 校验。该状态文件是构建产物，不应写回 `docs/public/material-quality/` 作为源码。

## 示例

```yaml
skills:
  ppt-deep-search:
    path: skills/ppt-deep-search
    mount: docs/skills/ppt-deep-search
    status: bootstrap
    publish:
      mode: subrepo-manifest
      entry: docs/skills/ppt-deep-search/index.md
      skill_manifest: docs.manifest.yml
    docs_review:
      source_fingerprint: sha256:...
      reviewed_at: "2026-06-04"
      reviewed_by: agent
      note: 已接入子仓 docs.manifest.yml，构建时从子仓同步文档。
```
