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
const card = ref(null)          // 右侧信息面板
const searchQ = ref('')         // 搜索关键词
const focusId = ref(null)       // 邻域聚焦的节点 id
const stats = ref({ nodes: 0, edges: 0 })

let chart = null
let allNodes = []
let allEdges = []
let selected = {}               // 图例显隐：moduleLabel -> true/false
let neighborMap = new Map()     // id -> Set(neighborId)
let themeObserver = null

function isDark() {
  return document.documentElement.classList.contains('dark')
}
function moduleOf(v) {
  return MODULES.find((m) => m.value === v)
}
function moduleColor(v) {
  const m = moduleOf(v)
  return m ? m.color : FALLBACK_COLOR
}
function moduleLabel(v) {
  const m = moduleOf(v)
  return m ? m.label : String(v == null ? '未知' : v)
}
function visibleModules() {
  return new Set(Object.keys(selected).filter((k) => selected[k]))
}

// 构建 id -> 邻居集合
function buildNeighbors() {
  neighborMap = new Map()
  for (const n of allNodes) neighborMap.set(n.id, new Set())
  for (const e of allEdges) {
    if (!neighborMap.has(e.source) || !neighborMap.has(e.target)) continue
    neighborMap.get(e.source).add(e.target)
    neighborMap.get(e.target).add(e.source)
  }
}
function neighborsOf(id) {
  return neighborMap.get(id) || new Set()
}

// 节点是否被搜索命中
function matchesQuery(n) {
  if (!searchQ.value.trim()) return null   // null = 无搜索，不区分
  const q = searchQ.value.trim().toLowerCase()
  const hay = [n.id, n.name || '', n.desc || ''].join(' ').toLowerCase()
  return hay.includes(q)
}

function buildOption() {
  const dark = isDark()
  const nodeColor = dark ? '#ccc' : '#333'
  const edgeColor = dark ? '#8a8a8a' : '#999'
  const activeMods = visibleModules()
  const focus = focusId.value
  const focusSet = focus ? new Set([focus, ...neighborsOf(focus)]) : null
  const focusedNeighbor = focus ? neighborsOf(focus) : null

  // 可见节点（按图例）
  const nodes = allNodes.filter((n) => activeMods.has(moduleLabel(n.module)))
  const nodeIds = new Set(nodes.map((n) => n.id))

  const nodeData = nodes.map((n) => {
    const style = { itemStyle: { color: moduleColor(n.module), opacity: 1 }, symbolSize: 36 }
    if (focusSet) {
      if (focusSet.has(n.id)) {
        style.itemStyle.opacity = 1
        if (n.id === focus) { style.symbolSize = 52; style.itemStyle.borderColor = moduleColor(n.module); style.itemStyle.borderWidth = 3 }
        else { style.symbolSize = 40; style.itemStyle.opacity = 0.95 }
      } else {
        style.itemStyle.opacity = 0.12
        style.symbolSize = 26
      }
    } else {
      const hit = matchesQuery(n)
      if (hit === true) {
        style.symbolSize = 46
        style.itemStyle.borderColor = moduleColor(n.module)
        style.itemStyle.borderWidth = 3
        style.itemStyle.opacity = 1
      } else if (hit === false) {
        style.itemStyle.opacity = 0.12
        style.symbolSize = 26
      }
    }
    return {
      name: n.id,
      displayName: n.name || n.id,
      module: n.module,
      desc: n.desc,
      chapter: n.chapter,
      anchor: n.anchor,
      focus: focus === n.id,
      symbolSize: style.symbolSize,
      itemStyle: style.itemStyle,
      label: {
        show: focusSet ? (focusSet.has(n.id)) : (matchesQuery(n) !== false),
        color: nodeColor, fontSize: 12,
      },
    }
  })

  const links = allEdges
    .filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))
    .map((e) => {
      const active = focusSet ? (focusSet.has(e.source) && focusSet.has(e.target)) : true
      return {
        source: e.source, target: e.target, relation: e.relation,
        lineStyle: { color: edgeColor, opacity: active ? 0.7 : 0.06, width: active ? 1.8 : 1 },
      }
    })

  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: dark ? '#1f1f1f' : '#fff',
      borderColor: dark ? '#444' : '#ddd',
      textStyle: { color: dark ? '#ccc' : '#333', fontSize: 12 },
    },
    legend: {
      top: 8,
      left: 'center',
      data: MODULES.map((m) => ({ name: m.label, icon: 'circle', itemStyle: { color: m.color } })),
      selected,
      textStyle: { color: nodeColor, fontSize: 12 },
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        force: { repulsion: 320, edgeLength: [80, 160], gravity: 0.08 },
        data: nodeData,
        links,
        label: { show: true, fontSize: 12, color: nodeColor },
        edgeLabel: { show: true, fontSize: 10, color: edgeColor, formatter: (p) => p.data.relation },
        lineStyle: { color: edgeColor, opacity: 0.6, width: 1.5 },
        emphasis: { focus: 'adjacency', scale: true },
        animationDuration: 500,
        animationDurationUpdate: 300,
        animationEasingUpdate: 'quinticInOut',
      },
    ],
  }
}

function update() {
  if (chart) chart.setOption(buildOption())
}

function onLegendChanged(params) {
  selected = { ...params.selected }
  update()
}

function onChartClick(params) {
  if (params && params.componentType === 'series' && params.dataType === 'node' && params.data) {
    setFocus(params.data.name)
  } else {
    clearFocus()          // 点空白：恢复全图并关闭面板
  }
}

function setFocus(id) {
  focusId.value = id
  const n = allNodes.find((x) => x.id === id)
  if (!n) return
  const rels = [...neighborsOf(id)].map((ne) => {
    const nn = allNodes.find((x) => x.id === ne)
    const edge = allEdges.find((e) =>
      (e.source === id && e.target === ne) || (e.source === ne && e.target === id))
    return { id: ne, name: nn ? (nn.name || nn.id) : ne, module: nn ? nn.module : '', relation: edge ? edge.relation : '' }
  })
  card.value = {
    id: n.id, name: n.name || n.id, module: n.module, desc: n.desc || '',
    chapter: n.chapter, anchor: n.anchor, rels,
  }
  update()
}

function clearFocus() {
  focusId.value = null
  card.value = null
  update()
}

function onClickRelation(relId) {
  setFocus(relId)
}

function onSearchInput() {
  focusId.value = null
  card.value = null
  update()
}

function onResize() {
  if (chart) chart.resize()
}

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
  } catch {
    errorMsg.value = '图谱数据加载失败'
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  if (themeObserver) themeObserver.disconnect()
  if (chart) { chart.dispose(); chart = null }
})
</script>

<template>
  <div class="kg-root">
    <!-- 顶部工具栏：统计 + 搜索 -->
    <div class="kg-toolbar">
      <span class="kg-stats">{{ statsText }}</span>
      <div class="kg-search">
        <input
          v-model="searchQ"
          class="kg-search-input"
          type="text"
          placeholder="搜索知识点 / 描述…"
          @input="onSearchInput"
        />
        <button v-if="searchQ" class="kg-search-clear" aria-label="清空搜索" @click="searchQ = ''; onSearchInput()">×</button>
      </div>
      <button
        v-if="focusId"
        class="kg-reset"
        @click="clearFocus"
      >重置视图</button>
    </div>

    <div
      v-show="!errorMsg"
      ref="chartEl"
      class="kg-chart"
      style="height: calc(100vh - 210px); width: 100%"
    ></div>
    <p v-if="errorMsg" class="kg-error">{{ errorMsg }}</p>

    <!-- 右侧信息面板 -->
    <Teleport to="body">
      <div v-if="card" class="kg-panel">
        <div class="kg-panel-head">
          <span class="kg-panel-title">{{ card.name }}</span>
          <button class="kg-panel-close" aria-label="关闭" @click="clearFocus">×</button>
        </div>
        <span class="kg-panel-module">{{ moduleLabel(card.module) }}</span>
        <p class="kg-panel-desc">{{ card.desc }}</p>
        <a
          v-if="card.anchor"
          class="kg-panel-link"
          :href="(card.chapter || '') + '#' + card.anchor"
          target="_blank"
        >查看详情</a>

        <div v-if="card.rels && card.rels.length" class="kg-panel-rels">
          <div class="kg-panel-rels-title">关联知识点（{{ card.rels.length }}）</div>
          <button
            v-for="r in card.rels"
            :key="r.id"
            class="kg-panel-rel"
            @click="onClickRelation(r.id)"
          >
            <span class="kg-panel-rel-name">{{ r.name }}</span>
            <span class="kg-panel-rel-rel">{{ r.relation }}</span>
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style>
.kg-root {
  position: relative;
}
.kg-chart {
  background: transparent;
}
.kg-error {
  color: #999;
  text-align: center;
  padding: 40px 0;
  font-size: 14px;
}

/* 工具栏 */
.kg-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 4px;
  flex-wrap: wrap;
}
.kg-stats {
  font-size: 12px;
  color: var(--vp-c-text-3, #999);
}
.kg-search {
  position: relative;
  display: inline-flex;
  align-items: center;
}
.kg-search-input {
  width: 240px;
  padding: 6px 28px 6px 10px;
  border: 1px solid var(--vp-c-divider, #ddd);
  border-radius: 8px;
  background: var(--vp-c-bg, #fff);
  color: var(--vp-c-text-1, #333);
  font-size: 13px;
  outline: none;
}
.kg-search-input:focus {
  border-color: var(--vp-c-brand, #3b82f6);
}
.kg-search-clear {
  position: absolute;
  right: 6px;
  border: none;
  background: none;
  cursor: pointer;
  color: var(--vp-c-text-3, #999);
  font-size: 14px;
  line-height: 1;
}
.kg-search-clear:hover {
  color: var(--vp-c-text-1, #333);
}
.kg-reset {
  border: 1px solid var(--vp-c-divider, #ddd);
  border-radius: 8px;
  background: var(--vp-c-bg, #fff);
  color: var(--vp-c-text-1, #333);
  padding: 6px 12px;
  font-size: 13px;
  cursor: pointer;
}
.kg-reset:hover {
  border-color: var(--vp-c-brand, #3b82f6);
  color: var(--vp-c-brand, #3b82f6);
}

/* 右侧信息面板 */
.kg-panel {
  position: fixed;
  top: 120px;
  right: 24px;
  z-index: 1000;
  width: 300px;
  max-width: calc(100vw - 48px);
  background: #fff;
  border: 1px solid #e2e2e2;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.14);
  padding: 14px 16px;
  color: #333;
  font-size: 13px;
  max-height: calc(100vh - 180px);
  overflow: auto;
}
.kg-panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.kg-panel-title {
  font-size: 16px;
  font-weight: 700;
}
.kg-panel-close {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  color: #999;
  padding: 2px 4px;
}
.kg-panel-close:hover {
  color: #333;
}
.kg-panel-module {
  display: inline-block;
  font-size: 12px;
  color: #666;
  background: #f5f5f5;
  border-radius: 4px;
  padding: 1px 8px;
  margin-bottom: 8px;
}
.kg-panel-desc {
  margin: 0 0 10px;
  line-height: 1.65;
  color: #444;
}
.kg-panel-link {
  display: inline-block;
  color: #3b82f6;
  text-decoration: none;
  font-size: 13px;
  margin-bottom: 12px;
}
.kg-panel-link:hover {
  text-decoration: underline;
}
.kg-panel-rels-title {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  margin-bottom: 6px;
  padding-top: 8px;
  border-top: 1px dashed #e2e2e2;
}
.kg-panel-rel {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  border: 1px solid var(--vp-c-divider, #e2e2e2);
  border-radius: 8px;
  background: var(--vp-c-bg-alt, #fafafa);
  padding: 6px 10px;
  margin-bottom: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #333;
  text-align: left;
}
.kg-panel-rel:hover {
  border-color: #3b82f6;
}
.kg-panel-rel-name {
  font-weight: 500;
}
.kg-panel-rel-rel {
  font-size: 12px;
  color: #999;
}

.dark .kg-panel {
  background: #1e1e1e;
  border-color: #3a3a3a;
  color: #ddd;
}
.dark .kg-panel-title { color: #eee; }
.dark .kg-panel-module { background: #2a2a2a; color: #aaa; }
.dark .kg-panel-desc { color: #bbb; }
.dark .kg-panel-close { color: #777; }
.dark .kg-panel-close:hover { color: #ddd; }
.dark .kg-panel-rels-title { color: #999; border-color: #3a3a3a; }
.dark .kg-panel-rel { background: #2a2a2a; color: #ddd; border-color: #3a3a3a; }
.dark .kg-panel-rel:hover { border-color: #3b82f6; }
.dark .kg-panel-rel-rel { color: #888; }
.dark .kg-stats { color: #777; }
</style>
