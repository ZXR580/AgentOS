<script setup>
import { ref, onMounted, computed } from 'vue'

const props = defineProps({
  // JSON 字符串：{"title":"可省略","pillars":[{"title":"规划","tag":"规划","desc":"……"},...]}
  data: { type: String, default: '{}' },
  title: { type: String, default: '' },
})

const pillars = ref([])
const active = ref(null)

onMounted(() => {
  try {
    const d = JSON.parse(props.data)
    pillars.value = (d && d.pillars) || []
  } catch {
    pillars.value = []
  }
})

function toggle(i) {
  active.value = active.value === i ? null : i
}
const cur = computed(() => (active.value !== null ? pillars.value[active.value] : null))
</script>

<template>
  <div class="viz viz-pillars">
    <div v-if="title || props.title" class="viz-title">{{ title || props.title }}</div>
    <div class="pil-row">
      <div
        v-for="(p, i) in pillars"
        :key="i"
        class="pil-item"
        :class="{ active: active === i }"
        @click="toggle(i)"
      >
        <div class="pil-num">{{ i + 1 }}</div>
        <div class="pil-title">{{ p.title }}</div>
        <div v-if="p.tag" class="pil-tag">{{ p.tag }}</div>
      </div>
    </div>
    <div v-if="cur" class="pil-desc">
      <strong>{{ cur.title }}</strong>{{ cur.desc ? ' — ' + cur.desc : '' }}
    </div>
  </div>
</template>

<style>
.viz-pillars .pil-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.viz-pillars .pil-item {
  flex: 1;
  min-width: 110px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  background: var(--vp-c-bg);
  padding: 14px 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.15s;
  color: var(--vp-c-text-1);
}
.viz-pillars .pil-item:hover {
  border-color: var(--vp-c-brand);
}
.viz-pillars .pil-item.active {
  border-color: var(--vp-c-brand);
  background: var(--vp-c-brand-soft);
}
.viz-pillars .pil-num {
  font-size: 12px;
  color: var(--vp-c-text-3);
  margin-bottom: 4px;
}
.viz-pillars .pil-title {
  font-weight: 600;
  font-size: 14px;
}
.viz-pillars .pil-tag {
  font-size: 12px;
  color: var(--vp-c-text-3);
  margin-top: 2px;
}
.viz-pillars .pil-desc {
  margin-top: 10px;
  font-size: 13px;
  color: var(--vp-c-text-2);
  background: var(--vp-c-bg-alt);
  border-radius: 8px;
  padding: 8px 12px;
}
</style>
