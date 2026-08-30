# mcp-manual：知识手册构建 MCP

把本仓库"知识手册"的**构建方式**抽成可调用的 MCP，用于**依据提供的材料，构建有逻辑、有体系的知识手册**。与 `mcp/exam`（考试系统 MCP）共用同一套标准结构（Host / Client / Server）。

> 约定：MCP Server 提供**确定性逻辑**（骨架 + 规约 + 校验）。"写正文"由 Host 侧 LLM 负责——先用 `chapter_outline` 把材料编排成有主线的章节骨架，再按骨架逐节写内容，最后用 `validate_anchors` / `check_graph_sync` 校验锚点与图谱一致性。这样构建出的手册**结构有逻辑、锚点不死链、图谱同步**。

## 目录

```
mcp/manual/
├── manual_engine.py   # 纯逻辑内核：手册规范 / 锚点 slug 生成校验 / 图谱同步 / 章节大纲骨架
├── server.py          # MCP Server：FastMCP 暴露 5 个工具（stdio）
├── client_test.py     # 标准 Client 流程演示
├── requirements.txt   # 依赖：mcp<2
```

## 安装与冒烟测试

```bash
cd mcp/manual
py -3 -m pip install -r requirements.txt
py -3 client_test.py     # 标准流程：握手→列工具→调用 manual_spec/slugify/outline/check_graph_sync
```

## 提供的工具

| 工具 | 入参 | 返回 | 作用 |
|---|---|---|---|
| `manual_spec` | — | `{chapters, structure, thread_style, explanatory_chain, synchronize, anchor_rule}` | 本库手册构建规范（章节数/占比/结构约定/主线句式/讲解链/图谱同步/锚点规则） |
| `slugify` | `title: str` | 字符串 | markdown 标题 → VitePress 锚点 slug |
| `validate_anchors` | `headings_json` | `{valid, items[], duplicates, errors}` | 生成并校验一组标题的锚点（防止重复） |
| `check_graph_sync` | `chapter_anchors_json, graph_nodes_json` | `{ok, missing_in_graph, orphan_anchors}` | 标题锚点 ↔ 图谱节点 anchor 的一致性（防死链） |
| `chapter_outline` | `material, chapter_no, chapter_title` | `{chapter_no, chapter_title, main_thread, sections[], style_checks}` | 把零散材料编排成"有主线 + 小节树 + 每节讲解链 + 考点提示"的章节骨架 |

## 用法示例（Python client）

```python
res = await session.call_tool("chapter_outline", {
    "material": "（教材/笔记等零散材料文本，可含 markdown 标题）",
    "chapter_no": 4, "chapter_title": "智能体技术基础",
})
# 得到 main_thread + sections（每节含 level/title/slug/guide/must）
```

随后按 sections 逐节写正文 → `validate_anchors` 校验锚点 → `check_graph_sync` 联动图谱。

## 接入 Host（opencode 为例）

在 `.opencode/opencode.json` 里与 `exam` 一起注册（见该文件）。重启 opencode 后，模型可用 `manual_spec` / `chapter_outline` / `validate_anchors` / `check_graph_sync` 来构建/校验手册，配合 `.opencode/skills/exam-builder` 或 manual-refactor 流程产出"有逻辑有体系"的章节。

## 与本库其它部分的分工

- `docs/ch0X.md`：知识手册正文（内容源）。**改动章节标题必须同步** `docs/public/graph-data.json` 对应节点 `anchor` 与 `docs/public/terms.json` 的 `href`，否则图谱/术语悬浮死链——这正是 `validate_anchors` / `check_graph_sync` 要防的。
- `mcp/exam`：考试系统 MCP（题库/组卷/判分/错题本）。
- `.opencode/skills/exam-builder`：出题提示词模板（供 LLM 生成题目候选，再交 `exam` 的 `validate_questions` 校验）。
