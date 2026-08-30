<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  // JSON 字符串：{"title":"可省略","sequence":"bottom-up","layers":[{"title":"应用能力层","items":["…","…"]},...]}
  // 数组顺序即从顶部到底部；sequence="top-down"（默认）顶部为数组首项，
  // "bottom-up" 时把数组反转显示（下层在底部）。
  data: { type: String, default: '{}' },
  title: { type: String, default: '' },
})

const layers = ref([])
const sequence = ref('top-down')
const active = ref(null)

onMounted(() => {
  try {
    const d = JSON.parse(props.data)
    sequence.value = (d && d.sequence) || 'top-down'
    let arr = (d && d.layers) || []
    if (sequence.value === 'bottom-up') arr = [...arr].reverse()
    layers.value = arr
  } catch {
    layers.value = []
  }
})

function toggle(i) {
  active.value = active.value === i ? null : i
}
</script>

<template>
  <div class="viz viz-layer">
    <div v-if="title || props.title" class="viz-title">{{ title || props.title }}</div>
    <div class="lay-stack">
      <div
        v-for="(l, i) in layers"
        :key="i"
        class="lay-item"
        :class="{ active: active === i }"
        @click="toggle(i)"
      >
        <div class="lay-head">
          <span class="lay-title">{{ l.title }}</span>
          <span class="lay-arrow">{{ active === i ? '▾' : '▸' }}</span>
        </div>
        <div v-if="active === i" class="lay-items">
          <span v-for="(it, k) in l.items" :key="k" class="lay-chip">{{ it }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
.viz-layer .lay-stack {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.viz-layer .lay-item {
  border: 1px solid var(--vp-c-divider);
  border-radius: 10px;
  background: var(--vp-c-bg);
  padding: 10px 14px;
  cursor: pointer;
  transition: all 0.15s;
  color: var(--vp-c-text-1);
}
.viz-layer .lay-item:hover {
  border-color: var(--vp-c-brand);
}
.viz-layer .lay-item.active {
  border-color: var(--vp-c-brand);
  background: var(--vp-c-brand-soft);
}
.viz-layer .lay-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 14px;
}
.viz-layer .lay-arrow {
  color: var(--vp-c-text-3);
}
.viz-layer .lay-items {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.viz-layer .lay-chip {
  font-size: 12px;
  background: var(--vp-c-bg-alt);
  border: 1px solid var(--vp-c-divider);
  border-radius: 6px;
  padding: 2px 8px;
  color: var(--vp-c-text-2);
}
</style>
