<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute } from 'vitepress'

const route = useRoute()
const terms = ref([])
const tooltip = ref(null)
let scanTimer = null

async function loadTerms() {
  try {
    const res = await fetch('/terms.json')
    if (!res.ok) throw new Error()
    const data = await res.json()
    terms.value = (data.terms || []).sort((a, b) => b.term.length - a.term.length)
  } catch {
    terms.value = []
  }
}

function isSkippable(node) {
  const el = node.parentElement
  if (!el) return true
  if (el.closest('pre, code, .vp-code, .eq-option, .kg-card, .exam-analysis-text')) return true
  if (el.closest('mark')) return true
  return false
}

function scan() {
  if (terms.value.length === 0) return
  const doc = document.querySelector('.VPDoc')
  if (!doc) return
  const walker = document.createTreeWalker(doc, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (isSkippable(node)) return NodeFilter.FILTER_REJECT
      if (!node.textContent.trim()) return NodeFilter.FILTER_REJECT
      return NodeFilter.FILTER_ACCEPT
    },
  })
  const textNodes = []
  while (walker.nextNode()) textNodes.push(walker.currentNode)
  for (const node of textNodes) wrapTextNode(node)
}

function wrapTextNode(node) {
  let text = node.textContent
  if (text.length < 2) return
  const matches = []
  for (const t of terms.value) {
    let idx = 0
    while ((idx = text.indexOf(t.term, idx)) !== -1) {
      matches.push({ term: t, index: idx })
      idx += t.term.length
    }
  }
  if (matches.length === 0) return
  matches.sort((a, b) => a.index - b.index)
  const frag = document.createDocumentFragment()
  let cursor = 0
  for (const m of matches) {
    if (m.index < cursor) continue
    if (m.index > cursor) {
      frag.appendChild(document.createTextNode(text.slice(cursor, m.index)))
    }
    const span = document.createElement('span')
    span.className = 'term-hover'
    span.dataset.term = m.term.term
    span.textContent = m.term.term
    span.addEventListener('mouseenter', (e) => showTip(e, m.term))
    span.addEventListener('mouseleave', hideTip)
    span.addEventListener('click', () => {
      if (m.term.href) window.location.href = m.term.href
    })
    frag.appendChild(span)
    cursor = m.index + m.term.term.length
  }
  if (cursor < text.length) {
    frag.appendChild(document.createTextNode(text.slice(cursor)))
  }
  node.parentNode.replaceChild(frag, node)
}

function showTip(e, term) {
  const rect = e.target.getBoundingClientRect()
  tooltip.value = {
    term: term.term,
    desc: term.desc,
    href: term.href || '',
    x: rect.left + rect.width / 2,
    y: rect.bottom + 8,
  }
}

function hideTip() {
  tooltip.value = null
}

watch(
  () => route.path,
  () => {
    clearTimeout(scanTimer)
    scanTimer = setTimeout(scan, 200)
  },
)

onMounted(async () => {
  await loadTerms()
  scan()
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="tooltip"
      class="term-tip"
      :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
      @mouseenter="tooltip = tooltip"
      @mouseleave="hideTip"
    >
      <div class="term-tip-head">
        <span class="term-tip-name">{{ tooltip.term }}</span>
        <a v-if="tooltip.href" class="term-tip-link" :href="tooltip.href">详情</a>
      </div>
      <p class="term-tip-desc">{{ tooltip.desc }}</p>
    </div>
  </Teleport>
</template>

<style>
.term-hover {
  border-bottom: 1px dashed var(--vp-c-brand);
  cursor: help;
  padding: 0 1px;
  transition: background 0.15s;
}
.term-hover:hover {
  background: var(--vp-c-brand-soft);
}
.term-tip {
  position: fixed;
  transform: translateX(-50%);
  z-index: 1200;
  width: 280px;
  max-width: calc(100vw - 40px);
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.14);
  padding: 10px 12px;
  pointer-events: auto;
}
.term-tip-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.term-tip-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--vp-c-text-1);
}
.term-tip-link {
  font-size: 12px;
  color: var(--vp-c-brand);
  text-decoration: none;
}
.term-tip-link:hover {
  text-decoration: underline;
}
.term-tip-desc {
  margin: 0;
  font-size: 12.5px;
  line-height: 1.6;
  color: var(--vp-c-text-2);
}
</style>
