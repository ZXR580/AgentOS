# REUSE_GUIDE：知识构建库复用指南

> 本指南告诉下一个 agent / 开发者：如何把本仓库「**知识手册构建 + 可视化 + 考试 + 知识图谱**」整套能力，复用到一套**新的知识体系**。**开始前先读本文件**，再按需读下方文档。

---

## 0. 这套库是什么
一套"知识体系"的完整生产链路，分**前端 + 后端 + 数据**三层：

- **前端（VitePress + Vue）**：可视化知识站——图表组件（Mermaid / Pillars / Compare / Flux / Layer）、知识网络图（KnowledgeGraph / SectionGraph）、考试 UI（ExamPage）、公式（KaTeX）、术语悬浮（TermHover）。
- **后端（3 个 MCP，`mcp/`）**：可被 AI 调用的确定性逻辑——建手册（**manual**）、管图谱（**graph**）、出题评测（**exam**）。
- **数据**：`docs/public/*.json`（图谱 / 题库 / 术语），**前后端共用**。

**核心闭环**：`manual 建结构 → graph 织关系 → exam 出题评测`；前端负责给"人"看。

---

## 1. 文档索引（先读哪个）
| 文档 | 内容 | 何时用 |
|---|---|---|
| **`REUSE_GUIDE.md`** | 本文件：总览 + 快速上手 + 坑 | 开始前必读 |
| `FRONTEND_COPYLIST.md` | 前端复制清单 + 一键 npm | 要整套前端知识站时 |
| `mcp/README.md` | 后端 3 个 MCP 的使用 / 串联 / 移植 | 要用可调用后端时 |
| `mcp/<x>/README.md` | 单个 MCP（exam / graph / manual）细节 | 细看某 MCP |
| `EXAM_SYSTEM_IMPLEMENTATION.md` | 考试系统实现原理 + RL 平台扩展 | 改考试 / 接 RL 时 |
| `docs/.vitepress/theme/` 各组件 | 可视化组件源码与用法示例（ch01/02/04/08 有演示） | 想自定义图表时 |

---

## 2. 三种复用模式
| 模式 | 复制什么 | 结果 |
|---|---|---|
| **A. 只前端** | `FRONTEND_COPYLIST.md` 的骨架 + 组件 | 可视化知识站（人看） |
| **B. 只后端** | `mcp/` + 装 `mcp<2` + `opencode.json` 注册 | AI 协作构建 / 出题 |
| **C. 完整（推荐）** | 前端 + 后端 + 数据 | 前端人看 + 后端 AI 用，数据打通 |

---

## 3. 快速上手（完整复用）
1. 按 `FRONTEND_COPYLIST.md` 复制前端骨架 + 组件 + `docs/public/*.json`（可用最小占位）。
2. 把 `docs/ch0X.md` 换成你的章节正文；需要图就用 `<Mermaid chart="..."/>`、`<Pillars data='...'/>`、`<SectionGraph chapter="/ch0X"/>` 等。
3. `npm install && npm run dev`（本地看效果）；`npm run build` 打包。
4. （可选，后端）拷 `mcp/` → `py -3 -m pip install "mcp>=1.0,<2"` → 在 `.opencode/opencode.json` 注册 3 个 MCP → **重启 opencode**。
5. 让 AI 用 `manual` 建章节骨架 → `graph` 补图谱关系 → `exam` 出题与评测（见 `mcp/README.md` 串联示例）。

---

## 4. 关键约定与坑（务必注意）
- **前端组件不在 `mcp/`**：Vue 组件与构建在 `docs/.vitepress/theme/` + `config.mts` + `package.json`；`mcp/` 只含 Python 后端。
- **mcp 依赖 `mcp<2`**（FastMCP 1.x）；2.x 把 `FastMCP` 改名 `MCPServer`，版本装错会 import 失败。
- **MCP 复杂入参/返回用 JSON 字符串**（`xx_json`），跨 Host 最稳、避免嵌套解析递归。
- **数据文件缺一不可**：`quiz-data.json / quiz-mock.json / graph-data.json / terms.json` 任一缺失，对应前端页面（考试 / 图谱 / 悬浮）会报错；最小占位见 `FRONTEND_COPYLIST.md` §3。
- **公式**：MCP 只产出 `$...$` / `$$...$$` 的 LaTeX 字符串，**渲染由前端 KaTeX 负责**；`$` 前后留空格、勿紧贴汉字/数字（否则 markdown-it-katex 不解析）。
- **锚点 / 图谱**：改章节标题必须同步 `graph-data.json` 对应节点 `anchor` 与 `terms.json` 的 `href`（`graph.update_anchor`、`manual.check_graph_sync` 可协助），否则死链。
- **写入会落盘**：`graph.add_node/add_edge/update_anchor`、`exam.wrong_*` 会写 `docs/public/graph-data.json` / `mcp/<x>/wrong_store.json`，注意备份。
- **opencode 配置不热重载**：改动 `opencode.json` 需**重启 opencode** 才生效（配置只在启动时加载一次）。
- **可视化组件是客户端渲染**：`npm run build` 只保证可编译；`Mermaid / Pillars / SectionGraph` 等的实际显示需 `npm run dev` 打开对应章节确认。

---

## 5. 一句话
> 复制前端骨架（`FRONTEND_COPYLIST.md`）→ 换 `docs/ch0X.md` 与 `docs/public/*.json` → `npm i && npm run dev` 得到可视化知识站；再拷 `mcp/` 并在 `.opencode/opencode.json` 注册，即可让 AI 协作构建 / 出题。前后端由 `docs/public/*.json` 打通。
