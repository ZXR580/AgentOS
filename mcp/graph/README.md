# mcp-graph：知识图谱 MCP

把 `docs/public/graph-data.json`（知识网络图数据）暴露成**可查询的 MCP 工具**，与 `mcp/exam`、`mcp/manual` 平级，让 AI Host（opencode 等）能查询/扩写知识图谱——呼应 MemoryGraphExplorer 的"AI 可查询图谱"设计。

> 约定：MCP Server 提供**确定性查询**。浏览器端可视化由 `docs/.vitepress/theme/KnowledgeGraph.vue`（echarts）负责；本 MCP 面向 AI，让模型能 `read_graph` / `search_nodes` / `open_node` / `get_relations`，例如"查一下 RAG 关联了哪些知识点"。

## 目录
```
mcp/graph/
├── graph_engine.py   # 纯逻辑内核：读 graph-data.json，提供查询方法
├── server.py         # MCP Server：FastMCP 暴露 5 个工具（stdio）
├── client_test.py    # 标准 Client 流程演示
└── requirements.txt  # 依赖：mcp<2
```

## 安装与冒烟测试
```bash
cd mcp/graph
py -3 -m pip install -r requirements.txt
py -3 client_test.py     # 握手→列工具→read_graph/stats/search/node/relations
```

## 提供的工具
| 工具 | 入参 | 返回 |
|---|---|---|
| `read_graph` | — | `{nodes:[{id,name,module,chapter,anchor,desc}], edges:[{source,target,relation}]}` |
| `search_nodes` | `query` | 匹配节点数组（按 name/desc/id 模糊） |
| `open_node` | `node_id` | 单节点详情 + `relations` 列表 |
| `get_relations` | `node_id` | 该节点一跳关系 `[{node,name,module,relation,chapter,anchor}]` |
| `graph_stats` | — | `{nodes, edges, modules:{module:count}}` |
| `add_node` | `node_json` | 新增节点并落盘（id/name/module 必填，module 5 类） |
| `add_edge` | `edge_json` | 新增关系边并落盘（source/target 须已存在） |
| `update_anchor` | `node_id, anchor` | 更新节点锚点（配合手册标题改动同步图谱） |
| `related_questions` | `node_id, count=10` | **串联**：查该节点关联 → 按关联 module 从模拟题库抽题 → 用 exam 校验，返回 `{node, relations, modules_used, count, valid, errors, questions}` |

## 数据来源
- `docs/public/graph-data.json`：节点 `{id,name,module,chapter,anchor,desc}`，边 `{source,target,relation}`。
- `graph_engine` 默认定位到本仓库 `docs/public/graph-data.json`；若图谱数据更新（改标题需同步 anchor），此 MCP 自动读到最新内容。

## 接入 Host（opencode 为例）
在 `.opencode/opencode.json` 的 `mcp` 里加：
```json
"graph": { "type": "local", "command": ["py", "-3", "mcp/graph/server.py"], "enabled": true }
```
重启 opencode 后，模型可用 `search_nodes("RAG")`、`get_relations("rag")` 等查询知识图谱。

## 与其它 MCP 的分工
- `mcp/exam`：考试系统（题库/组卷/判分/错题本）
- `mcp/manual`：知识手册构建（大纲骨架/锚点校验/图谱同步）
- `mcp/graph`：知识图谱**查询**（读图谱/搜索/节点详情/关系）
- 三者配合：manual 构建手册并同步图谱 → graph 供 AI 查询图谱 → exam 配套出题。
