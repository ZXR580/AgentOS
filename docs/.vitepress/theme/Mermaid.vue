<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import mermaid from 'mermaid'

const props = defineProps({
  // 单行 mermaid 源码（语句用 ; 分隔），例如
  // chart="flowchart LR; A[开始] --> B{判断}; B -->|是| C[结束]"
  chart: { type: String, default: '' },
  caption: { type: String, default: '' },
})

const el = ref(null)
const svg = ref('')
let obs = null

function isDark() {
  return document.documentElement.classList.contains('dark')
}

async function render() {
  const src = (props.chart || '').trim()
  if (!src) return
  try {
    mermaid.initialize({
      startOnLoad: false,
      theme: isDark() ? 'dark' : 'default',
      securityLevel: 'loose',
    })
    const { svg: out } = await mermaid.render('mmd-' + Date.now() + '-' + Math.floor(Math.random() * 1e6), src)
    svg.value = out
  } catch (e) {
    svg.value = '<pre style="color:#ef4444">Mermaid 渲染失败：' + String(e) + '</pre>'
  }
}

onMounted(() => {
  render()
  obs = new MutationObserver(() => render())
  obs.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
})

onBeforeUnmount(() => {
  if (obs) obs.disconnect()
})
</script>

<template>
  <figure class="mermaid-figure">
    <div ref="el" class="mermaid-svg" v-html="svg"></div>
    <figcaption v-if="caption" class="mermaid-caption">{{ caption }}</figcaption>
  </figure>
</template>

<style>
.mermaid-figure {
  margin: 16px 0;
  text-align: center;
}
.mermaid-svg {
  display: inline-block;
  max-width: 100%;
  overflow-x: auto;
  padding: 8px;
}
.mermaid-svg svg {
  max-width: 100%;
  height: auto;
}
.mermaid-caption {
  margin-top: 4px;
  font-size: 12px;
  color: var(--vp-c-text-3, #999);
}
</style>
