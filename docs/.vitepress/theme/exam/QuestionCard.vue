<script setup>
import { computed } from 'vue'

const props = defineProps({
  question: { type: Object, required: true },
  selected: { type: Array, default: () => [] },
  interactive: { type: Boolean, default: false },
  showResult: { type: Boolean, default: false },
  correct: { type: Boolean, default: false },
})

const TYPE_LABEL = { single: '单选题', multi: '多选题', judge: '判断题' }
const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

const selectedSet = computed(() => new Set(props.selected))

function optionClass(i) {
  const cls = ['eq-option']
  if (props.interactive && selectedSet.value.has(i)) cls.push('eq-selected')
  if (props.showResult) {
    if (props.question.answerIdx.includes(i)) cls.push('eq-right')
    else if (selectedSet.value.has(i)) cls.push('eq-wrong')
  }
  return cls
}
</script>

<template>
  <div class="eq-question">
    <div class="eq-head">
      <span class="eq-type" :class="'eq-type-' + question.type">{{ TYPE_LABEL[question.type] }}</span>
      <span class="eq-module">{{ question.module }}</span>
      <span v-if="showResult" class="eq-mark" :class="correct ? 'eq-mark-right' : 'eq-mark-wrong'">
        {{ correct ? '正确' : '错误' }}
      </span>
    </div>
    <div class="eq-stem">{{ question.stem }}</div>
    <div class="eq-options">
      <button
        v-for="(opt, i) in question.options"
        :key="i"
        class="eq-option"
        :class="optionClass(i)"
        :disabled="!interactive"
        @click="$emit('select', i)"
      >
        <span class="eq-letter">{{ LETTERS[i] }}</span>
        <span class="eq-text">{{ opt.text }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.eq-question {
  padding: 4px 0;
}
.eq-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.eq-type {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
  color: #fff;
}
.eq-type-single { background: #3b82f6; }
.eq-type-multi { background: #8b5cf6; }
.eq-type-judge { background: #10b981; }
.eq-module {
  font-size: 12px;
  color: var(--vp-c-text-3);
  background: var(--vp-c-bg-alt);
  padding: 2px 10px;
  border-radius: 10px;
}
.eq-mark {
  font-size: 13px;
  font-weight: 600;
}
.eq-mark-right { color: #22c55e; }
.eq-mark-wrong { color: #ef4444; }
.eq-stem {
  font-size: 15px;
  line-height: 1.7;
  color: var(--vp-c-text-1);
  margin-bottom: 16px;
}
.eq-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.eq-option {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  text-align: left;
  padding: 10px 14px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
  font-size: 14px;
  line-height: 1.6;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.eq-option:hover:not(:disabled) {
  border-color: var(--vp-c-brand);
}
.eq-option:disabled {
  cursor: default;
}
.eq-letter {
  font-weight: 600;
  color: var(--vp-c-brand);
  flex-shrink: 0;
}
.eq-selected {
  border-color: var(--vp-c-brand);
  background: var(--vp-c-brand-soft);
}
.eq-right {
  border-color: #22c55e;
  background: rgba(34, 197, 94, 0.12);
}
.eq-right .eq-letter { color: #22c55e; }
.eq-wrong {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}
.eq-wrong .eq-letter { color: #ef4444; }
</style>
