# mcp：知识构建 / 考试 / 图谱 三合一 MCP

本目录是一套**标准 MCP（Model Context Protocol）**，供 AI Host（opencode、Claude Desktop、Cursor 等）通过 stdio 接入，协作完成"**构建知识手册 → 同步知识图谱 → 配套出题 → 评分/错题本**"的闭环。全部用 Python + `mcp<2`（FastMCP）实现，不含前端。

> 前端可视化（Mermaid / SectionGraph / Pillars / Compare / Flux / Layer / KnowledgeGraph / ExamPage 等）在 `docs/.vitepress/theme/`，**不在本目录**；若要新知识体系也带可视化，需另行拷贝 theme 组件与 VitePress 配置。

## 目录结构
```
mcp/
├── exam/     # 考试系统：让 AI 也能出题/组卷/判分/错题本
│   ├── server.py         # FastMCP，8 个工具
│   ├── exam_engine.py    # 内核（校验/组卷/判分/错题本/生成题）
│   ├── client_test.py    # 标准 Client 流程演示
│   └── README.md
├── graph/    # 知识图谱：查询 + 维护图谱，并可串联出题
│   ├── server.py         # FastMCP，9 个工具
│   ├── graph_engine.py   # 内核（读/搜/节点/关系/写/串联）
│   ├── client_test.py
│   └── README.md
└── manual/   # 手册构建：把零散材料编排成有逻辑有体系的章节骨架 + 锚点/图谱校验
    ├── server.py         # FastMCP，5 个工具
    ├── manual_engine.py  # 内核（规范/锚点/图谱同步/大纲骨架）
    ├── client_test.py
    └── README.md
```

## 安装依赖（三处共用）
```bash
# 用装有 pip 的 Python（本机为 py -3）
py -3 -m pip install "mcp>=1.0,<2"
# 可选：若用 exam 的 generate_questions 生成题目，需可访问一个 OpenAI 兼容 LLM（默认 Ollama）
```

## 三个 MCP 的作用与工具
| MCP | 作用 | 工具 |
|---|---|---|
| **manual** | 手册构建：给材料出"有主线 + 小节树 + 讲解链"的骨架；校验锚点与图谱同步 | `manual_spec`、`slugify`、`validate_anchors`、`check_graph_sync`、`chapter_outline` |
| **graph** | 知识图谱：读/搜/节点详情/关系，**写入维护**，**串联按关联出题** | `read_graph`、`search_nodes`、`open_node`、`get_relations`、`graph_stats`、`add_node`、`add_edge`、`update_anchor`、`related_questions` |
| **exam** | 考试：**生成题**（调 LLM）、组卷、判分、错题本 | `generate_questions`、`validate_questions`、`assemble_paper`、`grade_paper`、`wrong_add`、`wrong_list`、`wrong_remove`、`wrong_clear` |

## 如何串联（推荐闭环）
1. **manual**：`chapter_outline(material, ...)` 把零散材料编排成章节骨架（`> 本节回答`、讲解链、考点提示）→ 按骨架写正文。
2. **锚点/图谱**：写正文时用 `slugify`/`validate_anchors` 生成标题锚点；章节标题改动后用 `check_graph_sync` 核对，并用 `graph.update_anchor` 同步 `graph-data.json`。
3. **graph**：用 `add_node`/`add_edge` 把新知识点补进图谱；`search_nodes`/`open_node`/`get_relations` 供 AI 查询（"RAG 关联了哪些点"）。
4. **exam**：用 `generate_questions(material, module, chapter, ...)` 基于某章材料**生成题目**（内部调 LLM + 自动校验）；或用 `graph.related_questions(node_id)` 按知识点关联自动取材 → `exam.validate_questions` 校验 → `assemble_paper` 组卷。
5. 答题/训练：`grade_paper` 判分，`wrong_add/list` 维护错题本（持久化到 `mcp/<x>/wrong_store.json`）。

> 一句话链路：**manual 建结构 → graph 织关系 → exam 出题与评测**。

## 数据文件依赖与路径
- `mcp/exam` 读 `docs/public/quiz-mock.json`（出题编号续号、related_questions 取材）。
- `mcp/graph` 读写 `docs/public/graph-data.json`（图谱）。
- `mcp/manual` 不依赖数据文件（纯逻辑 + 规范）。
- 路径由各 `*_engine.py` 用 `Path(__file__).parent.parent.parent / "docs" / "public" / ...` 定位到**仓库根**；若 mcp 放在别处或目录不同，请改对应 `DEFAULT_*_PATH`。

## 移植到新 workspace 的步骤
1. 复制 `mcp/` 到新仓库根。
2. 确保新仓库有目标数据：`docs/public/graph-data.json`（图谱）与 `docs/public/quiz-mock.json`（题库）；否则改 `DEFAULT_*_PATH` 指到你的数据位置，或先用 `graph.add_node`/`add_edge` 建图、用 `exam.generate_questions` 建题。
3. 安装依赖 `py -3 -m pip install "mcp>=1.0,<2"`。
4. （可选）在 `.opencode/opencode.json` 注册 Host 接入（见下），重启 opencode。
5. 逐个跑 `py -3 client_test.py` 冒烟确认。

## 接入 opencode（Host）
在 `.opencode/opencode.json`：
```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "manual": { "type": "local", "command": ["py", "-3", "mcp/manual/server.py"], "enabled": true },
    "graph":  { "type": "local", "command": ["py", "-3", "mcp/graph/server.py"],  "enabled": true },
    "exam":   { "type": "local", "command": ["py", "-3", "mcp/exam/server.py"],   "enabled": true }
  }
}
```
改动配置后需**重启 opencode** 生效（配置只在启动时加载）。若默认 `python` 未装 mcp，用 `py -3` 或写到装 mcp 的解释器绝对路径。

## 生成题目需要 LLM
`exam.generate_questions` 内部调用一个 OpenAI 兼容 LLM。默认 Ollama（`http://localhost:11434/v1`、模型 `qwen2.5:7b`），可用环境变量覆盖：
```bash
set LLM_BASE=http://localhost:11434/v1
set LLM_MODEL=qwen2.5:7b
set LLM_KEY=            # 若用云端 API 填 key
```
未配置/不可用时返回友好错误，其余工具不受影响。

## 校验与调试
- 每个 MCP 自带 `client_test.py`，跑一遍即验证"握手→列工具→调用"。
- `exam.validate_questions` / `manual.validate_anchors` / `graph.related_questions` 都带自动校验（返回 `valid/errors`）。
- 写入类工具（`graph.add_node/add_edge/update_anchor`、`exam.wrong_*`）会**真实落盘**（`graph-data.json` / `wrong_store.json`），注意数据回滚或备份。

## 约定
- 复杂入参/返回统一用 **JSON 字符串**（`xx_json`），最稳妥、可跨 Host。
- 三个 MCP 均按 `mcp<2`（FastMCP 1.x）编写，与仓库 `ch07` MCP 实践一致；用 2.x 需改 `MCPServer`。
