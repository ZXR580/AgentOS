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
const zoom = ref(false)
let obs = null

function toggleZoom() {
  zoom.value = !zoom.value
}
function closeZoom() {
  zoom.value = false
}

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
    <div ref="el" class="mermaid-svg" v-html="svg" @click="toggleZoom"></div>
    <figcaption v-if="caption" class="mermaid-caption">
      {{ caption }}<span v-if="svg" class="mermaid-zoom-hint">（点击图可放大）</span>
    </figcaption>
  </figure>

  <Teleport to="body">
    <div v-if="zoom" class="mermaid-zoom" @click="closeZoom">
      <div class="mermaid-zoom-box" @click.stop>
        <button class="mermaid-zoom-close" aria-label="关闭" @click="closeZoom">×</button>
        <div class="mermaid-zoom-svg" v-html="svg"></div>
      </div>
    </div>
  </Teleport>
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
  cursor: zoom-in;
}
.mermaid-svg svg {
  width: 100%;
  height: auto;
  min-width: 480px;
}
.mermaid-caption {
  margin-top: 4px;
  font-size: 12px;
  color: var(--vp-c-text-3, #999);
}
.mermaid-zoom-hint {
  margin-left: 6px;
  opacity: 0.7;
}
.mermaid-zoom {
  position: fixed;
  inset: 0;
  z-index: 2000;
  background: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.mermaid-zoom-box {
  position: relative;
  max-width: 96vw;
  max-height: 92vh;
  overflow: auto;
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
}
.mermaid-zoom-box .mermaid-zoom-svg svg {
  width: auto;
  max-width: none;
  height: auto;
  min-width: 720px;
}
.mermaid-zoom-close {
  position: absolute;
  top: 8px;
  right: 10px;
  border: none;
  background: none;
  font-size: 22px;
  line-height: 1;
  color: #666;
  cursor: pointer;
  z-index: 2;
}
.mermaid-zoom-close:hover {
  color: #000;
}

</style>
