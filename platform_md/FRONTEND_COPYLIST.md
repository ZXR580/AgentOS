# 前端复制清单（VitePress 可视化知识站）

把下面的前端文件从本仓库复制到**新的 workspace**，替换 `docs/` 里的 markdown 内容后，就能 `npm install && npm run dev` 一键跑起来，得到一个"可视化 + 知识手册 + 考试 UI"的完整知识站。

> **前端 = VitePress 站点 + Vue 可视化组件**；**后端 MCP（`mcp/`）不在此清单**（另见 `mcp/README.md`）。两者通过 `docs/public/*.json` 打通数据。

---

## 一、必须复制的"骨架 + 组件"（缺一个，对应页面/组件就失效）

```
<新仓库根>/
├── package.json          # 依赖：vitepress / echarts / katex / markdown-it-katex / mermaid
├── copy-docs.mjs         # predev/prebuild 钩子（从 ../KnowledgeBase 同步，无源则跳过，可保留）
└── docs/
    ├── .vitepress/
    │   ├── config.mts             # 站点路由(nav/sidebar) + katex 插件
    │   └── theme/
    │       ├── index.js           # 全局注册全部组件（KnowledgeGraph/Mermaid/SectionGraph/Pillars/Compare/Flux/Layer/TermHover/ExamPage…）
    │       ├── HighlightLayer.vue
    │       ├── KnowledgeGraph.vue # 全站知识网络图（fetch graph-data.json）
    │       ├── TermHover.vue      # 名词悬浮解释（依赖 terms.json）
    │       ├── Mermaid.vue        # 文本即图（flowchart 等）
    │       ├── SectionGraph.vue   # 本章知识点子图（fetch graph-data.json，按 chapter 过滤）
    │       ├── Pillars.vue        # 构成/零件图解
    │       ├── Compare.vue        # 对比图解
    │       ├── Flux.vue           # 流程/步骤图解
    │       ├── Layer.vue          # 分层图解
    │       └── exam/
    │           ├── ExamPage.vue   # 考试入口 UI（fetch 两套题库）
    │           ├── useExam.js     # 组卷/状态机/判分/错题本
    │           ├── QuestionCard.vue
    │           └── AnswerSheet.vue
    └── public/
        ├── graph-data.json        # 知识图谱数据（可替换）
        ├── quiz-data.json         # 真题题库（可替换，缺则页面报错）
        ├── quiz-mock.json         # 模拟题库（可替换）
        └── terms.json             # 术语表（可替换）
```

## 二、可替换的"内容"
- `docs/ch0X.md`（各章正文）→ 换成你的新知识体系（可继续用 `<Mermaid/>`、`<Pillars/>`、`<SectionGraph/>` 等组件）。
- `docs/index.md`、`docs/graph.md`、`docs/exam.md` → 入口页，按需改。
- `docs/public/*.json` → 换成你的数据（或保留模板，前端组件需能读到）。

## 三、数据文件缺一不可（前端组件依赖）
| 文件 | 谁用 | 缺失后果 |
|---|---|---|
| `quiz-data.json` | `ExamPage` | 任一题库加载失败 → **整页报"题库加载失败"** |
| `quiz-mock.json` | `ExamPage` / 后端 `mcp/exam` | 同上 |
| `graph-data.json` | `KnowledgeGraph` / `SectionGraph` / 后端 `mcp/graph` | 图谱加载失败 |
| `terms.json` | `TermHover` | 名词悬浮失效 |

> 若暂时没有真题/图谱，可用最小占位：`quiz-data.json`/`quiz-mock.json` 填 `{"questions":[]}`，`graph-data.json` 填 `{"nodes":[],"edges":[]}`，`terms.json` 填 `[]`，页面能加载（只是空）。

## 四、一键 npm（新 workspace 替换 md 后）
```bash
npm install
npm run dev      # 本地预览 http://localhost:5173
npm run build    # 产物 docs/.vitepress/dist
```
> `predev`/`prebuild` 钩子会跑 `copy-docs.mjs`（从 `../KnowledgeBase/` 同步章节；该目录不存在则保留 `docs/` 现有版本、跳过）。若你的新体系不想要这个钩子，删掉 `package.json` 里的 `predev`/`prebuild` 即可。

## 五、按需精简（可选）
- **不要考试**：删 `theme/exam/`、`docs/exam.md`；`config.mts` 的 nav/sidebar 去掉 `/exam`；`theme/index.js` 去掉 `ExamPage` 注册与 import。
- **不要全站图谱**：删 `KnowledgeGraph.vue`、`docs/graph.md`（保留 `SectionGraph` 即可，它按章节渲染子图）。
- **不要名词悬浮**：删 `TermHover.vue`，并去掉 `theme/index.js` 里 `layout-top` 对它的引用。

## 六、依赖（已含在 package.json，不必再加）
- `vitepress`（构建）
- `echarts`（知识图谱/子图）
- `katex` + `markdown-it-katex`（公式；`config.mts` 已 `md.use(markdownItKatex)`，`theme/index.js` 已引 CSS）
- `mermaid`（`<Mermaid/>` 组件）

## 七、后端 MCP（可选，另拷）
若也要**可调用的构建/出题/图谱后端**，再拷整个 `mcp/` + 装 `mcp<2` + 在 `.opencode/opencode.json` 注册（见 `mcp/README.md`）。前后端共用 `docs/public/*.json`，相互打通。

---

**一句话**：把「一、骨架+组件」这几类文件复制到新 workspace，替换 `docs/` 下的 `ch0X.md` 与 `public/*.json`，即可 `npm install && npm run dev` 得到带可视化、可检索、可考试的新知识体系站点。
