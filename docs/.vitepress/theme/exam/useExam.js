import { ref, computed } from 'vue'

// 最新正式命题规则：正式比赛每卷 120 题 = 单选 60 + 多选 40 + 判断 20
const EXAM_STRUCTURE = [
  { type: 'single', label: '单项选择题', count: 60 },
  { type: 'multi', label: '多项选择题', count: 40 },
  { type: 'judge', label: '判断题', count: 20 },
]

// 组卷时按题型归类的先后顺序（决定卷面分段顺序）
const TYPE_ORDER = { single: 0, multi: 1, judge: 2 }

const WRONGS_KEY = 'exam-wrongs'

function shuffle(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

// 把一组题目（含预先按题型+模块配比选好的题目）组装成一卷：
// 先按题型归类（单选 -> 多选 -> 判断），选项顺序随机并换算答案下标。
function buildPaper(questions) {
  const sorted = [...questions].sort(
    (a, b) => (TYPE_ORDER[a.type] ?? 9) - (TYPE_ORDER[b.type] ?? 9),
  )
  return sorted.map((q) => {
    const { options, answerIdx } = shuffleOptions(q)
    return {
      id: q.id, type: q.type, module: q.module, stem: q.stem,
      options, answerIdx, explanation: q.explanation, chapter: q.chapter,
      source: q.source || 'real',
    }
  })
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

export function useExam(realRef, mockRef, mockPapersRef) {
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
      // 未作答的题不算"做错"，不入错题本（否则提交未答题会误入错题本）
      if (!r.answer || r.answer.length === 0) continue
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

  // 把一组题目（已按题型+模块配比选好）组装成一卷并进入考试态
  function startWithQuestions(questions) {
    const qs = questions.filter(Boolean)
    if (qs.length === 0) return false
    paper.value = buildPaper(qs)
    answers.value = paper.value.map(() => [])
    current.value = 0
    results.value = []
    examSeq.value++
    phase.value = 'exam'
    return true
  }

  // source: 'real' | 'wrong' | 'mock'（纸卷由 paperId 指定，取自 mockPapersRef）
  function start(source, paperId) {
    if (source === 'wrong') {
      const list = wrongList().map((x) => x.q)
      return startWithQuestions(list)
    }
    if (source === 'real') {
      // 真题：官方 120 题原样呈现为一卷（单选 60 + 多选 20 + 判断 40）
      return startWithQuestions(realRef.value || [])
    }
    if (source === 'mock') {
      const papers = mockPapersRef.value || []
      const paper = papers.find((p) => p.id === paperId) || papers[0]
      if (!paper) return false
      const byId = new Map((mockRef.value || []).map((q) => [q.id, q]))
      const questions = paper.questionIds.map((id) => byId.get(id))
      return startWithQuestions(questions)
    }
    return false
  }

  function startReview() {
    const list = wrongList()
    if (list.length === 0) return false
    // 错题回顾也需打乱选项并算出 answerIdx（数字下标），供 reviewItem 与模板判分/显示
    paper.value = list.map((x) => {
      const { options, answerIdx } = shuffleOptions(x.q)
      return { ...x.q, options, answerIdx, myAnswerTexts: x.myAnswer || [], source: x.source }
    })
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
    // 交卷后把本次"做对"的题从错题本移除：已答对说明不再是错题，避免错题本残留旧记录
    result.forEach((r) => {
      if (r.correct) removeWrong(r.q.id, r.q.source || 'real')
    })
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

  // 交卷后的解析页 -> 返回"正误预览"（result 页）
  function gotoResult() {
    phase.value = 'result'
  }

  return {
    phase, paper, answers, current, results, confirmVisible, reviewIndex, examSeq,
    currentQuestion, total, structureLabel, answeredCount, score, wrongCountInExam,
    wrongCount, wrongList, removeWrong, clearWrongs,
    start, startReview, toggleOption, isAnswered, submit, gotoReview, restart, gotoResult,
  }
}
