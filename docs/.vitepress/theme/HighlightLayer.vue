<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vitepress'

const ROOT_SELECTOR = '.VPDoc'
const STORAGE_PREFIX = 'kb-hl:'

const route = useRoute()
const btnVisible = ref(false)
const btnPos = ref({ left: 0, top: 0 })
const count = ref(0)

let root = null

function storageKey() {
  return STORAGE_PREFIX + location.pathname
}

function loadRecords() {
  try {
    const arr = JSON.parse(localStorage.getItem(storageKey()) || '[]')
    return Array.isArray(arr) ? arr : []
  } catch {
    return []
  }
}

function saveRecords(records) {
  try {
    localStorage.setItem(storageKey(), JSON.stringify(records))
  } catch {}
}

function getRoot() {
  if (!root) root = document.querySelector(ROOT_SELECTOR)
  return root
}

function pathOf(node) {
  const r = getRoot()
  const path = []
  let cur = node
  while (cur && cur !== r) {
    path.unshift(Array.prototype.indexOf.call(cur.parentNode.childNodes, cur))
    cur = cur.parentNode
  }
  return path
}

function nodeFromPath(path) {
  const r = getRoot()
  let cur = r
  for (const idx of path) {
    if (!cur || !cur.childNodes) return null
    cur = cur.childNodes[idx]
    if (!cur) return null
  }
  return cur
}

function firstTextNode(node) {
  if (node.nodeType === Node.TEXT_NODE) return node
  return document.createTreeWalker(node, NodeFilter.SHOW_TEXT).nextNode()
}

function lastTextNode(node) {
  if (node.nodeType === Node.TEXT_NODE) return node
  const tw = document.createTreeWalker(node, NodeFilter.SHOW_TEXT)
  let last = null
  let n
  while ((n = tw.nextNode())) last = n
  return last
}

// 将 (container, offset) 归一化为文本节点边界；offset 越界时收敛到合法范围
function toTextBoundary(container, offset, isStart) {
  if (container.nodeType === Node.TEXT_NODE) {
    return { node: container, offset: Math.max(0, Math.min(offset, container.length)) }
  }
  const idx = isStart ? offset : Math.max(0, offset - 1)
  const child = container.childNodes[idx] || container
  if (child.nodeType === Node.TEXT_NODE) {
    return isStart ? { node: child, offset: 0 } : { node: child, offset: child.length }
  }
  const tn = isStart ? firstTextNode(child) : lastTextNode(child)
  if (tn) return { node: tn, offset: isStart ? 0 : tn.length }
  const fallback = isStart ? firstTextNode(container) : lastTextNode(container)
  return fallback ? { node: fallback, offset: isStart ? 0 : fallback.length } : null
}

function buildRange(startNode, startOffset, endNode, endOffset) {
  const range = document.createRange()
  const s = toTextBoundary(startNode, startOffset, true)
  const e = toTextBoundary(endNode, endOffset, false)
  if (!s || !e) return null
  range.setStart(s.node, s.offset)
  range.setEnd(e.node, e.offset)
  return range
}

function wrapRange(range) {
  const mark = document.createElement('mark')
  mark.className = 'kb-hl'
  try {
    range.surroundContents(mark)
  } catch {
    const frag = range.extractContents()
    mark.appendChild(frag)
    range.insertNode(mark)
  }
  return mark
}

function comparePaths(a, b) {
  const len = Math.min(a.length, b.length)
  for (let i = 0; i < len; i++) {
    if (a[i] !== b[i]) return a[i] - b[i]
  }
  return a.length - b.length
}

function hideButton() {
  btnVisible.value = false
}

function clearSelection() {
  const sel = window.getSelection()
  if (sel) sel.removeAllRanges()
  hideButton()
}

function isInsideDoc(container) {
  const r = getRoot()
  return !!r && r.contains(container)
}

function onMouseUp() {
  const r = getRoot()
  if (!r) return
  const sel = window.getSelection()
  if (!sel || sel.rangeCount === 0 || sel.isCollapsed) {
    hideButton()
    return
  }
  const range = sel.getRangeAt(0)
  if (!isInsideDoc(range.startContainer) || !isInsideDoc(range.endContainer)) {
    hideButton()
    return
  }
  if (!range.toString().trim()) {
    hideButton()
    return
  }
  const rect = range.getBoundingClientRect()
  if (!rect || (rect.width === 0 && rect.height === 0)) {
    hideButton()
    return
  }
  let top = rect.top - 38
  if (top < 8) top = rect.bottom + 8
  btnPos.value = { left: Math.min(Math.max(rect.left, 8), window.innerWidth - 90), top }
  btnVisible.value = true
}

function onSelectionChange() {
  const sel = window.getSelection()
  if (!sel || sel.isCollapsed || sel.rangeCount === 0) hideButton()
}

function onHighlightClick() {
  const r = getRoot()
  const sel = window.getSelection()
  if (!r || !sel || sel.rangeCount === 0) return
  const range = sel.getRangeAt(0)
  if (!isInsideDoc(range.startContainer) || !isInsideDoc(range.endContainer)) return
  // 选区与已有高亮相交时跳过，避免嵌套 mark
  const marks = r.querySelectorAll('mark.kb-hl')
  for (const m of marks) {
    if (range.intersectsNode(m)) {
      clearSelection()
      return
    }
  }
  const start = toTextBoundary(range.startContainer, range.startOffset, true)
  const end = toTextBoundary(range.endContainer, range.endOffset, false)
  if (!start || !end) return
  const rec = { path: pathOf(start.node), start: start.offset, end: end.offset }
  if (end.node !== start.node) rec.endPath = pathOf(end.node)
  wrapRange(buildRange(start.node, start.offset, end.node, end.offset))
  const records = loadRecords()
  records.push(rec)
  records.sort((a, b) => comparePaths(a.path, b.path))
  saveRecords(records)
  count.value = records.length
  clearSelection()
}

function resolveRecord(rec) {
  const startNode = nodeFromPath(rec.path)
  if (!startNode) return null
  const endNode = rec.endPath ? nodeFromPath(rec.endPath) : startNode
  if (!endNode) return null
  const range = buildRange(startNode, rec.start, endNode, rec.end)
  if (!range || range.collapsed) return null
  return range
}

function isInsideMark(node) {
  if (node.nodeType === Node.TEXT_NODE) {
    return !!(node.parentElement && node.parentElement.closest('mark.kb-hl'))
  }
  if (node.nodeType === Node.ELEMENT_NODE) {
    return !!node.closest('mark.kb-hl')
  }
  return false
}

// 顺序恢复：每恢复一条就重现一次创建时的 DOM 结构，后续记录的 path 才能按序解析
function restore() {
  const r = getRoot()
  if (!r || r.querySelector('mark.kb-hl')) return
  const records = loadRecords()
  const kept = []
  for (const rec of records) {
    const range = resolveRecord(rec)
    if (!range || isInsideMark(range.startContainer)) continue
    wrapRange(range)
    kept.push(rec)
  }
  if (kept.length !== records.length) saveRecords(kept)
  count.value = kept.length
}

function restoreWithRetry(attempt = 0) {
  if (!document.querySelector(ROOT_SELECTOR) && attempt < 5) {
    setTimeout(() => restoreWithRetry(attempt + 1), 200)
    return
  }
  restore()
}

function onDocumentClick(e) {
  hideButton()
  const r = getRoot()
  const target = e.target
  if (!r || !target || typeof target.closest !== 'function') return
  const mark = target.closest('mark.kb-hl')
  if (!mark || !r.contains(mark)) return
  removeMark(mark)
}

// 展开 mark（子节点数 != 1）后，同一父容器内后续记录的路径需要平移
function adjustPath(path, parentPath, slotIdx, extra) {
  if (path.length <= parentPath.length) return
  for (let i = 0; i < parentPath.length; i++) {
    if (path[i] !== parentPath[i]) return
  }
  if (path[parentPath.length] > slotIdx) path[parentPath.length] += extra
}

function removeMark(mark) {
  const r = getRoot()
  const records = loadRecords()
  // 记录按 path 排序，与文档顺序的 mark 一一对应
  const marks = Array.prototype.slice.call(r.querySelectorAll('mark.kb-hl'))
  const idx = marks.indexOf(mark)
  if (idx === -1 || idx >= records.length) return
  const parent = mark.parentNode
  const extra = mark.childNodes.length - 1
  if (extra !== 0) {
    const parentPath = pathOf(parent)
    const slotIdx = Array.prototype.indexOf.call(parent.childNodes, mark)
    for (const rec of records) {
      adjustPath(rec.path, parentPath, slotIdx, extra)
      if (rec.endPath) adjustPath(rec.endPath, parentPath, slotIdx, extra)
    }
  }
  while (mark.firstChild) parent.insertBefore(mark.firstChild, mark)
  parent.removeChild(mark)
  records.splice(idx, 1)
  saveRecords(records)
  count.value = records.length
}

function clearAll() {
  const r = getRoot()
  if (!r) return
  r.querySelectorAll('mark.kb-hl').forEach((m) => {
    const p = m.parentNode
    while (m.firstChild) p.insertBefore(m.firstChild, m)
    p.removeChild(m)
  })
  localStorage.removeItem(storageKey())
  count.value = 0
}

onMounted(() => {
  document.addEventListener('mouseup', onMouseUp)
  document.addEventListener('click', onDocumentClick, true)
  document.addEventListener('selectionchange', onSelectionChange)
  window.addEventListener('scroll', hideButton, true)
  restoreWithRetry()
})

watch(
  () => route.path,
  () => {
    root = null
    hideButton()
    count.value = 0
    restoreWithRetry()
  },
  { flush: 'post' }
)

onBeforeUnmount(() => {
  document.removeEventListener('mouseup', onMouseUp)
  document.removeEventListener('click', onDocumentClick, true)
  document.removeEventListener('selectionchange', onSelectionChange)
  window.removeEventListener('scroll', hideButton, true)
})
</script>

<template>
  <Teleport to="body">
    <button
      v-if="btnVisible"
      class="kb-hl-btn"
      :style="{ left: btnPos.left + 'px', top: btnPos.top + 'px' }"
      @mousedown.prevent
      @click="onHighlightClick"
    >高亮</button>
    <button
      v-if="count > 0"
      class="kb-hl-clear"
      title="清除本页高亮"
      @click="clearAll"
    >清除本页高亮</button>
  </Teleport>
</template>

<style>
mark.kb-hl {
  background: rgba(255, 213, 0, 0.4);
  border-radius: 2px;
  cursor: pointer;
  color: inherit;
}

.kb-hl-btn {
  position: fixed;
  z-index: 1000;
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 13px;
  line-height: 1.4;
  color: #333;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  user-select: none;
}

.kb-hl-btn:hover {
  background: #f5f5f5;
}

.kb-hl-clear {
  position: fixed;
  top: 72px;
  right: 16px;
  z-index: 1000;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 12px;
  color: #999;
  cursor: pointer;
  opacity: 0.45;
  transition: opacity 0.2s;
}

.kb-hl-clear:hover {
  opacity: 1;
  color: #666;
  border-color: #ddd;
  background: rgba(255, 255, 255, 0.6);
}

.dark .kb-hl-btn {
  background: #2b2b2b;
  border-color: #555;
  color: #eee;
}

.dark .kb-hl-btn:hover {
  background: #333;
}

.dark .kb-hl-clear {
  color: #777;
}

.dark .kb-hl-clear:hover {
  color: #bbb;
  border-color: #444;
  background: rgba(0, 0, 0, 0.3);
}
</style>
