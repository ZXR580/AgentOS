<script setup>
defineProps({
  total: { type: Number, required: true },
  answers: { type: Array, required: true },
  current: { type: Number, required: true },
  review: { type: Boolean, default: false },
})

const emit = defineEmits(['jump'])
</script>

<template>
  <div class="eq-sheet">
    <div class="eq-sheet-title">{{ review ? '错题导览' : '答题卡' }}</div>
    <div class="eq-sheet-grid">
      <button
        v-for="i in total"
        :key="i"
        class="eq-cell"
        :class="{
          'eq-cell-wrong': review,
          'eq-cell-done': !review && answers[i - 1] && answers[i - 1].length > 0,
          'eq-cell-current': current === i - 1,
        }"
        @click="emit('jump', i - 1)"
      >
        {{ i }}
      </button>
    </div>
    <div v-if="review" class="eq-legend">
      <span><i class="eq-dot eq-dot-wrong"></i>错题</span>
      <span><i class="eq-dot eq-dot-current"></i>当前</span>
    </div>
    <div v-else class="eq-legend">
      <span><i class="eq-dot eq-dot-done"></i>已答</span>
      <span><i class="eq-dot"></i>未答</span>
      <span><i class="eq-dot eq-dot-current"></i>当前</span>
    </div>
  </div>
</template>

<style scoped>
.eq-sheet {
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: 10px;
  padding: 14px;
}
.eq-sheet-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--vp-c-text-2);
  margin-bottom: 10px;
}
.eq-sheet-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 6px;
}
.eq-cell {
  height: 30px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 6px;
  background: var(--vp-c-bg-alt);
  color: var(--vp-c-text-2);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.eq-cell:hover {
  border-color: var(--vp-c-brand);
}
.eq-cell-done {
  background: var(--vp-c-brand);
  border-color: var(--vp-c-brand);
  color: #fff;
}
.eq-cell-wrong {
  background: #ef4444;
  border-color: #ef4444;
  color: #fff;
}
.eq-cell-current {
  box-shadow: 0 0 0 2px var(--vp-c-brand);
  font-weight: 600;
}
.eq-legend {
  display: flex;
  gap: 14px;
  margin-top: 12px;
  font-size: 12px;
  color: var(--vp-c-text-3);
}
.eq-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 3px;
  background: var(--vp-c-bg-alt);
  border: 1px solid var(--vp-c-divider);
  margin-right: 4px;
  vertical-align: middle;
}
.eq-dot-done { background: var(--vp-c-brand); border-color: var(--vp-c-brand); }
.eq-dot-wrong { background: #ef4444; border-color: #ef4444; }
.eq-dot-current { box-shadow: 0 0 0 2px var(--vp-c-brand); }
</style>
