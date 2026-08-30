<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  // JSON 字符串：{"title":"可选中","columns":["SVM","朴素贝叶斯"],"rows":[{"dim":"建模对象","cells":["边界","概率"]},...]}
  data: { type: String, default: '{}' },
  title: { type: String, default: '' },
})

const columns = ref([])
const rows = ref([])
const activeDim = ref(null)
const activeCol = ref(null)

onMounted(() => {
  try {
    const d = JSON.parse(props.data)
    columns.value = (d && d.columns) || []
    rows.value = (d && d.rows) || []
  } catch {
    columns.value = []
    rows.value = []
  }
})

function toggleDim(i) {
  activeDim.value = activeDim.value === i ? null : i
}
function toggleCol(i) {
  activeCol.value = activeCol.value === i ? null : i
}
</script>

<template>
  <div class="viz viz-compare">
    <div v-if="title || props.title" class="viz-title">{{ title || props.title }}</div>
    <table class="cmp-table">
      <thead>
        <tr>
          <th class="cmp-dim" @click="toggleCol(-1)">维度</th>
          <th
            v-for="(c, i) in columns"
            :key="i"
            :class="{ active: activeCol === i }"
            @click="toggleCol(i)"
          >{{ c }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(r, i) in rows" :key="i" :class="{ active: activeDim === i }">
          <td class="cmp-dim" @click="toggleDim(i)">{{ r.dim }}</td>
          <td v-for="(cell, j) in r.cells" :key="j" :class="{ 'col-hit': activeCol === j }">
            {{ cell }}
          </td>
        </tr>
      </tbody>
    </table>
    <div class="cmp-hint">点击维度或列可高亮对比差异</div>
  </div>
</template>

<style>
.viz-compare .cmp-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin-top: 6px;
}
.viz-compare .cmp-table th,
.viz-compare .cmp-table td {
  border: 1px solid var(--vp-c-divider);
  padding: 7px 10px;
  text-align: left;
  color: var(--vp-c-text-1);
}
.viz-compare .cmp-table th {
  background: var(--vp-c-bg-alt);
  font-weight: 600;
  cursor: pointer;
}
.viz-compare .cmp-table th.active,
.viz-compare .cmp-table td.col-hit {
  background: var(--vp-c-brand-soft);
}
.viz-compare .cmp-table tr.active td {
  background: var(--vp-c-brand-soft);
}
.viz-compare .cmp-dim {
  font-weight: 600;
  color: var(--vp-c-text-2);
  cursor: pointer;
}
.viz-compare .cmp-hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--vp-c-text-3);
}
</style>
