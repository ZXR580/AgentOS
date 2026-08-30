<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import { TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([GraphChart, TooltipComponent, CanvasRenderer])

const props = defineProps({
  chapter: { type: String, required: true },   // e.g. "/ch04_agent"
  title: { type: String, default: '本章知识点脉络' },
})

const MODULES = [
  { value: 'ai', color: '#3b82f6' },
  { value: 'agent', color: '#8b5cf6' },
  { value: 'os', color: '#10b981' },
  { value: 'software', color: '#f59e0b' },
  { value: 'hardware', color: '#ef4444' },
]
const FALLBACK = '#94a3b8'

const chartEl = ref(null)
const errorMsg = ref('')
const count = ref(0)
let chart = null
let nodes = []
let edges = []

function color(m) {
  const f = MODULES.find((x) => x.value === m)
  return f ? f.color : FALLBACK
}
function isDark() {
  return document.documentElement.classList.contains('dark')
}
function onResize() {
  if (chart) chart.resize()
}

function option() {
  const dark = isDark()
  const nodeColor = dark ? '#ccc' : '#333'
  const edgeColor = dark ? '#8a8a8a' : '#999'
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: dark ? '#1f1f1f' : '#fff',
      borderColor: dark ? '#444' : '#ddd',
      textStyle: { color: dark ? '#ccc' : '#333', fontSize: 12 },
    },
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      force: { repulsion: 220, edgeLength: [70, 130], gravity: 0.1 },
      data: nodes.map((n) => ({
        name: n.id, displayName: n.name || n.id,
        chapter: n.chapter, anchor: n.anchor,
        symbolSize: 30,
        itemStyle: { color: color(n.module) },
      })),
      links: edges.map((e) => ({ source: e.source, target: e.target, relation: e.relation })),
      label: { show: true, fontSize: 11, color: nodeColor, formatter: (p) => p.data.displayName },
      edgeLabel: { show: true, fontSize: 10, color: edgeColor, formatter: (p) => p.data.relation },
      lineStyle: { color: edgeColor, opacity: 0.5, width: 1.2 },
      emphasis: { focus: 'adjacency' },
      animationDuration: 400,
    }],
  }
}

function onClick(p) {
  if (p && p.componentType === 'series' && p.dataType === 'node' && p.data) {
    const d = p.data
    if (d.chapter && d.anchor) window.open(d.chapter + '#' + d.anchor, '_blank')
  }
}

let obs = null
onMounted(async () => {
  try {
    const res = await fetch('/graph-data.json')
    if (!res.ok) throw new Error('bad status ' + res.status)
    const data = await res.json()
    if (!data || !Array.isArray(data.nodes)) throw new Error('invalid payload')
    nodes = data.nodes.filter((n) => n && n.chapter === props.chapter)
    const idSet = new Set(nodes.map((n) => n.id))
    edges = (data.edges || []).filter((e) => idSet.has(e.source) && idSet.has(e.target))
    count.value = nodes.length
    if (!chart && chartEl.value) {
      chart = echarts.init(chartEl.value)
      chart.setOption(option())
      chart.on('click', onClick)
    }
    window.addEventListener('resize', onResize)
    obs = new MutationObserver(() => chart && chart.setOption(option()))
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
  } catch {
    errorMsg.value = '本章知识点图谱加载失败'
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  if (obs) obs.disconnect()
  if (chart) { chart.dispose(); chart = null }
})
</script>

<template>
  <div class="sg-wrap">
    <div class="sg-head">
      <span class="sg-title">{{ title }}</span>
      <span class="sg-count">{{ count }} 个知识点 · 点击节点跳转对应小节</span>
    </div>
    <div v-if="!errorMsg" ref="chartEl" class="sg-chart" style="height: 320px; width: 100%"></div>
    <p v-if="errorMsg" class="sg-error">{{ errorMsg }}</p>
  </div>
</template>

<style>
.sg-wrap {
  margin: 20px 0 8px;
  border: 1px solid var(--vp-c-divider, #e2e2e2);
  border-radius: 12px;
  padding: 12px;
  background: var(--vp-c-bg, #fff);
}
.sg-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 8px;
}
.sg-title {
  font-weight: 600;
  font-size: 15px;
  color: var(--vp-c-text-1, #333);
}
.sg-count {
  font-size: 12px;
  color: var(--vp-c-text-3, #999);
}
.sg-chart {
  background: transparent;
}
.sg-error {
  color: #999;
  font-size: 13px;
}
</style>
