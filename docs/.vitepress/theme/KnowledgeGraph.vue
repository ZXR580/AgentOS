<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
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

let chart = null
let allNodes = []
let allEdges = []
let selected = {}
let themeObserver = null

function isDark() {
  return document.documentElement.classList.contains('dark')
}

function moduleOf(value) {
  return MODULES.find((m) => m.value === value)
}

function moduleColor(value) {
  const m = moduleOf(value)
  return m ? m.color : FALLBACK_COLOR
}

function moduleLabel(value) {
  const m = moduleOf(value)
  return m ? m.label : String(value == null ? '未知' : value)
}

function buildOption() {
  const dark = isDark()
  const nodeColor = dark ? '#ccc' : '#333'
  const edgeColor = dark ? '#8a8a8a' : '#999'
  const nodes = allNodes.filter((n) => selected[moduleLabel(n.module)] !== false)
  const nodeIds = new Set(nodes.map((n) => n.id))
  const links = allEdges
    .filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))
    .map((e) => ({ source: e.source, target: e.target, relation: e.relation }))

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
        data: nodes.map((n) => ({
          name: n.id,
          displayName: n.name || n.id,
          module: n.module,
          desc: n.desc,
          chapter: n.chapter,
          anchor: n.anchor,
          symbolSize: 36,
          itemStyle: { color: moduleColor(n.module) },
        })),
        links,
        label: { show: true, fontSize: 12, color: nodeColor, formatter: (p) => p.data.displayName },
        edgeLabel: { show: true, fontSize: 10, color: edgeColor, formatter: (p) => p.data.relation },
        lineStyle: { color: edgeColor, opacity: 0.6, width: 1.5 },
        emphasis: { focus: 'adjacency' },
        animationDuration: 500,
        animationDurationUpdate: 300,
        animationEasingUpdate: 'quinticInOut',
      },
    ],
  }
}

function onLegendChanged(params) {
  selected = { ...params.selected }
  chart.setOption(buildOption())
}

function onChartClick(params) {
  if (params && params.componentType === 'series' && params.dataType === 'node' && params.data) {
    const d = params.data
    card.value = {
      name: d.displayName,
      module: d.module,
      desc: d.desc || '',
      chapter: d.chapter,
      anchor: d.anchor,
    }
  } else {
    card.value = null
  }
}

function onResize() {
  if (chart) chart.resize()
}

onMounted(async () => {
  try {
    const res = await fetch('/graph-data.json')
    if (!res.ok) throw new Error('bad status ' + res.status)
    const data = await res.json()
    if (!data || !Array.isArray(data.nodes)) throw new Error('invalid payload')
    allNodes = data.nodes.filter((n) => n && n.id)
    allEdges = (data.edges || []).filter((e) => e && e.source != null && e.target != null)
    MODULES.forEach((m) => {
      selected[m.label] = true
    })
    chart = echarts.init(chartEl.value)
    chart.setOption(buildOption())
    chart.on('legendselectchanged', onLegendChanged)
    chart.on('click', onChartClick)
    window.addEventListener('resize', onResize)
    themeObserver = new MutationObserver(() => {
      if (chart) chart.setOption(buildOption())
    })
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
  } catch {
    errorMsg.value = '图谱数据加载失败'
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  if (themeObserver) themeObserver.disconnect()
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<template>
  <div
    v-show="!errorMsg"
    ref="chartEl"
    class="kg-chart"
    style="height: calc(100vh - 180px); width: 100%"
  ></div>
  <p v-if="errorMsg" class="kg-error">{{ errorMsg }}</p>

  <Teleport to="body">
    <div v-if="card" class="kg-card">
      <div class="kg-card-head">
        <span class="kg-card-title">{{ card.name }}</span>
        <button class="kg-card-close" aria-label="关闭" @click="card = null">×</button>
      </div>
      <div class="kg-card-module">{{ moduleLabel(card.module) }}</div>
      <p class="kg-card-desc">{{ card.desc }}</p>
      <a
        v-if="card.anchor"
        class="kg-card-link"
        :href="(card.chapter || '') + '#' + card.anchor"
      >查看详情</a>
    </div>
  </Teleport>
</template>

<style>
.kg-chart {
  background: transparent;
}

.kg-error {
  color: #999;
  text-align: center;
  padding: 40px 0;
  font-size: 14px;
}

.kg-card {
  position: fixed;
  top: 120px;
  right: 24px;
  z-index: 1000;
  width: 280px;
  max-width: calc(100vw - 48px);
  background: #fff;
  border: 1px solid #e2e2e2;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  padding: 12px 14px;
  color: #333;
  font-size: 13px;
}

.kg-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.kg-card-title {
  font-size: 15px;
  font-weight: 600;
}

.kg-card-close {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  color: #999;
  padding: 2px 4px;
}

.kg-card-close:hover {
  color: #333;
}

.kg-card-module {
  display: inline-block;
  font-size: 12px;
  color: #666;
  background: #f5f5f5;
  border-radius: 4px;
  padding: 1px 8px;
  margin-bottom: 8px;
}

.kg-card-desc {
  margin: 0 0 10px;
  line-height: 1.6;
  color: #444;
}

.kg-card-link {
  display: inline-block;
  color: #3b82f6;
  text-decoration: none;
  font-size: 13px;
}

.kg-card-link:hover {
  text-decoration: underline;
}

.dark .kg-card {
  background: #1e1e1e;
  border-color: #3a3a3a;
  color: #ddd;
}

.dark .kg-card-title {
  color: #eee;
}

.dark .kg-card-module {
  background: #2a2a2a;
  color: #aaa;
}

.dark .kg-card-desc {
  color: #bbb;
}

.dark .kg-card-close {
  color: #777;
}

.dark .kg-card-close:hover {
  color: #ddd;
}
</style>
