<script setup>
import { ref, onMounted, computed } from 'vue'

const props = defineProps({
  // JSON 字符串：{"title":"可选标题","steps":[{"label":"生成","tag":"模型","desc":"……"},...]}
  data: { type: String, default: '{}' },
  title: { type: String, default: '' },
})

const steps = ref([])
const active = ref(null)

onMounted(() => {
  try {
    const d = JSON.parse(props.data)
    steps.value = (d && d.steps) || []
  } catch {
    steps.value = []
  }
})

function toggle(i) {
  active.value = active.value === i ? null : i
}
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
    <div v-if="cur" class="flux-desc">
      <strong>{{ cur.label }}</strong>{{ cur.desc ? ' — ' + cur.desc : '' }}
    </div>
  </div>
</template>

<style>
.viz-flux .flux-track {
  display: flex;
  align-items: stretch;
  gap: 6px;
  flex-wrap: wrap;
}
.viz-flux .flux-step {
  flex: 1;
  min-width: 110px;
  padding: 10px 12px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 10px;
  background: var(--vp-c-bg);
  cursor: pointer;
  text-align: center;
  transition: all 0.15s;
  color: var(--vp-c-text-1);
}
.viz-flux .flux-step:hover {
  border-color: var(--vp-c-brand);
}
.viz-flux .flux-step.active {
  border-color: var(--vp-c-brand);
  background: var(--vp-c-brand-soft);
}
.viz-flux .flux-label {
  font-weight: 600;
  font-size: 14px;
}
.viz-flux .flux-tag {
  font-size: 12px;
  color: var(--vp-c-text-3);
  margin-top: 2px;
}
.viz-flux .flux-arrow {
  align-self: center;
  color: var(--vp-c-text-3);
  font-size: 16px;
}
.viz-flux .flux-desc {
  margin-top: 10px;
  font-size: 13px;
  color: var(--vp-c-text-2);
  background: var(--vp-c-bg-alt);
  border-radius: 8px;
  padding: 8px 12px;
}
</style>
