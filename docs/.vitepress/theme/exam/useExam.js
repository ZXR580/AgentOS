import { ref, computed } from 'vue'

const EXAM_STRUCTURE = [
  { type: 'single', label: '单项选择题', count: 30 },
  { type: 'multi', label: '多项选择题', count: 10 },
  { type: 'judge', label: '判断题', count: 20 },
]

const MODULE_ORDER = ['ai', 'os', 'software', 'agent', 'hardware']
const MODULE_RATIO = { ai: 0.3, os: 0.2, software: 0.2, agent: 0.2, hardware: 0.1 }

const WRONGS_KEY = 'exam-wrongs'

function shuffle(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

function draw(questions, count, ratioMap) {
  const byModule = {}
  for (const q of questions) {
    if (!byModule[q.module]) byModule[q.module] = []
    byModule[q.module].push(q)
  }
  const drawn = []
  const rest = [...questions]
  const expected = {}
  let assigned = 0
  MODULE_ORDER.forEach((m, i) => {
    if (i === MODULE_ORDER.length - 1) {
      expected[m] = count - assigned
    } else {
      expected[m] = Math.round(count * (ratioMap[m] || 0))
      assigned += expected[m]
    }
  })
  for (const m of MODULE_ORDER) {
    const pool = byModule[m] || []
    const take = Math.min(expected[m] || 0, pool.length)
    const picked = shuffle(pool).slice(0, take)
    drawn.push(...picked)
    picked.forEach((q) => {
      const idx = rest.findIndex((r) => r.id === q.id)
      if (idx >= 0) rest.splice(idx, 1)
    })
  }
  if (drawn.length < count) {
    drawn.push(...shuffle(rest).slice(0, count - drawn.length))
  }
  return drawn
}

function shuffleOptions(q) {
  const order = shuffle(q.options.map((_, i) => i))
  const newOptions = order.map((i) => q.options[i])
  const answerIdx = q.answerKeys
    .map((k) => q.options.findIndex((o) => o.key === k))
    .filter((i) => i >= 0)
    .map((oldIdx) => order.indexOf(oldIdx))
    .sort((a, b) => a - b)
  return { options: newOptions, answerIdx }
}

export function useExam(realRef, mockRef) {
  const phase = ref('start')
  const paper = ref([])
  const answers = ref([])
  const current = ref(0)
  const results = ref([])
  const confirmVisible = ref(false)
  const reviewIndex = ref(0)
  const examSeq = ref(0)

  const currentQuestion = computed(() => paper.value[current.value] || null)
  const total = computed(() => paper.value.length)

  const structureLabel = computed(() =>
    EXAM_STRUCTURE.map((s) => `${s.label} ${s.count} 题`).join('、'),
  )

  const answeredCount = computed(() =>
    answers.value.filter((a) => a && a.length > 0).length,
  )

  function loadWrongsRaw() {
    try {
      return JSON.parse(localStorage.getItem(WRONGS_KEY)) || []
    } catch {
      return []
    }
  }

  function saveWrongs(list) {
    localStorage.setItem(WRONGS_KEY, JSON.stringify(list))
  }

  function findQuestion(id, source) {
    const pool = source === 'mock' ? mockRef.value : realRef.value
    return pool.find((q) => q.id === id) || null
  }

  function wrongCount() {
    return loadWrongsRaw().length
  }

  function recordWrongs(result) {
    const wrongs = loadWrongsRaw()
    for (const r of result) {
      if (r.correct) continue
      const myTexts = (r.answer || []).map((i) => r.q.options[i].text)
      const existing = wrongs.find((w) => w.id === r.q.id && w.source === (r.q.source || 'real'))
      if (existing) {
        existing.myAnswer = myTexts
        existing.at = Date.now()
      } else {
        wrongs.push({
          id: r.q.id,
          source: r.q.source || 'real',
          myAnswer: myTexts,
          at: Date.now(),
        })
      }
    }
    saveWrongs(wrongs)
  }

  function wrongList() {
    return loadWrongsRaw()
      .map((w) => ({ ...w, q: findQuestion(w.id, w.source) }))
      .filter((x) => x.q)
  }

  function removeWrong(id, source) {
    const wrongs = loadWrongsRaw().filter((w) => !(w.id === id && w.source === source))
    saveWrongs(wrongs)
  }

  function clearWrongs() {
    saveWrongs([])
  }

  function buildPaper(pool) {
    return pool.map((q) => {
      const { options, answerIdx } = shuffleOptions(q)
      return {
        id: q.id, type: q.type, module: q.module, stem: q.stem,
        options, answerIdx, explanation: q.explanation, chapter: q.chapter,
        source: q.source || 'real',
      }
    })
  }

  function start(source) {
    let pool
    if (source === 'wrong') {
      pool = wrongList().map((x) => x.q)
      if (pool.length === 0) return false
    } else {
      pool = (source === 'mock' ? mockRef.value : realRef.value) || []
    }
    const picked = []
    for (const s of EXAM_STRUCTURE) {
      const typePool = pool.filter((q) => q.type === s.type)
      picked.push(...draw(typePool, s.count, MODULE_RATIO))
    }
    paper.value = buildPaper(picked)
    answers.value = paper.value.map(() => [])
    current.value = 0
    results.value = []
    examSeq.value++
    phase.value = 'exam'
    return true
  }

  function startReview() {
    const list = wrongList()
    if (list.length === 0) return false
    paper.value = list.map((x) => ({
      ...x.q,
      myAnswerTexts: x.myAnswer || [],
      source: x.source,
    }))
    answers.value = paper.value.map(() => [])
    current.value = 0
    results.value = []
    examSeq.value++
    phase.value = 'review'
    return true
  }

  function toggleOption(optIndex) {
    if (phase.value !== 'exam') return
    const q = paper.value[current.value]
    if (!q) return
    const set = new Set(answers.value[current.value])
    if (q.type === 'single' || q.type === 'judge') {
      set.clear()
      set.add(optIndex)
    } else {
      if (set.has(optIndex)) set.delete(optIndex)
      else set.add(optIndex)
    }
    answers.value[current.value] = [...set].sort((a, b) => a - b)
  }

  function isAnswered(i) {
    return answers.value[i] && answers.value[i].length > 0
  }

  function isCorrect(q, ans) {
    if (!ans || ans.length === 0) return false
    return ans.length === q.answerIdx.length &&
      ans.every((v, i) => v === q.answerIdx[i])
  }

  function submit() {
    const result = paper.value.map((q, i) => ({
      q, answer: answers.value[i] || [], correct: isCorrect(q, answers.value[i]),
    }))
    results.value = result
    recordWrongs(result)
    phase.value = 'result'
  }

  const score = computed(() => results.value.filter((r) => r.correct).length)
  const wrongCountInExam = computed(() => results.value.filter((r) => !r.correct).length)

  function gotoReview(i) {
    reviewIndex.value = i
    phase.value = 'review'
  }

  function restart() {
    phase.value = 'start'
  }

  return {
    phase, paper, answers, current, results, confirmVisible, reviewIndex, examSeq,
    currentQuestion, total, structureLabel, answeredCount, score, wrongCountInExam,
    wrongCount, wrongList, removeWrong, clearWrongs,
    start, startReview, toggleOption, isAnswered, submit, gotoReview, restart,
  }
}
