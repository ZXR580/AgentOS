# AGENTS.md

智能体应用开发实践赛 · 知识手册学习站：VitePress 1.x 中文静态站。**无测试 / lint / typecheck**，`npm run build` 通过即为主要验证手段。Node ≥ 18。

## 命令

- `npm run dev` — 本地预览（http://localhost:5173）；`predev` / `prebuild` 钩子会自动执行 `node copy-docs.mjs`，无需手动跑同步脚本
- `npm run build` — 产物在 `docs/.vitepress/dist/`
- 图谱改动后需在 dev 下确认渲染正常（组件 `docs/.vitepress/theme/KnowledgeGraph.vue`，echarts）

## 内容源（README 与现实不符，先读这条）

- `copy-docs.mjs` 设计为从 `../KnowledgeBase/` 同步章节，但该目录**当前不存在**；脚本对缺失源文件会跳过并保留 `docs/` 现有版本。
- 因此现阶段手册的真正源文件就是 `docs/ch01~ch07.md`，直接编辑即可，README 里"勿直接编辑"的警告不适用。
- 每次开始内容工作前仍应检查 `../KnowledgeBase/` 是否已出现——一旦存在，必须改为编辑源文件再 `node copy-docs.mjs` 同步，否则 `docs/` 下的改动会被覆盖。

## 章节结构

ch01 AI 基础理论 / ch02 国产操作系统 / ch03 国产软件 / ch04 智能体（体量最大）/ ch05 国产硬件 / ch06 附录（高频考点·陷阱·易混对照·命令速查）/ ch07 MCP 与 Agent 落地实践。考核占比：AI 基础 30%，OS / 软件 / 智能体各 20%，硬件 10%（见 `docs/index.md`）。

## 知识图谱联动

- 数据全在 `docs/public/graph-data.json`：节点 `{id, name, module, chapter, anchor, desc}`，边 `{source, target, relation}`。注意：`.github/agents/*.md` 里写的 `href` 字段实际不存在，跳转链接由 `KnowledgeGraph.vue` 用 `chapter + '#' + anchor` 拼出；`graph.md` 只是组件壳页，无数据可改。
- 锚点是 VitePress 标题 slug：`1.2 大语言模型原理` → `_1-2-大语言模型原理`，`KV Cache` → `kv-cache`。**改任何 `##` / `###` 标题都必须同步 graph-data.json 里对应节点的 `anchor`**，否则图谱死链。
- 新增章节需四处联动：`copy-docs.mjs` 的 `files` 列表 + `docs/.vitepress/config.mts` 的 `nav`/`sidebar` + `graph-data.json` + `docs/index.md` 导览。

## Git 怪癖

- 仓库没有 `.gitignore`：`node_modules/`（约 6000 个文件）、`docs/.vitepress/cache/`、`dist/` 全部被 git 跟踪，`git status` 常年是脏的。提交时只 stage 实际改动的内容文件，**不要 `git add -A`**。
- `gpt-researcher/`、`langchain/` 是无 `.gitmodules` 的 gitlink（参考仓库克隆），与本站无关；`markdown/`、`maunals/`（UOS / 天数智芯 PDF 文档）是参考资料——都不是站点代码，勿改。

## 既有智能体定义

- `.github/agents/manual-refactor.agent.md` — 手册重构工作流（考点零丢失、一次一章、先诊断后重组再深化、图谱锚点同步）
- `.github/agents/knowledge-base.agent.md` — 章节新增 / 导航 / 图谱维护流程
- OpenCode 版手册重构智能体：`.opencode/agent/manual-refactor.md`（基于上述 md 构建，已修正其中过期的 `href` 字段与源目录描述）
