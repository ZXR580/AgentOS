# FRONTEND_SOURCE：前端完整源码蓝图（不拉库重建指南）

> 本文件内嵌了"可视化知识站"的**全部前端源码、配置、依赖、数据模板与组装路径**。
> 下一个 agent 只要按 `§1 组装路径` 建目录、把下面各代码块**原样粘贴**到对应文件，再 `npm install && npm run dev`，即可**不 clone 本仓库**重建同一套前端。后端 MCP（`mcp/`）见 `mcp/README.md`。

---

## §1 组装路径（把代码放到这些位置）
```
<新仓库根>/
├── package.json                        ← §2
├── copy-docs.mjs                       ← §3（可选）
└── docs/
    ├── index.md                        ← §12
    ├── graph.md                        ← §12
    ├── exam.md                         ← §12
    ├── .vitepress/
    │   ├── config.mts                  ← §4
    │   └── theme/
    │       ├── index.js                ← §5
    │       ├── Mermaid.vue             ← §6
    │       ├── SectionGraph.vue        ← §7
    │       ├── Pillars.vue             ← §8
    │       ├── Compare.vue             ← §9
    │       ├── Flux.vue                ← §10
    │       ├── Layer.vue               ← §11
    │       ├── KnowledgeGraph.vue      ← §13
    │       ├── TermHover.vue           ← §14
    │       ├── HighlightLayer.vue      ← §15
    │       └── exam/
    │           ├── ExamPage.vue        ← §16
    │           ├── useExam.js          ← §17
    │           ├── QuestionCard.vue    ← §18
    │           └── AnswerSheet.vue     ← §19
    └── public/
        ├── graph-data.json             ← §20
        ├── quiz-data.json              ← §20
        ├── quiz-mock.json              ← §20
        └── terms.json                  ← §20
```

---

## §2 package.json
```json
{
  "name": "knowledge-site",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vitepress dev docs",
    "build": "vitepress build docs",
    "preview": "vitepress preview docs"
  },
  "dependencies": {
    "vitepress": "^1.6.3",
    "echarts": "^5.6.0",
    "katex": "^0.18.4",
    "markdown-it-katex": "^2.0.3",
    "mermaid": "^11.17.2"
  }
}
```

## §3 copy-docs.mjs（可选；不需要同步可删除并在 package.json 去掉 predev/prebuild）
```js
import { copyFileSync, existsSync, mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const srcDir = join(__dirname, '..', 'KnowledgeBase')
const dstDir = join(__dirname, 'docs')

if (!existsSync(srcDir)) {
  console.log('[copy-docs] KnowledgeBase 未找到，跳过同步（docs/ 即为内容源）')
  process.exit(0)
}

const files = [
  'ch01_ai_foundation.md','ch02_os_linux.md','ch03_software.md','ch04_agent.md',
  'ch05_hardware.md','ch06_appendix.md','ch07_mcp_agent_practice.md','ch08_intelligent_platform.md',
]
mkdirSync(dstDir, { recursive: true })
for (const f of files) {
  const src = join(srcDir, f)
  if (!existsSync(src)) { console.log(`[copy-docs] 源文件缺失，跳过: ${src}`); continue }
  copyFileSync(src, join(dstDir, f))
  console.log('copied', f)
}
```

## §4 docs/.vitepress/config.mts
```ts
import { defineConfig } from 'vitepress'
import markdownItKatex from 'markdown-it-katex'

export default defineConfig({
  title: '知识手册',
  description: '可视化知识手册',
  lang: 'zh-CN',
  cleanUrls: true,
  markdown: {
    config(md) { md.use(markdownItKatex) },
  },
  themeConfig: {
    nav: [
      { text: '总览', link: '/' },
      { text: '模拟考试', link: '/exam' },
      { text: '知识网络图', link: '/graph' },
      // 各章链接按需加，如 { text: '第 1 章', link: '/ch01' }
    ],
    sidebar: [
      { text: '导航', items: [
        { text: '总览', link: '/' },
        { text: '模拟考试', link: '/exam' },
        { text: '知识网络图', link: '/graph' },
      ]},
      // 你的章节列表按需加
    ],
    search: { provider: 'local' },
    outline: { level: [2, 3], label: '本页目录' },
    darkModeSwitchLabel: '深色模式',
    sidebarMenuLabel: '目录',
    returnToTopLabel: '返回顶部',
  },
  vite: { optimizeDeps: { include: ['echarts/core'] } },
})
```

## §5 docs/.vitepress/theme/index.js
```js
import DefaultTheme from 'vitepress/theme'
import { h } from 'vue'
import 'katex/dist/katex.min.css'
import HighlightLayer from './HighlightLayer.vue'
import TermHover from './TermHover.vue'
import KnowledgeGraph from './KnowledgeGraph.vue'
import Mermaid from './Mermaid.vue'
import SectionGraph from './SectionGraph.vue'
import Flux from './Flux.vue'
import Compare from './Compare.vue'
import Pillars from './Pillars.vue'
import Layer from './Layer.vue'
import ExamPage from './exam/ExamPage.vue'

export default {
  extends: DefaultTheme,
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'layout-top': () => [h(HighlightLayer), h(TermHover)],
    })
  },
  enhanceApp({ app }) {
    app.component('KnowledgeGraph', KnowledgeGraph)
    app.component('Mermaid', Mermaid)
    app.component('SectionGraph', SectionGraph)
    app.component('Flux', Flux)
    app.component('Compare', Compare)
    app.component('Pillars', Pillars)
    app.component('Layer', Layer)
    app.component('ExamPage', ExamPage)
  },
}
```

## §6 docs/.vitepress/theme/Mermaid.vue
```vue
<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import mermaid from 'mermaid'

const props = defineProps({
  chart: { type: String, default: '' },
  caption: { type: String, default: '' },
})
const el = ref(null)
const svg = ref('')
let obs = null
function isDark() { return document.documentElement.classList.contains('dark') }
async function render() {
  const src = (props.chart || '').trim()
  if (!src) return
  try {
    mermaid.initialize({ startOnLoad: false, theme: isDark() ? 'dark' : 'default', securityLevel: 'loose' })
    const { svg: out } = await mermaid.render('mmd-' + Date.now() + '-' + Math.floor(Math.random() * 1e6), src)
    svg.value = out
  } catch (e) { svg.value = '<pre style="color:#ef4444">Mermaid 渲染失败：' + String(e) + '</pre>' }
}
onMounted(() => { render(); obs = new MutationObserver(() => render()); obs.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] }) })
onBeforeUnmount(() => { if (obs) obs.disconnect() })
</script>

<template>
  <figure class="mermaid-figure">
    <div ref="el" class="mermaid-svg" v-html="svg"></div>
    <figcaption v-if="caption" class="mermaid-caption">{{ caption }}</figcaption>
  </figure>
</template>

<style>
.mermaid-figure { margin: 16px 0; text-align: center; }
.mermaid-svg { display: inline-block; max-width: 100%; overflow-x: auto; padding: 8px; }
.mermaid-svg svg { max-width: 100%; height: auto; }
.mermaid-caption { margin-top: 4px; font-size: 12px; color: var(--vp-c-text-3, #999); }
</style>
```

## §7 docs/.vitepress/theme/SectionGraph.vue
```vue
<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import { TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
echarts.use([GraphChart, TooltipComponent, CanvasRenderer])

const props = defineProps({
  chapter: { type: String, required: true },
  title: { type: String, default: '本章知识点脉络' },
})
const MODULES = [{ value: 'ai', color: '#3b82f6' }, { value: 'agent', color: '#8b5cf6' },
  { value: 'os', color: '#10b981' }, { value: 'software', color: '#f59e0b' }, { value: 'hardware', color: '#ef4444' }]
const chartEl = ref(null)
const errorMsg = ref('')
const count = ref(0)
let chart = null, nodes = [], edges = []
function color(m) { const f = MODULES.find((x) => x.value === m); return f ? f.color : '#94a3b8' }
function isDark() { return document.documentElement.classList.contains('dark') }
function onResize() { if (chart) chart.resize() }
function option() {
  const dark = isDark(); const nodeColor = dark ? '#ccc' : '#333'; const edgeColor = dark ? '#8a8a8a' : '#999'
  return {
    tooltip: { trigger: 'item', backgroundColor: dark ? '#1f1f1f' : '#fff', borderColor: dark ? '#444' : '#ddd', textStyle: { color: dark ? '#ccc' : '#333', fontSize: 12 } },
    series: [{ type: 'graph', layout: 'force', roam: true, draggable: true, force: { repulsion: 220, edgeLength: [70, 130], gravity: 0.1 },
      data: nodes.map((n) => ({ name: n.id, displayName: n.name || n.id, chapter: n.chapter, anchor: n.anchor, symbolSize: 30, itemStyle: { color: color(n.module) } })),
      links: edges.map((e) => ({ source: e.source, target: e.target, relation: e.relation })),
      label: { show: true, fontSize: 11, color: nodeColor, formatter: (p) => p.data.displayName },
      edgeLabel: { show: true, fontSize: 10, color: edgeColor, formatter: (p) => p.data.relation },
      lineStyle: { color: edgeColor, opacity: 0.5, width: 1.2 }, emphasis: { focus: 'adjacency' }, animationDuration: 400 }],
  }
}
function onClick(p) { if (p && p.componentType === 'series' && p.dataType === 'node' && p.data && p.data.chapter && p.data.anchor) window.open(p.data.chapter + '#' + p.data.anchor, '_blank') }
let obs = null
onMounted(async () => {
  try {
    const res = await fetch('/graph-data.json')
    if (!res.ok) throw new Error('bad status ' + res.status)
    const data = await res.json()
    nodes = (data.nodes || []).filter((n) => n && n.chapter === props.chapter)
    const idSet = new Set(nodes.map((n) => n.id))
    edges = (data.edges || []).filter((e) => idSet.has(e.source) && idSet.has(e.target))
    count.value = nodes.length
    if (!chart && chartEl.value) { chart = echarts.init(chartEl.value); chart.setOption(option()); chart.on('click', onClick) }
    window.addEventListener('resize', onResize)
    obs = new MutationObserver(() => chart && chart.setOption(option()))
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
  } catch { errorMsg.value = '本章知识点图谱加载失败' }
})
onBeforeUnmount(() => { window.removeEventListener('resize', onResize); if (obs) obs.disconnect(); if (chart) { chart.dispose(); chart = null } })
</script>

<template>
  <div class="sg-wrap">
    <div class="sg-head"><span class="sg-title">{{ title }}</span><span class="sg-count">{{ count }} 个知识点 · 点击节点跳转对应小节</span></div>
    <div v-if="!errorMsg" ref="chartEl" class="sg-chart" style="height: 320px; width: 100%"></div>
    <p v-if="errorMsg" class="sg-error">{{ errorMsg }}</p>
  </div>
</template>

<style>
.sg-wrap { margin: 20px 0 8px; border: 1px solid var(--vp-c-divider, #e2e2e2); border-radius: 12px; padding: 12px; background: var(--vp-c-bg, #fff); }
.sg-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; }
.sg-title { font-weight: 600; font-size: 15px; color: var(--vp-c-text-1, #333); }
.sg-count { font-size: 12px; color: var(--vp-c-text-3, #999); }
.sg-chart { background: transparent; }
.sg-error { color: #999; font-size: 13px; }
</style>
```

## §8 docs/.vitepress/theme/Pillars.vue
```vue
<script setup>
import { ref, onMounted, computed } from 'vue'
const props = defineProps({ data: { type: String, default: '{}' }, title: { type: String, default: '' } })
const pillars = ref([]); const active = ref(null)
onMounted(() => { try { const d = JSON.parse(props.data); pillars.value = (d && d.pillars) || [] } catch { pillars.value = [] } })
function toggle(i) { active.value = active.value === i ? null : i }
const cur = computed(() => (active.value !== null ? pillars.value[active.value] : null))
</script>

<template>
  <div class="viz viz-pillars">
    <div v-if="title || props.title" class="viz-title">{{ title || props.title }}</div>
    <div class="pil-row">
      <div v-for="(p, i) in pillars" :key="i" class="pil-item" :class="{ active: active === i }" @click="toggle(i)">
        <div class="pil-num">{{ i + 1 }}</div>
        <div class="pil-title">{{ p.title }}</div>
        <div v-if="p.tag" class="pil-tag">{{ p.tag }}</div>
      </div>
    </div>
    <div v-if="cur" class="pil-desc"><strong>{{ cur.title }}</strong>{{ cur.desc ? ' — ' + cur.desc : '' }}</div>
  </div>
</template>

<style>
.viz-title { font-weight: 600; font-size: 15px; margin-bottom: 10px; color: var(--vp-c-text-1, #333); }
.viz-pillars .pil-row { display: flex; gap: 10px; flex-wrap: wrap; }
.viz-pillars .pil-item { flex: 1; min-width: 110px; border: 1px solid var(--vp-c-divider); border-radius: 12px; background: var(--vp-c-bg); padding: 14px 12px; text-align: center; cursor: pointer; transition: all 0.15s; color: var(--vp-c-text-1); }
.viz-pillars .pil-item:hover { border-color: var(--vp-c-brand); }
.viz-pillars .pil-item.active { border-color: var(--vp-c-brand); background: var(--vp-c-brand-soft); }
.viz-pillars .pil-num { font-size: 12px; color: var(--vp-c-text-3); margin-bottom: 4px; }
.viz-pillars .pil-title { font-weight: 600; font-size: 14px; }
.viz-pillars .pil-tag { font-size: 12px; color: var(--vp-c-text-3); margin-top: 2px; }
.viz-pillars .pil-desc { margin-top: 10px; font-size: 13px; color: var(--vp-c-text-2); background: var(--vp-c-bg-alt); border-radius: 8px; padding: 8px 12px; }
</style>
```

## §9 docs/.vitepress/theme/Compare.vue
```vue
<script setup>
import { ref, onMounted } from 'vue'
const props = defineProps({ data: { type: String, default: '{}' }, title: { type: String, default: '' } })
const columns = ref([]); const rows = ref([]); const activeDim = ref(null); const activeCol = ref(null)
onMounted(() => { try { const d = JSON.parse(props.data); columns.value = (d && d.columns) || []; rows.value = (d && d.rows) || [] } catch { columns.value = []; rows.value = [] } })
function toggleDim(i) { activeDim.value = activeDim.value === i ? null : i }
function toggleCol(i) { activeCol.value = activeCol.value === i ? null : i }
</script>

<template>
  <div class="viz viz-compare">
    <div v-if="title || props.title" class="viz-title">{{ title || props.title }}</div>
    <table class="cmp-table">
      <thead><tr><th class="cmp-dim" @click="toggleCol(-1)">维度</th>
        <th v-for="(c, i) in columns" :key="i" :class="{ active: activeCol === i }" @click="toggleCol(i)">{{ c }}</th></tr></thead>
      <tbody><tr v-for="(r, i) in rows" :key="i" :class="{ active: activeDim === i }">
        <td class="cmp-dim" @click="toggleDim(i)">{{ r.dim }}</td>
        <td v-for="(cell, j) in r.cells" :key="j" :class="{ 'col-hit': activeCol === j }">{{ cell }}</td>
      </tr></tbody>
    </table>
    <div class="cmp-hint">点击维度或列可高亮对比差异</div>
  </div>
</template>

<style>
.viz-compare .cmp-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 6px; }
.viz-compare .cmp-table th, .viz-compare .cmp-table td { border: 1px solid var(--vp-c-divider); padding: 7px 10px; text-align: left; color: var(--vp-c-text-1); }
.viz-compare .cmp-table th { background: var(--vp-c-bg-alt); font-weight: 600; cursor: pointer; }
.viz-compare .cmp-table th.active, .viz-compare .cmp-table td.col-hit { background: var(--vp-c-brand-soft); }
.viz-compare .cmp-table tr.active td { background: var(--vp-c-brand-soft); }
.viz-compare .cmp-dim { font-weight: 600; color: var(--vp-c-text-2); cursor: pointer; }
.viz-compare .cmp-hint { margin-top: 6px; font-size: 12px; color: var(--vp-c-text-3); }
</style>
```

## §10 docs/.vitepress/theme/Flux.vue
```vue
<script setup>
import { ref, onMounted, computed } from 'vue'
const props = defineProps({ data: { type: String, default: '{}' }, title: { type: String, default: '' } })
const steps = ref([]); const active = ref(null)
onMounted(() => { try { const d = JSON.parse(props.data); steps.value = (d && d.steps) || [] } catch { steps.value = [] } })
function toggle(i) { active.value = active.value === i ? null : i }
const cur = computed(() => (active.value !== null ? steps.value[active.value] : null))
</script>

<template>
  <div class="viz viz-flux">
    <div v-if="title || props.title" class="viz-title">{{ title || props.title }}</div>
    <div class="flux-track">
      <template v-for="(s, i) in steps" :key="i">
        <div class="flux-step" :class="{ active: active === i }" @click="toggle(i)">
          <div class="flux-label">{{ s.label }}</div>
          <div v-if="s.tag" class="flux-tag">{{ s.tag }}</div>
        </div>
        <div v-if="i < steps.length - 1" class="flux-arrow">→</div>
      </template>
    </div>
    <div v-if="cur" class="flux-desc"><strong>{{ cur.label }}</strong>{{ cur.desc ? ' — ' + cur.desc : '' }}</div>
  </div>
</template>

<style>
.viz-flux .flux-track { display: flex; align-items: stretch; gap: 6px; flex-wrap: wrap; }
.viz-flux .flux-step { flex: 1; min-width: 110px; padding: 10px 12px; border: 1px solid var(--vp-c-divider); border-radius: 10px; background: var(--vp-c-bg); cursor: pointer; text-align: center; transition: all 0.15s; color: var(--vp-c-text-1); }
.viz-flux .flux-step:hover { border-color: var(--vp-c-brand); }
.viz-flux .flux-step.active { border-color: var(--vp-c-brand); background: var(--vp-c-brand-soft); }
.viz-flux .flux-label { font-weight: 600; font-size: 14px; }
.viz-flux .flux-tag { font-size: 12px; color: var(--vp-c-text-3); margin-top: 2px; }
.viz-flux .flux-arrow { align-self: center; color: var(--vp-c-text-3); font-size: 16px; }
.viz-flux .flux-desc { margin-top: 10px; font-size: 13px; color: var(--vp-c-text-2); background: var(--vp-c-bg-alt); border-radius: 8px; padding: 8px 12px; }
</style>
```

## §11 docs/.vitepress/theme/Layer.vue
```vue
<script setup>
import { ref, onMounted } from 'vue'
const props = defineProps({ data: { type: String, default: '{}' }, title: { type: String, default: '' } })
const layers = ref([]); const sequence = ref('top-down'); const active = ref(null)
onMounted(() => { try { const d = JSON.parse(props.data); sequence.value = (d && d.sequence) || 'top-down'; let arr = (d && d.layers) || []; if (sequence.value === 'bottom-up') arr = [...arr].reverse(); layers.value = arr } catch { layers.value = [] } })
function toggle(i) { active.value = active.value === i ? null : i }
</script>

<template>
  <div class="viz viz-layer">
    <div v-if="title || props.title" class="viz-title">{{ title || props.title }}</div>
    <div class="lay-stack">
      <div v-for="(l, i) in layers" :key="i" class="lay-item" :class="{ active: active === i }" @click="toggle(i)">
        <div class="lay-head"><span class="lay-title">{{ l.title }}</span><span class="lay-arrow">{{ active === i ? '▾' : '▸' }}</span></div>
        <div v-if="active === i" class="lay-items"><span v-for="(it, k) in l.items" :key="k" class="lay-chip">{{ it }}</span></div>
      </div>
    </div>
  </div>
</template>

<style>
.viz-layer .lay-stack { display: flex; flex-direction: column; gap: 8px; }
.viz-layer .lay-item { border: 1px solid var(--vp-c-divider); border-radius: 10px; background: var(--vp-c-bg); padding: 10px 14px; cursor: pointer; transition: all 0.15s; color: var(--vp-c-text-1); }
.viz-layer .lay-item:hover { border-color: var(--vp-c-brand); }
.viz-layer .lay-item.active { border-color: var(--vp-c-brand); background: var(--vp-c-brand-soft); }
.viz-layer .lay-head { display: flex; justify-content: space-between; align-items: center; font-weight: 600; font-size: 14px; }
.viz-layer .lay-arrow { color: var(--vp-c-text-3); }
.viz-layer .lay-items { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px; }
.viz-layer .lay-chip { font-size: 12px; background: var(--vp-c-bg-alt); border: 1px solid var(--vp-c-divider); border-radius: 6px; padding: 2px 8px; color: var(--vp-c-text-2); }
</style>

## §12 入口 md（docs/ 下）
`docs/index.md`：
```md
# 知识手册

基于可视化 + 模拟练习的知识手册。

## 章节导览

- [模拟考试](/exam)
- [知识网络图](/graph)
（各章链接按需加）

## 使用说明

- 选中正文文本可高亮；带下划线的术语可悬浮查看解释；知识网络图可搜索、点击聚焦。
```
`docs/graph.md`：
```md
# 知识网络图

探索式知识图谱：搜索高亮、点击节点邻域聚焦、右侧面板显示详情与关联、图例切换模块、可缩放拖拽。

<KnowledgeGraph />
```
`docs/exam.md`：
```md
# 模拟考试

真题练习 / 模拟练习 / 错题本三入口。答题阶段无答案，交卷后评分并可看解析。

<ExamPage />
```

## §13 docs/.vitepress/theme/KnowledgeGraph.vue
```vue
<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import * as echarts from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([GraphChart, TooltipComponent, LegendComponent, CanvasRenderer])

const MODULES = [
  { value: 'ai', label: 'AI', color: '#3b82f6' },
  { value: 'agent', label: 'Agent', color: '#8b5cf6' },
  { value: 'os', label: 'OS', color: '#10b981' },
  { value: 'software', label: 'Software', color: '#f59e0b' },
  { value: 'hardware', label: 'Hardware', color: '#ef4444' },
]
const FALLBACK_COLOR = '#94a3b8'

const chartEl = ref(null)
const errorMsg = ref('')
const card = ref(null)
const searchQ = ref('')
const focusId = ref(null)
const stats = ref({ nodes: 0, edges: 0 })

let chart = null
let allNodes = []
let allEdges = []
let selected = {}
let neighborMap = new Map()
let themeObserver = null

function isDark() { return document.documentElement.classList.contains('dark') }
function moduleOf(v) { return MODULES.find((m) => m.value === v) }
function moduleColor(v) { const m = moduleOf(v); return m ? m.color : FALLBACK_COLOR }
function moduleLabel(v) { const m = moduleOf(v); return m ? m.label : String(v == null ? '未知' : v) }
function visibleModules() { return new Set(Object.keys(selected).filter((k) => selected[k])) }

function buildNeighbors() {
  neighborMap = new Map()
  for (const n of allNodes) neighborMap.set(n.id, new Set())
  for (const e of allEdges) {
    if (!neighborMap.has(e.source) || !neighborMap.has(e.target)) continue
    neighborMap.get(e.source).add(e.target); neighborMap.get(e.target).add(e.source)
  }
}
function neighborsOf(id) { return neighborMap.get(id) || new Set() }
function matchesQuery(n) {
  if (!searchQ.value.trim()) return null
  const q = searchQ.value.trim().toLowerCase()
  return [n.id, n.name || '', n.desc || ''].join(' ').toLowerCase().includes(q)
}

function buildOption() {
  const dark = isDark()
  const nodeColor = dark ? '#ccc' : '#333'
  const edgeColor = dark ? '#8a8a8a' : '#999'
  const activeMods = visibleModules()
  const focus = focusId.value
  const focusSet = focus ? new Set([focus, ...neighborsOf(focus)]) : null
  const nodes = allNodes.filter((n) => activeMods.has(moduleLabel(n.module)))
  const nodeIds = new Set(nodes.map((n) => n.id))
  const nodeData = nodes.map((n) => {
    const style = { itemStyle: { color: moduleColor(n.module), opacity: 1 }, symbolSize: 36 }
    if (focusSet) {
      if (focusSet.has(n.id)) {
        style.itemStyle.opacity = 1
        if (n.id === focus) { style.symbolSize = 52; style.itemStyle.borderColor = moduleColor(n.module); style.itemStyle.borderWidth = 3 }
        else { style.symbolSize = 40; style.itemStyle.opacity = 0.95 }
      } else { style.itemStyle.opacity = 0.12; style.symbolSize = 26 }
    } else {
      const hit = matchesQuery(n)
      if (hit === true) { style.symbolSize = 46; style.itemStyle.borderColor = moduleColor(n.module); style.itemStyle.borderWidth = 3; style.itemStyle.opacity = 1 }
      else if (hit === false) { style.itemStyle.opacity = 0.12; style.symbolSize = 26 }
    }
    return { name: n.id, displayName: n.name || n.id, module: n.module, desc: n.desc, chapter: n.chapter, anchor: n.anchor, focus: focus === n.id, symbolSize: style.symbolSize, itemStyle: style.itemStyle, label: { show: focusSet ? (focusSet.has(n.id)) : (matchesQuery(n) !== false), color: nodeColor, fontSize: 12 } }
  })
  const links = allEdges.filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))
    .map((e) => { const active = focusSet ? (focusSet.has(e.source) && focusSet.has(e.target)) : true
      return { source: e.source, target: e.target, relation: e.relation, lineStyle: { color: edgeColor, opacity: active ? 0.7 : 0.06, width: active ? 1.8 : 1 } } })
  return {
    tooltip: { trigger: 'item', backgroundColor: dark ? '#1f1f1f' : '#fff', borderColor: dark ? '#444' : '#ddd', textStyle: { color: dark ? '#ccc' : '#333', fontSize: 12 } },
    legend: { top: 8, left: 'center', data: MODULES.map((m) => ({ name: m.label, icon: 'circle', itemStyle: { color: m.color } })), selected, textStyle: { color: nodeColor, fontSize: 12 } },
    series: [{ type: 'graph', layout: 'force', roam: true, draggable: true, force: { repulsion: 320, edgeLength: [80, 160], gravity: 0.08 },
      data: nodeData, links, label: { show: true, fontSize: 12, color: nodeColor },
      edgeLabel: { show: true, fontSize: 10, color: edgeColor, formatter: (p) => p.data.relation },
      lineStyle: { color: edgeColor, opacity: 0.6, width: 1.5 }, emphasis: { focus: 'adjacency', scale: true },
      animationDuration: 500, animationDurationUpdate: 300, animationEasingUpdate: 'quinticInOut' }],
  }
}

function update() { if (chart) chart.setOption(buildOption()) }
function onLegendChanged(params) { selected = { ...params.selected }; update() }
function onChartClick(params) { if (params && params.componentType === 'series' && params.dataType === 'node' && params.data) setFocus(params.data.name); else clearFocus() }
function setFocus(id) {
  focusId.value = id
  const n = allNodes.find((x) => x.id === id)
  if (!n) return
  const rels = [...neighborsOf(id)].map((ne) => {
    const nn = allNodes.find((x) => x.id === ne)
    const edge = allEdges.find((e) => (e.source === id && e.target === ne) || (e.source === ne && e.target === id))
    return { id: ne, name: nn ? (nn.name || nn.id) : ne, module: nn ? nn.module : '', relation: edge ? edge.relation : '' }
  })
  card.value = { id: n.id, name: n.name || n.id, module: n.module, desc: n.desc || '', chapter: n.chapter, anchor: n.anchor, rels }
  update()
}
function clearFocus() { focusId.value = null; card.value = null; update() }
function onClickRelation(relId) { setFocus(relId) }
function onSearchInput() { focusId.value = null; card.value = null; update() }
function onResize() { if (chart) chart.resize() }
const statsText = computed(() => `${stats.value.nodes} 个知识点 · ${stats.value.edges} 条关系`)

onMounted(async () => {
  try {
    const res = await fetch('/graph-data.json')
    if (!res.ok) throw new Error('bad status ' + res.status)
    const data = await res.json()
    if (!data || !Array.isArray(data.nodes)) throw new Error('invalid payload')
    allNodes = data.nodes.filter((n) => n && n.id)
    allEdges = (data.edges || []).filter((e) => e && e.source != null && e.target != null)
    stats.value = { nodes: allNodes.length, edges: allEdges.length }
    buildNeighbors()
    MODULES.forEach((m) => { selected[m.label] = true })
    chart = echarts.init(chartEl.value)
    chart.setOption(buildOption())
    chart.on('legendselectchanged', onLegendChanged)
    chart.on('click', onChartClick)
    window.addEventListener('resize', onResize)
    themeObserver = new MutationObserver(() => update())
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
  } catch { errorMsg.value = '图谱数据加载失败' }
})
onBeforeUnmount(() => { window.removeEventListener('resize', onResize); if (themeObserver) themeObserver.disconnect(); if (chart) { chart.dispose(); chart = null } })
</script>

<template>
  <div class="kg-root">
    <div class="kg-toolbar">
      <span class="kg-stats">{{ statsText }}</span>
      <div class="kg-search">
        <input v-model="searchQ" class="kg-search-input" type="text" placeholder="搜索知识点 / 描述…" @input="onSearchInput" />
        <button v-if="searchQ" class="kg-search-clear" aria-label="清空搜索" @click="searchQ = ''; onSearchInput()">×</button>
      </div>
      <button v-if="focusId" class="kg-reset" @click="clearFocus">重置视图</button>
    </div>
    <div v-show="!errorMsg" ref="chartEl" class="kg-chart" style="height: calc(100vh - 210px); width: 100%"></div>
    <p v-if="errorMsg" class="kg-error">{{ errorMsg }}</p>
    <Teleport to="body">
      <div v-if="card" class="kg-panel">
        <div class="kg-panel-head"><span class="kg-panel-title">{{ card.name }}</span><button class="kg-panel-close" aria-label="关闭" @click="clearFocus">×</button></div>
        <span class="kg-panel-module">{{ moduleLabel(card.module) }}</span>
        <p class="kg-panel-desc">{{ card.desc }}</p>
        <a v-if="card.anchor" class="kg-panel-link" :href="(card.chapter || '') + '#' + card.anchor" target="_blank">查看详情</a>
        <div v-if="card.rels && card.rels.length" class="kg-panel-rels">
          <div class="kg-panel-rels-title">关联知识点（{{ card.rels.length }}）</div>
          <button v-for="r in card.rels" :key="r.id" class="kg-panel-rel" @click="onClickRelation(r.id)">
            <span class="kg-panel-rel-name">{{ r.name }}</span><span class="kg-panel-rel-rel">{{ r.relation }}</span>
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style>
.kg-root { position: relative; }
.kg-chart { background: transparent; }
.kg-error { color: #999; text-align: center; padding: 40px 0; font-size: 14px; }
.kg-toolbar { display: flex; align-items: center; gap: 12px; padding: 8px 4px; flex-wrap: wrap; }
.kg-stats { font-size: 12px; color: var(--vp-c-text-3, #999); }
.kg-search { position: relative; display: inline-flex; align-items: center; }
.kg-search-input { width: 240px; padding: 6px 28px 6px 10px; border: 1px solid var(--vp-c-divider, #ddd); border-radius: 8px; background: var(--vp-c-bg, #fff); color: var(--vp-c-text-1, #333); font-size: 13px; outline: none; }
.kg-search-input:focus { border-color: var(--vp-c-brand, #3b82f6); }
.kg-search-clear { position: absolute; right: 6px; border: none; background: none; cursor: pointer; color: var(--vp-c-text-3, #999); font-size: 14px; line-height: 1; }
.kg-reset { border: 1px solid var(--vp-c-divider, #ddd); border-radius: 8px; background: var(--vp-c-bg, #fff); color: var(--vp-c-text-1, #333); padding: 6px 12px; font-size: 13px; cursor: pointer; }
.kg-reset:hover { border-color: var(--vp-c-brand, #3b82f6); color: var(--vp-c-brand, #3b82f6); }
.kg-panel { position: fixed; top: 120px; right: 24px; z-index: 1000; width: 300px; max-width: calc(100vw - 48px); background: #fff; border: 1px solid #e2e2e2; border-radius: 10px; box-shadow: 0 8px 24px rgba(0,0,0,0.14); padding: 14px 16px; color: #333; font-size: 13px; max-height: calc(100vh - 180px); overflow: auto; }
.kg-panel-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.kg-panel-title { font-size: 16px; font-weight: 700; }
.kg-panel-close { border: none; background: none; cursor: pointer; font-size: 18px; line-height: 1; color: #999; }
.kg-panel-module { display: inline-block; font-size: 12px; color: #666; background: #f5f5f5; border-radius: 4px; padding: 1px 8px; margin-bottom: 8px; }
.kg-panel-desc { margin: 0 0 10px; line-height: 1.65; color: #444; }
.kg-panel-link { display: inline-block; color: #3b82f6; text-decoration: none; font-size: 13px; margin-bottom: 12px; }
.kg-panel-rels-title { font-size: 12px; font-weight: 600; color: #666; margin-bottom: 6px; padding-top: 8px; border-top: 1px dashed #e2e2e2; }
.kg-panel-rel { display: flex; justify-content: space-between; align-items: center; width: 100%; border: 1px solid var(--vp-c-divider, #e2e2e2); border-radius: 8px; background: var(--vp-c-bg-alt, #fafafa); padding: 6px 10px; margin-bottom: 6px; cursor: pointer; font-size: 13px; color: #333; text-align: left; }
.kg-panel-rel:hover { border-color: #3b82f6; }
.kg-panel-rel-name { font-weight: 500; }
.kg-panel-rel-rel { font-size: 12px; color: #999; }
.dark .kg-panel { background: #1e1e1e; border-color: #3a3a3a; color: #ddd; }
.dark .kg-panel-title { color: #eee; }
.dark .kg-panel-module { background: #2a2a2a; color: #aaa; }
.dark .kg-panel-desc { color: #bbb; }
.dark .kg-panel-close { color: #777; }
.dark .kg-panel-rels-title { color: #999; border-color: #3a3a3a; }
.dark .kg-panel-rel { background: #2a2a2a; color: #ddd; border-color: #3a3a3a; }
.dark .kg-panel-rel:hover { border-color: #3b82f6; }
.dark .kg-panel-rel-rel { color: #888; }
.dark .kg-stats { color: #777; }
</style>

## §14 docs/.vitepress/theme/TermHover.vue
```vue
<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute } from 'vitepress'
const route = useRoute()
const terms = ref([])
const tooltip = ref(null)
let scanTimer = null
async function loadTerms() {
  try {
    const res = await fetch('/terms.json')
    if (!res.ok) throw new Error()
    const data = await res.json()
    terms.value = (data.terms || []).sort((a, b) => b.term.length - a.term.length)
  } catch { terms.value = [] }
}
function isSkippable(node) {
  const el = node.parentElement
  if (!el) return true
  if (el.closest('pre, code, .vp-code, .eq-option, .kg-card, .exam-analysis-text')) return true
  if (el.closest('mark')) return true
  return false
}
function scan() {
  if (terms.value.length === 0) return
  const doc = document.querySelector('.VPDoc')
  if (!doc) return
  const walker = document.createTreeWalker(doc, NodeFilter.SHOW_TEXT, {
    acceptNode(node) { if (isSkippable(node)) return NodeFilter.FILTER_REJECT; if (!node.textContent.trim()) return NodeFilter.FILTER_REJECT; return NodeFilter.FILTER_ACCEPT },
  })
  const textNodes = []
  while (walker.nextNode()) textNodes.push(walker.currentNode)
  for (const node of textNodes) wrapTextNode(node)
}
function wrapTextNode(node) {
  let text = node.textContent
  if (text.length < 2) return
  const matches = []
  for (const t of terms.value) { let idx = 0; while ((idx = text.indexOf(t.term, idx)) !== -1) { matches.push({ term: t, index: idx }); idx += t.term.length } }
  if (matches.length === 0) return
  matches.sort((a, b) => a.index - b.index)
  const frag = document.createDocumentFragment()
  let cursor = 0
  for (const m of matches) {
    if (m.index < cursor) continue
    if (m.index > cursor) frag.appendChild(document.createTextNode(text.slice(cursor, m.index)))
    const span = document.createElement('span')
    span.className = 'term-hover'
    span.dataset.term = m.term.term
    span.textContent = m.term.term
    span.addEventListener('mouseenter', (e) => showTip(e, m.term))
    span.addEventListener('mouseleave', hideTip)
    span.addEventListener('click', () => { if (m.term.href) window.location.href = m.term.href })
    frag.appendChild(span)
    cursor = m.index + m.term.term.length
  }
  if (cursor < text.length) frag.appendChild(document.createTextNode(text.slice(cursor)))
  node.parentNode.replaceChild(frag, node)
}
function showTip(e, term) {
  const rect = e.target.getBoundingClientRect()
  tooltip.value = { term: term.term, desc: term.desc, href: term.href || '', x: rect.left + rect.width / 2, y: rect.bottom + 8 }
}
function hideTip() { tooltip.value = null }
watch(() => route.path, () => { clearTimeout(scanTimer); scanTimer = setTimeout(scan, 200) })
onMounted(async () => { await loadTerms(); scan() })
</script>

<template>
  <Teleport to="body">
    <div v-if="tooltip" class="term-tip" :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }" @mouseenter="tooltip = tooltip" @mouseleave="hideTip">
      <div class="term-tip-head"><span class="term-tip-name">{{ tooltip.term }}</span><a v-if="tooltip.href" class="term-tip-link" :href="tooltip.href">详情</a></div>
      <p class="term-tip-desc">{{ tooltip.desc }}</p>
    </div>
  </Teleport>
</template>

<style>
.term-hover { border-bottom: 1px dashed var(--vp-c-brand); cursor: help; padding: 0 1px; transition: background 0.15s; }
.term-hover:hover { background: var(--vp-c-brand-soft); }
.term-tip { position: fixed; transform: translateX(-50%); z-index: 1200; width: 280px; max-width: calc(100vw - 40px); background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); border-radius: 8px; box-shadow: 0 6px 24px rgba(0,0,0,0.14); padding: 10px 12px; pointer-events: auto; }
.term-tip-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.term-tip-name { font-size: 14px; font-weight: 600; color: var(--vp-c-text-1); }
.term-tip-link { font-size: 12px; color: var(--vp-c-brand); text-decoration: none; }
.term-tip-desc { margin: 0; font-size: 12.5px; line-height: 1.6; color: var(--vp-c-text-2); }
</style>
```

## §15 docs/.vitepress/theme/HighlightLayer.vue
```vue
<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vitepress'
const ROOT_SELECTOR = '.VPDoc'
const STORAGE_PREFIX = 'kb-hl:'
const route = useRoute()
const btnVisible = ref(false)
const btnPos = ref({ left: 0, top: 0 })
const count = ref(0)
let root = null
function storageKey() { return STORAGE_PREFIX + location.pathname }
function loadRecords() { try { const a = JSON.parse(localStorage.getItem(storageKey()) || '[]'); return Array.isArray(a) ? a : [] } catch { return [] } }
function saveRecords(r) { try { localStorage.setItem(storageKey(), JSON.stringify(r)) } catch {} }
function getRoot() { if (!root) root = document.querySelector(ROOT_SELECTOR); return root }
function pathOf(node) { const r = getRoot(); const path = []; let cur = node; while (cur && cur !== r) { path.unshift(Array.prototype.indexOf.call(cur.parentNode.childNodes, cur)); cur = cur.parentNode } return path }
function nodeFromPath(path) { const r = getRoot(); let cur = r; for (const idx of path) { if (!cur || !cur.childNodes) return null; cur = cur.childNodes[idx]; if (!cur) return null } return cur }
function firstTextNode(node) { if (node.nodeType === Node.TEXT_NODE) return node; return document.createTreeWalker(node, NodeFilter.SHOW_TEXT).nextNode() }
function lastTextNode(node) { if (node.nodeType === Node.TEXT_NODE) return node; const tw = document.createTreeWalker(node, NodeFilter.SHOW_TEXT); let last = null, n; while ((n = tw.nextNode())) last = n; return last }
function toTextBoundary(container, offset, isStart) {
  if (container.nodeType === Node.TEXT_NODE) return { node: container, offset: Math.max(0, Math.min(offset, container.length)) }
  const idx = isStart ? offset : Math.max(0, offset - 1)
  const child = container.childNodes[idx] || container
  if (child.nodeType === Node.TEXT_NODE) return isStart ? { node: child, offset: 0 } : { node: child, offset: child.length }
  const tn = isStart ? firstTextNode(child) : lastTextNode(child)
  if (tn) return { node: tn, offset: isStart ? 0 : tn.length }
  const fb = isStart ? firstTextNode(container) : lastTextNode(container)
  return fb ? { node: fb, offset: isStart ? 0 : fb.length } : null
}
function buildRange(sn, so, en, eo) { const r = document.createRange(); const s = toTextBoundary(sn, so, true), e = toTextBoundary(en, eo, false); if (!s || !e) return null; r.setStart(s.node, s.offset); r.setEnd(e.node, e.offset); return r }
function wrapRange(range) { const mark = document.createElement('mark'); mark.className = 'kb-hl'; try { range.surroundContents(mark) } catch { const f = range.extractContents(); mark.appendChild(f); range.insertNode(mark) } return mark }
function comparePaths(a, b) { const len = Math.min(a.length, b.length); for (let i = 0; i < len; i++) { if (a[i] !== b[i]) return a[i] - b[i] } return a.length - b.length }
function hideButton() { btnVisible.value = false }
function clearSelection() { const sel = window.getSelection(); if (sel) sel.removeAllRanges(); hideButton() }
function isInsideDoc(container) { const r = getRoot(); return !!r && r.contains(container) }
function onMouseUp() {
  const r = getRoot(); if (!r) return
  const sel = window.getSelection()
  if (!sel || sel.rangeCount === 0 || sel.isCollapsed) { hideButton(); return }
  const range = sel.getRangeAt(0)
  if (!isInsideDoc(range.startContainer) || !isInsideDoc(range.endContainer)) { hideButton(); return }
  if (!range.toString().trim()) { hideButton(); return }
  const rect = range.getBoundingClientRect()
  if (!rect || (rect.width === 0 && rect.height === 0)) { hideButton(); return }
  let top = rect.top - 38; if (top < 8) top = rect.bottom + 8
  btnPos.value = { left: Math.min(Math.max(rect.left, 8), window.innerWidth - 90), top }
  btnVisible.value = true
}
function onSelectionChange() { const sel = window.getSelection(); if (!sel || sel.isCollapsed || sel.rangeCount === 0) hideButton() }
function onHighlightClick() {
  const r = getRoot(); const sel = window.getSelection()
  if (!r || !sel || sel.rangeCount === 0) return
  const range = sel.getRangeAt(0)
  if (!isInsideDoc(range.startContainer) || !isInsideDoc(range.endContainer)) return
  const marks = r.querySelectorAll('mark.kb-hl')
  for (const m of marks) { if (range.intersectsNode(m)) { clearSelection(); return } }
  const start = toTextBoundary(range.startContainer, range.startOffset, true)
  const end = toTextBoundary(range.endContainer, range.endOffset, false)
  if (!start || !end) return
  const rec = { path: pathOf(start.node), start: start.offset, end: end.offset }
  if (end.node !== start.node) rec.endPath = pathOf(end.node)
  wrapRange(buildRange(start.node, start.offset, end.node, end.offset))
  const records = loadRecords(); records.push(rec); records.sort((a, b) => comparePaths(a.path, b.path)); saveRecords(records); count.value = records.length; clearSelection()
}
function resolveRecord(rec) { const startNode = nodeFromPath(rec.path); if (!startNode) return null; const endNode = rec.endPath ? nodeFromPath(rec.endPath) : startNode; if (!endNode) return null; const range = buildRange(startNode, rec.start, endNode, rec.end); if (!range || range.collapsed) return null; return range }
function isInsideMark(node) { if (node.nodeType === Node.TEXT_NODE) return !!(node.parentElement && node.parentElement.closest('mark.kb-hl')); if (node.nodeType === Node.ELEMENT_NODE) return !!node.closest('mark.kb-hl'); return false }
function restore() {
  const r = getRoot(); if (!r || r.querySelector('mark.kb-hl')) return
  const records = loadRecords(); const kept = []
  for (const rec of records) { const range = resolveRecord(rec); if (!range || isInsideMark(range.startContainer)) continue; wrapRange(range); kept.push(rec) }
  if (kept.length !== records.length) saveRecords(kept)
  count.value = kept.length
}
function restoreWithRetry(attempt = 0) { if (!document.querySelector(ROOT_SELECTOR) && attempt < 5) { setTimeout(() => restoreWithRetry(attempt + 1), 200); return } restore() }
function onDocumentClick(e) { hideButton(); const r = getRoot(); const target = e.target; if (!r || !target || typeof target.closest !== 'function') return; const mark = target.closest('mark.kb-hl'); if (!mark || !r.contains(mark)) return; removeMark(mark) }
function adjustPath(path, parentPath, slotIdx, extra) { if (path.length <= parentPath.length) return; for (let i = 0; i < parentPath.length; i++) { if (path[i] !== parentPath[i]) return } if (path[parentPath.length] > slotIdx) path[parentPath.length] += extra }
function removeMark(mark) {
  const r = getRoot(); const records = loadRecords()
  const marks = Array.prototype.slice.call(r.querySelectorAll('mark.kb-hl'))
  const idx = marks.indexOf(mark)
  if (idx === -1 || idx >= records.length) return
  const parent = mark.parentNode; const extra = mark.childNodes.length - 1
  if (extra !== 0) { const parentPath = pathOf(parent); const slotIdx = Array.prototype.indexOf.call(parent.childNodes, mark); for (const rec of records) { adjustPath(rec.path, parentPath, slotIdx, extra); if (rec.endPath) adjustPath(rec.endPath, parentPath, slotIdx, extra) } }
  while (mark.firstChild) parent.insertBefore(mark.firstChild, mark)
  parent.removeChild(mark); records.splice(idx, 1); saveRecords(records); count.value = records.length
}
function clearAll() { const r = getRoot(); if (!r) return; r.querySelectorAll('mark.kb-hl').forEach((m) => { const p = m.parentNode; while (m.firstChild) p.insertBefore(m.firstChild, m); p.removeChild(m) }); localStorage.removeItem(storageKey()); count.value = 0 }
onMounted(() => { document.addEventListener('mouseup', onMouseUp); document.addEventListener('click', onDocumentClick, true); document.addEventListener('selectionchange', onSelectionChange); window.addEventListener('scroll', hideButton, true); restoreWithRetry() })
watch(() => route.path, () => { root = null; hideButton(); count.value = 0; restoreWithRetry() }, { flush: 'post' })
onBeforeUnmount(() => { document.removeEventListener('mouseup', onMouseUp); document.removeEventListener('click', onDocumentClick, true); document.removeEventListener('selectionchange', onSelectionChange); window.removeEventListener('scroll', hideButton, true) })
</script>

<template>
  <Teleport to="body">
    <button v-if="btnVisible" class="kb-hl-btn" :style="{ left: btnPos.left + 'px', top: btnPos.top + 'px' }" @mousedown.prevent @click="onHighlightClick">高亮</button>
    <button v-if="count > 0" class="kb-hl-clear" title="清除本页高亮" @click="clearAll">清除本页高亮</button>
  </Teleport>
</template>

<style>
mark.kb-hl { background: rgba(255,213,0,0.4); border-radius: 2px; cursor: pointer; color: inherit; }
.kb-hl-btn { position: fixed; z-index: 1000; background: #fff; border: 1px solid #ccc; border-radius: 6px; padding: 4px 10px; font-size: 13px; line-height: 1.4; color: #333; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.15); user-select: none; }
.kb-hl-btn:hover { background: #f5f5f5; }
.kb-hl-clear { position: fixed; top: 72px; right: 16px; z-index: 1000; background: transparent; border: 1px solid transparent; border-radius: 4px; padding: 2px 8px; font-size: 12px; color: #999; cursor: pointer; opacity: 0.45; transition: opacity 0.2s; }
.kb-hl-clear:hover { opacity: 1; color: #666; border-color: #ddd; background: rgba(255,255,255,0.6); }
.dark .kb-hl-btn { background: #2b2b2b; border-color: #555; color: #eee; }
.dark .kb-hl-btn:hover { background: #333; }
.dark .kb-hl-clear { color: #777; }
.dark .kb-hl-clear:hover { color: #bbb; border-color: #444; background: rgba(0,0,0,0.3); }
</style>

## §16 docs/.vitepress/theme/exam/ExamPage.vue
```vue
<script setup>
import { ref, onMounted, computed } from 'vue'
import { useExam } from './useExam'
import QuestionCard from './QuestionCard.vue'
import AnswerSheet from './AnswerSheet.vue'

const realQuestions = ref([])
const mockQuestions = ref([])
const loadError = ref('')
const exam = useExam(realQuestions, mockQuestions)
const activeSource = ref('real')
const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

onMounted(async () => {
  try {
    const [realRes, mockRes] = await Promise.all([fetch('/quiz-data.json'), fetch('/quiz-mock.json')])
    if (!realRes.ok || !mockRes.ok) throw new Error('bad status')
    const realData = await realRes.json()
    const mockData = await mockRes.json()
    if (!realData?.questions || !mockData?.questions) throw new Error('bad payload')
    realQuestions.value = realData.questions.map((q) => ({ ...q, source: 'real' }))
    mockQuestions.value = mockData.questions.map((q) => ({ ...q, source: 'mock' }))
  } catch { loadError.value = '题库加载失败，请刷新重试' }
})

function startExam(source) { activeSource.value = source; if (!exam.start(source)) alert('当前题库暂无可用题目') }
function fmtAnswer(idxArr) { return idxArr.map((i) => LETTERS[i]).join(',') || '未作答' }
function sectionTitle(i) { if (i < 30) return '一、单项选择题'; if (i < 40) return '二、多项选择题'; return '三、判断题' }
const wrongTotal = computed(() => exam.wrongCount())
const reviewItem = computed(() => {
  const q = exam.paper.value[exam.reviewIndex.value]
  if (!q) return null
  const texts = q.myAnswerTexts || []
  const myIdx = q.options.map((o) => o.text).map((t, i) => (texts.includes(t) ? i : -1)).filter((i) => i >= 0).sort((a, b) => a - b)
  const correct = myIdx.length === q.answerIdx.length && myIdx.every((v, i) => v === q.answerIdx[i])
  return { q, myIdx, correct }
})
function removeCurrentWrong() { const q = exam.paper.value[exam.reviewIndex.value]; if (!q) return; exam.removeWrong(q.id, q.source); exam.startReview(); exam.reviewIndex.value = 0 }
</script>

<template>
  <div class="exam">
    <p v-if="loadError" class="exam-error">{{ loadError }}</p>
    <div v-else-if="exam.phase.value === 'start'" class="exam-start">
      <h2>模拟考试</h2>
      <div class="exam-start-cards">
        <div class="exam-entry-card"><h3>真题练习</h3><p>从真题题库随机组卷 60 题，按官方结构（单选 30 + 多选 10 + 判断 20）与模块占比抽取，选项顺序随机。</p>
          <button class="eq-btn eq-btn-primary" @click="startExam('real')">开始真题练习</button></div>
        <div class="exam-entry-card"><h3>模拟练习</h3><p>从模拟题库随机组卷，覆盖相同知识点与模块配比，与真题题库完全隔离。</p>
          <button class="eq-btn eq-btn-primary" @click="startExam('mock')">开始模拟练习</button></div>
        <div class="exam-entry-card"><h3>错题本</h3><p>答错的题自动收录于此，含解析与正确答案，可回顾或重练。当前错题：<strong>{{ wrongTotal }}</strong> 题。</p>
          <div class="exam-entry-actions">
            <button class="eq-btn" :disabled="wrongTotal === 0" @click="exam.startReview()">回顾错题</button>
            <button class="eq-btn" :disabled="wrongTotal === 0" @click="startExam('wrong')">重练错题</button>
            <button class="eq-btn eq-btn-danger" :disabled="wrongTotal === 0" @click="exam.clearWrongs()">清空错题</button>
          </div></div>
      </div>
      <p class="exam-start-note">考试不限时。答题阶段不显示答案与解析，提交后打分，之后可逐题查看解析。</p>
    </div>

    <div v-else-if="exam.phase.value === 'exam'" class="exam-body">
      <div class="exam-main">
        <div class="exam-source-tag">{{ activeSource === 'mock' ? '模拟练习' : activeSource === 'wrong' ? '错题重练' : '真题练习' }}</div>
        <QuestionCard :question="exam.currentQuestion.value" :selected="exam.answers.value[exam.current.value] || []" :interactive="true" @select="exam.toggleOption" />
        <div class="exam-nav">
          <button class="eq-btn" :disabled="exam.current.value === 0" @click="exam.current.value--">上一题</button>
          <span class="exam-progress">{{ exam.current.value + 1 }} / {{ exam.total.value }}</span>
          <button class="eq-btn" :disabled="exam.current.value >= exam.total.value - 1" @click="exam.current.value++">下一题</button>
          <button class="eq-btn eq-btn-primary" @click="exam.confirmVisible.value = true">提交试卷</button>
        </div>
      </div>
      <aside class="exam-side"><AnswerSheet :total="exam.total.value" :answers="exam.answers.value" :current="exam.current.value" @jump="(i) => (exam.current.value = i)" /></aside>
    </div>

    <div v-else-if="exam.phase.value === 'result'" class="exam-result">
      <div class="exam-result-score"><span class="exam-score-num">{{ exam.score.value }}</span><span class="exam-score-total">/ {{ exam.total.value }}</span></div>
      <div class="exam-result-stats"><span>答对 {{ exam.score.value }} 题</span><span>答错 {{ exam.wrongCountInExam.value }} 题</span><span>未答 {{ exam.total.value - exam.answeredCount.value }} 题</span></div>
      <div class="exam-result-actions">
        <button class="eq-btn eq-btn-primary" @click="exam.gotoReview(0)">查看解析</button>
        <button class="eq-btn" :disabled="wrongTotal === 0" @click="startExam('wrong')">错题重练（{{ wrongTotal }}）</button>
        <button class="eq-btn" @click="exam.restart()">返回</button>
      </div>
    </div>

    <div v-else-if="exam.phase.value === 'review' && !reviewItem?.q?.myAnswerTexts" class="exam-review">
      <div class="exam-review-head"><span class="exam-review-section">{{ sectionTitle(exam.reviewIndex.value) }}</span><span class="exam-review-counter">{{ exam.reviewIndex.value + 1 }} / {{ exam.total.value }}</span></div>
      <QuestionCard :question="exam.results.value[exam.reviewIndex.value].q" :selected="exam.results.value[exam.reviewIndex.value].answer" :show-result="true" :correct="exam.results.value[exam.reviewIndex.value].correct" />
      <div class="exam-analysis">
        <p><strong>我的答案：</strong>{{ fmtAnswer(exam.results.value[exam.reviewIndex.value].answer) }}</p>
        <p><strong>正确答案：</strong>{{ fmtAnswer(exam.results.value[exam.reviewIndex.value].q.answerIdx) }}<a class="exam-link" :href="exam.results.value[exam.reviewIndex.value].q.chapter" target="_blank">查看考点</a></p>
        <div class="exam-analysis-text">{{ exam.results.value[exam.reviewIndex.value].q.explanation }}</div>
      </div>
      <div class="exam-nav">
        <button class="eq-btn" :disabled="exam.reviewIndex.value === 0" @click="exam.reviewIndex.value--">上一题</button>
        <button class="eq-btn" :disabled="exam.reviewIndex.value >= exam.total.value - 1" @click="exam.reviewIndex.value++">下一题</button>
        <button class="eq-btn eq-btn-primary" @click="exam.restart()">返回</button>
      </div>
    </div>

    <div v-else-if="exam.phase.value === 'review' && reviewItem" class="exam-review">
      <div class="exam-review-head"><span class="exam-review-section">错题回顾</span><span class="exam-review-counter">{{ exam.reviewIndex.value + 1 }} / {{ exam.total.value }}</span></div>
      <QuestionCard :question="reviewItem.q" :selected="reviewItem.myIdx" :show-result="true" :correct="reviewItem.correct" />
      <div class="exam-analysis">
        <p><strong>我的答案：</strong>{{ fmtAnswer(reviewItem.myIdx) }}<span :class="reviewItem.correct ? 'exam-mark-good' : 'exam-mark-bad'">{{ reviewItem.correct ? '（已掌握）' : '（答错）' }}</span></p>
        <p><strong>正确答案：</strong>{{ fmtAnswer(reviewItem.q.answerIdx) }}<a class="exam-link" :href="reviewItem.q.chapter" target="_blank">查看考点</a></p>
        <div class="exam-analysis-text">{{ reviewItem.q.explanation }}</div>
      </div>
      <div class="exam-nav">
        <button class="eq-btn" :disabled="exam.reviewIndex.value === 0" @click="exam.reviewIndex.value--">上一题</button>
        <button class="eq-btn" :disabled="exam.reviewIndex.value >= exam.total.value - 1" @click="exam.reviewIndex.value++">下一题</button>
        <button class="eq-btn eq-btn-danger" @click="removeCurrentWrong">移出本错题</button>
        <button class="eq-btn eq-btn-primary" @click="exam.restart()">返回</button>
      </div>
      <aside class="exam-side-review"><AnswerSheet :total="exam.total.value" :answers="exam.answers.value" :current="exam.reviewIndex.value" :review="true" @jump="(i) => (exam.reviewIndex.value = i)" /></aside>
    </div>

    <Teleport to="body">
      <div v-if="exam.confirmVisible.value" class="exam-mask" @click.self="exam.confirmVisible.value = false">
        <div class="exam-dialog">
          <h3>确认交卷？</h3>
          <p>已答 <strong>{{ exam.answeredCount.value }}</strong> 题，未答 <strong>{{ exam.total.value - exam.answeredCount.value }}</strong> 题。</p>
          <p class="exam-dialog-tip">交卷后无法修改答案，将立即评分，答错的题会自动进入错题本。</p>
          <div class="exam-dialog-actions"><button class="eq-btn" @click="exam.confirmVisible.value = false">继续作答</button><button class="eq-btn eq-btn-primary" @click="exam.submit()">确认交卷</button></div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.exam { min-height: 60vh; }
.exam-error { color: #ef4444; text-align: center; padding: 60px 0; }
.exam-start { max-width: 860px; margin: 0 auto; padding: 20px 0 60px; text-align: center; }
.exam-start h2 { font-size: 24px; margin-bottom: 20px; }
.exam-start-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; text-align: left; }
.exam-entry-card { background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); border-radius: 12px; padding: 20px 22px; display: flex; flex-direction: column; gap: 10px; }
.exam-entry-card h3 { margin: 0; font-size: 17px; }
.exam-entry-card p { margin: 0; font-size: 13px; line-height: 1.7; color: var(--vp-c-text-2); flex: 1; }
.exam-entry-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.exam-start-note { margin-top: 20px; font-size: 13px; color: var(--vp-c-text-3); }
.exam-body { display: flex; gap: 24px; align-items: flex-start; }
.exam-main { flex: 1; min-width: 0; }
.exam-side { width: 260px; flex-shrink: 0; position: sticky; top: 90px; }
.exam-side-review { margin-top: 18px; max-width: 360px; }
.exam-source-tag { display: inline-block; font-size: 12px; color: var(--vp-c-brand); background: var(--vp-c-brand-soft); border-radius: 10px; padding: 2px 12px; margin-bottom: 10px; }
.exam-nav { display: flex; align-items: center; gap: 10px; margin-top: 20px; flex-wrap: wrap; }
.exam-progress { color: var(--vp-c-text-2); font-size: 13px; }
.exam-result { text-align: center; padding: 60px 0; }
.exam-result-score { font-size: 72px; font-weight: 700; color: var(--vp-c-brand); line-height: 1; }
.exam-score-total { font-size: 24px; color: var(--vp-c-text-3); font-weight: 400; }
.exam-result-stats { display: flex; justify-content: center; gap: 30px; margin: 20px 0 30px; color: var(--vp-c-text-2); }
.exam-result-actions { display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; }
.exam-review-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.exam-review-section { font-weight: 600; color: var(--vp-c-text-1); }
.exam-review-counter { color: var(--vp-c-text-3); font-size: 13px; }
.exam-analysis { margin-top: 18px; background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); border-radius: 10px; padding: 16px 18px; font-size: 14px; line-height: 1.8; color: var(--vp-c-text-1); }
.exam-analysis-text { margin-top: 8px; padding-top: 8px; border-top: 1px dashed var(--vp-c-divider); color: var(--vp-c-text-2); }
.exam-link { margin-left: 12px; color: var(--vp-c-brand); font-size: 13px; text-decoration: none; }
.exam-mark-good { color: #22c55e; font-size: 12px; margin-left: 6px; }
.exam-mark-bad { color: #ef4444; font-size: 12px; margin-left: 6px; }
.exam-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.45); z-index: 999; display: flex; align-items: center; justify-content: center; }
.exam-dialog { background: var(--vp-c-bg); border-radius: 12px; padding: 26px 30px; width: 420px; max-width: calc(100vw - 40px); color: var(--vp-c-text-1); }
.exam-dialog h3 { margin: 0 0 12px; }
.exam-dialog-tip { color: var(--vp-c-text-3); font-size: 13px; }
.exam-dialog-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.eq-btn { padding: 8px 18px; border: 1px solid var(--vp-c-divider); border-radius: 8px; background: var(--vp-c-bg); color: var(--vp-c-text-1); font-size: 14px; cursor: pointer; transition: all 0.15s; }
.eq-btn:hover:not(:disabled) { border-color: var(--vp-c-brand); color: var(--vp-c-brand); }
.eq-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.eq-btn-primary { background: var(--vp-c-brand); border-color: var(--vp-c-brand); color: #fff; }
.eq-btn-primary:hover:not(:disabled) { background: var(--vp-c-brand-2); color: #fff; }
.eq-btn-danger { border-color: #ef4444; color: #ef4444; }
.eq-btn-danger:hover:not(:disabled) { background: rgba(239,68,68,0.1); color: #ef4444; }
@media (max-width: 900px) { .exam-body { flex-direction: column-reverse; } .exam-side { width: 100%; position: static; } }
</style>
```

## §17 docs/.vitepress/theme/exam/useExam.js
```js
import { ref, computed } from 'vue'

const EXAM_STRUCTURE = [
  { type: 'single', label: '单项选择题', count: 30 },
  { type: 'multi', label: '多项选择题', count: 10 },
  { type: 'judge', label: '判断题', count: 20 },
]
const MODULE_ORDER = ['ai', 'os', 'software', 'agent', 'hardware']
const MODULE_RATIO = { ai: 0.3, os: 0.2, software: 0.2, agent: 0.2, hardware: 0.1 }
const WRONGS_KEY = 'exam-wrongs'

function shuffle(arr) { const a = [...arr]; for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]] } return a }
function draw(questions, count, ratioMap) {
  const byModule = {}
  for (const q of questions) { if (!byModule[q.module]) byModule[q.module] = []; byModule[q.module].push(q) }
  const drawn = []; const rest = [...questions]; const expected = {}; let assigned = 0
  MODULE_ORDER.forEach((m, i) => { if (i === MODULE_ORDER.length - 1) expected[m] = count - assigned; else { expected[m] = Math.round(count * (ratioMap[m] || 0)); assigned += expected[m] } })
  for (const m of MODULE_ORDER) { const pool = byModule[m] || []; const take = Math.min(expected[m] || 0, pool.length); const picked = shuffle(pool).slice(0, take); drawn.push(...picked); picked.forEach((q) => { const idx = rest.findIndex((r) => r.id === q.id); if (idx >= 0) rest.splice(idx, 1) }) }
  if (drawn.length < count) drawn.push(...shuffle(rest).slice(0, count - drawn.length))
  return drawn
}
function shuffleOptions(q) {
  const order = shuffle(q.options.map((_, i) => i))
  const newOptions = order.map((i) => q.options[i])
  const answerIdx = q.answerKeys.map((k) => q.options.findIndex((o) => o.key === k)).filter((i) => i >= 0).map((oldIdx) => order.indexOf(oldIdx)).sort((a, b) => a - b)
  return { options: newOptions, answerIdx }
}

export function useExam(realRef, mockRef) {
  const phase = ref('start')
  const paper = ref([])
  const answers = ref([])
  const current = ref(0)
  const results = ref([])
  const confirmVisible = ref(false)
  const reviewIndex = ref(0)
  const examSeq = ref(0)
  const currentQuestion = computed(() => paper.value[current.value] || null)
  const total = computed(() => paper.value.length)
  const answeredCount = computed(() => answers.value.filter((a) => a && a.length > 0).length)

  function loadWrongsRaw() { try { return JSON.parse(localStorage.getItem(WRONGS_KEY)) || [] } catch { return [] } }
  function saveWrongs(list) { localStorage.setItem(WRONGS_KEY, JSON.stringify(list)) }
  function findQuestion(id, source) { const pool = source === 'mock' ? mockRef.value : realRef.value; return pool.find((q) => q.id === id) || null }
  function wrongCount() { return loadWrongsRaw().length }
  function recordWrongs(result) {
    const wrongs = loadWrongsRaw()
    for (const r of result) {
      if (r.correct) continue
      const myTexts = (r.answer || []).map((i) => r.q.options[i].text)
      const existing = wrongs.find((w) => w.id === r.q.id && w.source === (r.q.source || 'real'))
      if (existing) { existing.myAnswer = myTexts; existing.at = Date.now() } else wrongs.push({ id: r.q.id, source: r.q.source || 'real', myAnswer: myTexts, at: Date.now() })
    }
    saveWrongs(wrongs)
  }
  function wrongList() { return loadWrongsRaw().map((w) => ({ ...w, q: findQuestion(w.id, w.source) })).filter((x) => x.q) }
  function removeWrong(id, source) { const wrongs = loadWrongsRaw().filter((w) => !(w.id === id && w.source === source)); saveWrongs(wrongs) }
  function clearWrongs() { saveWrongs([]) }

  function buildPaper(pool) { return pool.map((q) => { const { options, answerIdx } = shuffleOptions(q); return { id: q.id, type: q.type, module: q.module, stem: q.stem, options, answerIdx, explanation: q.explanation, chapter: q.chapter, source: q.source || 'real' } }) }
  function start(source) {
    let pool
    if (source === 'wrong') { pool = wrongList().map((x) => x.q); if (pool.length === 0) return false }
    else pool = (source === 'mock' ? mockRef.value : realRef.value) || []
    const picked = []
    for (const s of EXAM_STRUCTURE) { const typePool = pool.filter((q) => q.type === s.type); picked.push(...draw(typePool, s.count, MODULE_RATIO)) }
    paper.value = buildPaper(picked); answers.value = paper.value.map(() => []); current.value = 0; results.value = []; examSeq.value++; phase.value = 'exam'; return true
  }
  function startReview() {
    const list = wrongList()
    if (list.length === 0) return false
    paper.value = list.map((x) => ({ ...x.q, myAnswerTexts: x.myAnswer || [], source: x.source }))
    answers.value = paper.value.map(() => []); current.value = 0; results.value = []; examSeq.value++; phase.value = 'review'; return true
  }
  function toggleOption(optIndex) {
    if (phase.value !== 'exam') return
    const q = paper.value[current.value]
    if (!q) return
    const set = new Set(answers.value[current.value])
    if (q.type === 'single' || q.type === 'judge') { set.clear(); set.add(optIndex) } else { if (set.has(optIndex)) set.delete(optIndex); else set.add(optIndex) }
    answers.value[current.value] = [...set].sort((a, b) => a - b)
  }
  function isAnswered(i) { return answers.value[i] && answers.value[i].length > 0 }
  function isCorrect(q, ans) { if (!ans || ans.length === 0) return false; return ans.length === q.answerIdx.length && ans.every((v, i) => v === q.answerIdx[i]) }
  function submit() { const result = paper.value.map((q, i) => ({ q, answer: answers.value[i] || [], correct: isCorrect(q, answers.value[i]) })); results.value = result; recordWrongs(result); phase.value = 'result' }
  const score = computed(() => results.value.filter((r) => r.correct).length)
  const wrongCountInExam = computed(() => results.value.filter((r) => !r.correct).length)
  function gotoReview(i) { reviewIndex.value = i; phase.value = 'review' }
  function restart() { phase.value = 'start' }

  return { phase, paper, answers, current, results, confirmVisible, reviewIndex, examSeq, currentQuestion, total, answeredCount, score, wrongCountInExam, wrongCount, wrongList, removeWrong, clearWrongs, start, startReview, toggleOption, isAnswered, submit, gotoReview, restart }
}

## §18 docs/.vitepress/theme/exam/QuestionCard.vue
```vue
<script setup>
import { computed } from 'vue'
const props = defineProps({ question: { type: Object, required: true }, selected: { type: Array, default: () => [] }, interactive: { type: Boolean, default: false }, showResult: { type: Boolean, default: false }, correct: { type: Boolean, default: false } })
const TYPE_LABEL = { single: '单选题', multi: '多选题', judge: '判断题' }
const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']
const selectedSet = computed(() => new Set(props.selected))
function optionClass(i) {
  const cls = ['eq-option']
  if (props.interactive && selectedSet.value.has(i)) cls.push('eq-selected')
  if (props.showResult) { if (props.question.answerIdx.includes(i)) cls.push('eq-right'); else if (selectedSet.value.has(i)) cls.push('eq-wrong') }
  return cls
}
</script>

<template>
  <div class="eq-question">
    <div class="eq-head">
      <span class="eq-type" :class="'eq-type-' + question.type">{{ TYPE_LABEL[question.type] }}</span>
      <span class="eq-module">{{ question.module }}</span>
      <span v-if="showResult" class="eq-mark" :class="correct ? 'eq-mark-right' : 'eq-mark-wrong'">{{ correct ? '正确' : '错误' }}</span>
    </div>
    <div class="eq-stem">{{ question.stem }}</div>
    <div class="eq-options">
      <button v-for="(opt, i) in question.options" :key="i" class="eq-option" :class="optionClass(i)" :disabled="!interactive" @click="$emit('select', i)">
        <span class="eq-letter">{{ LETTERS[i] }}</span><span class="eq-text">{{ opt.text }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.eq-question { padding: 4px 0; }
.eq-head { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.eq-type { font-size: 12px; padding: 2px 10px; border-radius: 10px; color: #fff; }
.eq-type-single { background: #3b82f6; }
.eq-type-multi { background: #8b5cf6; }
.eq-type-judge { background: #10b981; }
.eq-module { font-size: 12px; color: var(--vp-c-text-3); background: var(--vp-c-bg-alt); padding: 2px 10px; border-radius: 10px; }
.eq-mark { font-size: 13px; font-weight: 600; }
.eq-mark-right { color: #22c55e; }
.eq-mark-wrong { color: #ef4444; }
.eq-stem { font-size: 15px; line-height: 1.7; color: var(--vp-c-text-1); margin-bottom: 16px; }
.eq-options { display: flex; flex-direction: column; gap: 8px; }
.eq-option { display: flex; align-items: flex-start; gap: 10px; text-align: left; padding: 10px 14px; border: 1px solid var(--vp-c-divider); border-radius: 8px; background: var(--vp-c-bg); color: var(--vp-c-text-1); font-size: 14px; line-height: 1.6; cursor: pointer; transition: border-color 0.15s, background 0.15s; }
.eq-option:hover:not(:disabled) { border-color: var(--vp-c-brand); }
.eq-option:disabled { cursor: default; }
.eq-letter { font-weight: 600; color: var(--vp-c-brand); flex-shrink: 0; }
.eq-selected { border-color: var(--vp-c-brand); background: var(--vp-c-brand-soft); }
.eq-right { border-color: #22c55e; background: rgba(34,197,94,0.12); }
.eq-right .eq-letter { color: #22c55e; }
.eq-wrong { border-color: #ef4444; background: rgba(239,68,68,0.1); }
.eq-wrong .eq-letter { color: #ef4444; }
</style>
```

## §19 docs/.vitepress/theme/exam/AnswerSheet.vue
```vue
<script setup>
defineProps({ total: { type: Number, required: true }, answers: { type: Array, required: true }, current: { type: Number, required: true }, review: { type: Boolean, default: false } })
const emit = defineEmits(['jump'])
</script>

<template>
  <div class="eq-sheet">
    <div class="eq-sheet-title">{{ review ? '错题导览' : '答题卡' }}</div>
    <div class="eq-sheet-grid">
      <button v-for="i in total" :key="i" class="eq-cell" :class="{ 'eq-cell-wrong': review, 'eq-cell-done': !review && answers[i - 1] && answers[i - 1].length > 0, 'eq-cell-current': current === i - 1 }" @click="emit('jump', i - 1)">{{ i }}</button>
    </div>
    <div v-if="review" class="eq-legend"><span><i class="eq-dot eq-dot-wrong"></i>错题</span><span><i class="eq-dot eq-dot-current"></i>当前</span></div>
    <div v-else class="eq-legend"><span><i class="eq-dot eq-dot-done"></i>已答</span><span><i class="eq-dot"></i>未答</span><span><i class="eq-dot eq-dot-current"></i>当前</span></div>
  </div>
</template>

<style scoped>
.eq-sheet { background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); border-radius: 10px; padding: 14px; }
.eq-sheet-title { font-size: 13px; font-weight: 600; color: var(--vp-c-text-2); margin-bottom: 10px; }
.eq-sheet-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 6px; }
.eq-cell { height: 30px; border: 1px solid var(--vp-c-divider); border-radius: 6px; background: var(--vp-c-bg-alt); color: var(--vp-c-text-2); font-size: 12px; cursor: pointer; transition: all 0.15s; }
.eq-cell:hover { border-color: var(--vp-c-brand); }
.eq-cell-done { background: var(--vp-c-brand); border-color: var(--vp-c-brand); color: #fff; }
.eq-cell-wrong { background: #ef4444; border-color: #ef4444; color: #fff; }
.eq-cell-current { box-shadow: 0 0 0 2px var(--vp-c-brand); font-weight: 600; }
.eq-legend { display: flex; gap: 14px; margin-top: 12px; font-size: 12px; color: var(--vp-c-text-3); }
.eq-dot { display: inline-block; width: 10px; height: 10px; border-radius: 3px; background: var(--vp-c-bg-alt); border: 1px solid var(--vp-c-divider); margin-right: 4px; vertical-align: middle; }
.eq-dot-done { background: var(--vp-c-brand); border-color: var(--vp-c-brand); }
.eq-dot-wrong { background: #ef4444; border-color: #ef4444; }
.eq-dot-current { box-shadow: 0 0 0 2px var(--vp-c-brand); }
</style>
```

## §20 最小数据模板（docs/public/*.json）
`graph-data.json`：
```json
{
  "nodes": [
    { "id": "a", "name": "示例知识点A", "module": "ai", "chapter": "/ch01", "anchor": "_1-1-示例", "desc": "示例描述" }
  ],
  "edges": []
}
```
`quiz-data.json`（无真题时用空，考试页可加载）：
```json
{ "questions": [] }
```
`quiz-mock.json`（空题库；示例题见 `mcp/exam` 题干 schema）：
```json
{ "questions": [] }
```
`terms.json`（术语可空）：
```json
{ "terms": [] }
```

## §21 一键 npm 与常见坑
```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # 产物 docs/.vitepress/dist
```
- 若你在 `package.json` 里保留了 `predev`/`prebuild`，需要 `copy-docs.mjs`；不需要就删掉这两条脚本。
- 组件均为**客户端渲染**，`build` 只保证编译；`Mermaid`/`Pillars`/`SectionGraph`/`KnowledgeGraph`/`ExamPage` 的实际显示/交互需 `dev` 看。
- 数据缺一不可：`quiz-data`/`quiz-mock`/`graph-data`/`terms.json` 缺失对应页面/组件会报加载失败；用 §20 最小模板即可。
- 题库 schema：`{id,type(single|multi|judge),module,stem,options[{key,text}],answerKeys[],explanation,chapter,source}`；`source` 为 `real`/`mock`；题型格式对齐真题（single 4项/1正确、multi 6项/3~4正确、judge 2项正确/错误）。
- 组件用法：``<Mermaid chart="flowchart LR; A-->B" caption="..." />``、``<Pillars data='{"pillars":[{"title":"A","desc":"…"}]}' />``、``<Compare data='{"columns":["X","Y"],"rows":[{"dim":"d","cells":["a","b"]}]}' />``、``<Flux data='{"steps":[{"label":"s","desc":"…"}]}' />``、``<Layer data='{"sequence":"bottom-up","layers":[{"title":"L","items":["…"]}]}' />``、``<SectionGraph chapter="/ch04" />``。
- 公式：用 `$...$`/`$$...$$` 的 LaTeX，前端 KaTeX 渲染；`$` 前后留空格、勿紧贴汉字/数字。

```

```

```

```
