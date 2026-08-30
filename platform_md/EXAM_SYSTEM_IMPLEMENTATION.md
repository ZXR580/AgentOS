# 考试系统实现说明（Vue 3 + VitePress 版）

本文完整说明本仓库中"模拟考试系统"是如何从零实现的，供你（另一个 agent）参考，构建一套**线上考试平台**（尤其是配合强化学习 RL 的训练/评测场景）。原文为中文，关键再实现代码尽量贴近源码，便于直接复用或改造成独立 Vue / Vue + 后端项目。

---

## 0. 这套系统是什么

- **形态**：一个纯前端的在线练习/考试界面，跑在 **VitePress 1.x** 静态站点里，用 **Vue 3 组合式 API（Composition API）** 编写。
- **功能**：三套练习入口（真题、模拟题、错题本）；随机**组卷**（定结构 + 定模块占比）；逐题作答；**交卷评分**；错题自动收录（本地持久化）；逐题**查看解析/考点**。
- **数据**：题目是**静态 JSON 文件**（`docs/public/*.json`），前端 `fetch` 加载，无需后端。
- **关键特性**：
  1. 两套题库**物理隔离**：真题（`quiz-data.json`，120 题）与模拟题（`quiz-mock.json`，≥300 题），来源不同，不互相污染。
  2. 组卷**结构固定**（每卷 60 题：单选 30 + 多选 10 + 判断 20），并按**模块占比**抽取（ai 30% / os 20% / software 20% / agent 20% / hardware 10%）。
  3. **选项顺序随机**：每套卷生成时打乱选项顺序，避免"背选项位置"。
  4. **错题本**用 `localStorage` 持久化，只存"题干引用 + 我的答案 + 时间戳"，题目本体每次从题库取。

---

## 1. 技术栈与依赖

`package.json`：

```json
{
  "name": "learning-site",
  "type": "module",
  "scripts": {
    "dev": "vitepress dev docs",        // 本地预览 http://localhost:5173
    "build": "vitepress build docs",    // 打成静态站点到 docs/.vitepress/dist
    "preview": "vitepress preview docs"
  },
  "dependencies": {
    "vitepress": "^1.6.3",
    "echarts": "^5.6.0",
    "katex": "^0.18.4",
    "markdown-it-katex": "^2.0.3"
  }
}
```

- **VitePress** 静态站点生成器，本身基于 **Vite + Vue 3**。
- 考试相关的组件/逻辑**不依赖 echarts/katex**，那些是知识图谱（`KnowledgeGraph.vue`）和公式渲染用的，可忽略。
- 若要做**独立线上考试平台**，可以直接用 `Vite + Vue 3` 脚手架替代 VitePress（见 §10），考试逻辑可完整搬运。

---

## 2. 目录结构（考试相关）

```
docs/
├── exam.md                     # 入口页，挂 <ExamPage />
├── .vitepress/
│   ├── config.mts              # 站点配置：nav/sidebar 加 /exam 链接
│   ├── theme/
│   │   ├── index.js            # 主题入口：全局注册 ExamPage 等组件
│   │   └── exam/
│   │       ├── ExamPage.vue    # 顶层容器：入口/考试/结果/解析/错题回顾 五态切换
│   │       ├── useExam.js      # 核心逻辑：组卷/状态机/评分/错题本（组合式函数）
│   │       ├── QuestionCard.vue# 题目卡片：显示题干+选项，支持作答/展示结果
│   │       └── AnswerSheet.vue # 答题卡：题号导航，已答/未答/当前
│   └── ...
└── public/
    ├── quiz-data.json          # 真题题库（勿改）
    └── quiz-mock.json          # 模拟题库（可增改）
```

---

## 3. 数据层：题库 JSON Schema

每道题是这样一个对象（`useExam.js` 通过 `fetch` 加载后，标注 `source` 字段）：

```json
{
  "id": "M001",
  "type": "single",            // "single" | "multi" | "judge"
  "module": "ai",              // "ai"|"os"|"software"|"agent"|"hardware"
  "stem": "题干……",
  "options": [
    { "key": "A", "text": "选项文本" },
    { "key": "B", "text": "……" }
  ],
  "answerKeys": ["A"],          // single/judge 1 个；multi ≥2 个（A-F）
  "explanation": "解析……",
  "chapter": "/ch01_ai_foundation",  // 对应"查看考点"跳转链接
  "source": "mock"             // 加载后由代码标注，"real"|"mock"
}
```

### 3.1 题型格式（重要，三种题型要统一风格）
| type | 选项数 | 正确项数 | 选项 key | 说明 |
|---|---|---|---|---|
| `single` | 4 | 1 | A–D | 单选题 |
| `multi` | 6 | 3~4 | A–F | 多选题，正确项须全部选中才算对 |
| `judge` | 2（"正确"/"错误"） | 1 | A / B | 判断题，options 固定 `[{A:正确},{B:错误}]` |

> 模拟题（`quiz-mock.json`）必须与真题（`quiz-data.json`）对齐这些格式，否则组卷配比、答题体验都会不一致。

### 3.2 module ↔ chapter 映射（决定"考点"归属与"查看考点"链接）
| module | chapter | 对应手册 |
|---|---|---|
| ai | `/ch01_ai_foundation` | 第 1 章 |
| os | `/ch02_os_linux` | 第 2 章 |
| software | `/ch03_software` | 第 3 章 |
| agent | `/ch04_agent`（实践类 `/ch07_mcp_agent_practice`、平台 `/ch08_intelligent_platform`） | 第 4 / 7 / 8 章 |
| hardware | `/ch05_hardware` | 第 5 章 |

### 3.3 两套题库隔离
- `quiz-data.json`：**真题**（120 题），来源 `doc/A卷还原.md` + `doc/B卷还原.md`，由 `node tools/parse-quiz.mjs` 生成。**这是生成产物，别手改**；要改就改源 md 再跑脚本。
- `quiz-mock.json`：**模拟题**（≥300 题），人工/维护 agent 维护，`source` 固定为 `"mock"`。
- 前端加载时给 `source:'real'` / `source:'mock'`，错题本靠 `id + source` 区分来源。

---

## 4. 组卷逻辑（`useExam.js` 核心）

### 4.1 固定结构与模块占比
```js
const EXAM_STRUCTURE = [
  { type: 'single', label: '单项选择题', count: 30 },
  { type: 'multi',  label: '多项选择题', count: 10 },
  { type: 'judge',  label: '判断题',     count: 20 },
]
const MODULE_ORDER = ['ai', 'os', 'software', 'agent', 'hardware']
const MODULE_RATIO = { ai: 0.3, os: 0.2, software: 0.2, agent: 0.2, hardware: 0.1 }
```

每卷 **60 题** = 单选30 + 多选10 + 判断20；模块占比 = ai.3 / os.2 / software.2 / agent.2 / hardware.1。

### 4.2 `draw(questions, count, ratioMap)`：按模块占比抽题
```js
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
      expected[m] = count - assigned        // 最后一个模块补齐余数
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
  if (drawn.length < count) {               // 某模块不足时，从剩余题库补满
    drawn.push(...shuffle(rest).slice(0, count - drawn.length))
  }
  return drawn
}
```
- 先按 `module` 分池，再按 `MODULE_ORDER` 逐模块按比例取；最后一个模块用 `count - assigned` 补齐，保证总数精确。
- 某 `(type, module)` 池不足时，会从剩余题里补满——会**破坏配比**。所以题库要在 `module 3:2:2:2:1`、`type 3:1:2` 的节奏下**供题充足**（这也是维护模拟题时要控制分布的原因）。

### 4.3 `shuffleOptions(q)`：选项顺序随机
```js
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
```
- 打乱选项顺序，并**同步换算**正确答案在**新选项里的下标** `answerIdx`（用于比对）。
- 之后题目对象里用 `answerIdx`（数字下标数组）而不是 `answerKeys`（字母）来判分。

### 4.4 `buildPaper(pool)`：把题转成"考试卷"
```js
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
```
- 每题额外带 `options`（打乱后）、`answerIdx`、`source`，供答题与判分用。

### 4.5 `start(source)`：开始一场考试
```js
function start(source) {
  let pool
  if (source === 'wrong') {
    pool = wrongList().map((x) => x.q)      // 错题重练：从错题本取题
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
```

---

## 5. 核心状态机（`useExam.js`）

用 Vue 3 组合式 API，把整场考试的"状态 + 操作"收拢成一个 `useExam(realRef, mockRef)` 函数，返回响应式状态与方法。这是**组合式函数（composable）**的典型用法。

### 5.1 状态
```js
const phase = ref('start')        // 'start' | 'exam' | 'result' | 'review'
const paper = ref([])             // 当前卷（题目数组，含打乱后选项）
const answers = ref([])           // 每题的答案下标数组
const current = ref(0)            // 当前题索引
const results = ref([])           // 交卷后：{q, answer, correct}[]
const confirmVisible = ref(false) // 交卷确认弹窗
const reviewIndex = ref(0)        // 解析页当前索引
const examSeq = ref(0)            // 试卷序号
```

### 5.2 派生状态（computed）
```js
const currentQuestion = computed(() => paper.value[current.value] || null)
const total = computed(() => paper.value.length)
const answeredCount = computed(() => answers.value.filter((a) => a && a.length > 0).length)
// score / wrongCountInExam 在交卷后由 results 算出
```

### 5.3 作答 `toggleOption(optIndex)`
- 单选/判断：**单选**（先清空再设当前项）。
- 多选：**可多选**（有则删、无则加）。
- 存的是选项**下标**数组，已排序。

```js
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
```

### 5.4 判分 `isCorrect(q, ans)`
- 多选题**全对才给分**：答案下标集合与正确下标集合**完全一致**才算对。

```js
function isCorrect(q, ans) {
  if (!ans || ans.length === 0) return false
  return ans.length === q.answerIdx.length &&
    ans.every((v, i) => v === q.answerIdx[i])
}
```

### 5.5 交卷 `submit()`
```js
function submit() {
  const result = paper.value.map((q, i) => ({
    q, answer: answers.value[i] || [], correct: isCorrect(q, answers.value[i]),
  }))
  results.value = result
  recordWrongs(result)          // 把答错的题写进错题本
  phase.value = 'result'
}
```

---

## 6. 错题本（`localStorage` 持久化）

### 6.1 存储结构
只存错题的**元信息**（不存题目正文），key 为 `'exam-wrongs'`：

```js
const WRONGS_KEY = 'exam-wrongs'

function loadWrongsRaw() {
  try { return JSON.parse(localStorage.getItem(WRONGS_KEY)) || [] }
  catch { return [] }
}
function saveWrongs(list) {
  localStorage.setItem(WRONGS_KEY, JSON.stringify(list))
}
```

每条：
```js
{ id, source, myAnswer, at }
// id：题目 id；source：'real'|'mock'；myAnswer：我选的选项文本数组；at：时间戳
```

### 6.2 写入（交卷后）
```js
function recordWrongs(result) {
  const wrongs = loadWrongsRaw()
  for (const r of result) {
    if (r.correct) continue
    const myTexts = (r.answer || []).map((i) => r.q.options[i].text) // 存"文本"便于后续比对
    const existing = wrongs.find((w) => w.id === r.q.id && w.source === (r.q.source || 'real'))
    if (existing) { existing.myAnswer = myTexts; existing.at = Date.now() }
    else wrongs.push({ id: r.q.id, source: r.q.source, myAnswer: myTexts, at: Date.now() })
  }
  saveWrongs(wrongs)
}
```

### 6.3 读取（还原成完整题）
```js
function findQuestion(id, source) {
  const pool = source === 'mock' ? mockRef.value : realRef.value
  return pool.find((q) => q.id === id) || null
}
function wrongList() {
  return loadWrongsRaw()
    .map((w) => ({ ...w, q: findQuestion(w.id, w.source) }))
    .filter((x) => x.q)   // 题库里找不到的（题被删/改 id）自动过滤
}
```

### 6.4 删除/清空
```js
function removeWrong(id, source) {
  const wrongs = loadWrongsRaw().filter((w) => !(w.id === id && w.source === source))
  saveWrongs(wrongs)
}
function clearWrongs() { saveWrongs([]) }
```

### 6.5 错题回顾 `startReview()`
从错题本取题构建卷，进入 `review` 阶段；每题额外带 `myAnswerTexts`，用于显示"我的答案"并比对是否已掌握。

---

## 7. 组件划分

### 7.1 `ExamPage.vue`（顶层容器，按 `phase` 切五个视图）
```
phase === 'start'  -> 入口页：三张卡片（真题/模拟/错题本）
phase === 'exam'   -> 考试页：QuestionCard + 答题卡 + 上一题/下一题/交卷
phase === 'result' -> 结果页：得分 + 答对/答错/未答 + 查看解析
phase === 'review' -> 解析页：交卷后逐题看答案+解析+考点；或错题回顾
(每页都可能弹出)   -> 交卷确认弹窗（Teleport 到 body）
```
- **数据加载**（`onMounted`）：`Promise.all` 并行 `fetch('/quiz-data.json')` 和 `fetch('/quiz-mock.json')`；任一缺失/非法则整页显示"题库加载失败"。
  ```js
  onMounted(async () => {
    try {
      const [realRes, mockRes] = await Promise.all([
        fetch('/quiz-data.json'), fetch('/quiz-mock.json'),
      ])
      if (!realRes.ok || !mockRes.ok) throw new Error('bad status')
      const realData = await realRes.json()
      const mockData = await mockRes.json()
      if (!realData?.questions || !mockData?.questions) throw new Error('bad payload')
      realQuestions.value = realData.questions.map((q) => ({ ...q, source: 'real' }))
      mockQuestions.value = mockData.questions.map((q) => ({ ...q, source: 'mock' }))
    } catch {
      loadError.value = '题库加载失败，请刷新重试'
    }
  })
  ```
- 用 `exam.phase.value`、`exam.currentQuestion.value` 等（来自 `useExam` 返回对象）驱动模板，`phase`/`current` 等 ref 在模板里用 `.value` 访问（因为没解包）。

### 7.2 `QuestionCard.vue`（题目卡片，可复用）
Props：
```js
defineProps({
  question:    { type: Object, required: true },
  selected:    { type: Array, default: () => [] },   // 选中下标数组
  interactive: { type: Boolean, default: false },    // 是否可作答
  showResult:  { type: Boolean, default: false },    // 是否展示对错
  correct:     { type: Boolean, default: false },
})
```
- 头部显示题型标签（单选/多选/判断）、module、对错标记。
- 题干 + 选项列表；每题选项是一个 `<button>`，点击 `emit('select', i)`。
- 风格：作答态高亮选中（`eq-selected`）；结果态标绿（正确/`eq-right`）、标红（选错/`eq-wrong`）。
- 非 `interactive` 时 `disabled`（解析/回顾时只读）。

### 7.3 `AnswerSheet.vue`（答题卡/题号导航）
- 展示 1..total 的题号格子；点击 `emit('jump', i-1)` 跳题。
- 考试态：已答（`eq-cell-done`）、当前题（`eq-cell-current`）、未答。
- 回顾态：所有格子都标红表示错题（`eq-cell-wrong`），标题变为"错题导览"。
- 底部图例解释颜色。

### 7.4 组件如何被 Vue 使用（VitePress 集成）
- **全局注册**：`docs/.vitepress/theme/index.js` 里 `enhanceApp({app}) { app.component('ExamPage', ExamPage) }`，让所有 `.md` 页可用 `<ExamPage />`。
- **入口页**：`docs/exam.md` 直接写 `<ExamPage />`（VitePress 的 markdown 允许内嵌 Vue 组件；也支持顶部 `<script setup>` 显式 import，双保险）。
- **路由/导航**：`docs/.vitepress/config.mts` 的 `nav` 与 `sidebar` 里加 `{ text: '模拟考试', link: '/exam' }`。

---

## 8. 一份"线上考试平台"的从零搭建步骤

若你要脱离 VitePress，做一个**独立的线上考试平台**（Vue + 可选后端），步骤如下。考试核心逻辑（组卷/状态机/判分/错题本）可直接复用 §4–§6。

### Step 1：脚手架
```bash
# 用 Vite 建 Vue 3 项目
npm create vite@latest exam-platform -- --template vue
cd exam-platform
npm install
```
（如需后端，可再加 `npm install express`，或直接用 Node / Python FastAPI，任选。）

### Step 2：整理目录
```
exam-platform/
├── src/
│   ├── exam/
│   │   ├── useExam.js           # 直接复用本仓库的组卷/状态/判分/错题逻辑
│   │   ├── ExamPage.vue
│   │   ├── QuestionCard.vue
│   │   └── AnswerSheet.vue
│   ├── data/                    # 题库（或改成从后端 API 拉取）
│   │   ├── quiz-real.json
│   │   └── quiz-mock.json
│   ├── App.vue
│   └── main.js
└── index.html
```

### Step 3：数据获取（三种可选）
1. **静态打包**：把 JSON 放 `public/`，前端 `fetch('/quiz-real.json')`（和本仓库一致，最简单）。
2. **后端下发**：后端提供 `GET /api/quiz?type=mock`，前端 `fetch` 拉取题目数组。
3. **按需下发**：题目可分页、分模块下发，配合前端缓存。

### Step 4：状态管理（用组合式函数即可，无需 Pinia）
`useExam.js` 就是一个纯函数，内部用 `ref/computed` 管理状态，实例化一次即可跨组件共享。如果要"全局唯一一份考试状态"，把它放到一个模块级单例，或交给 `App.vue` 顶层 `provide`。

### Step 5：路由
- 单页式：用 `v-if` 按 `phase` 切换（本仓库做法，最简单）。
- 多页式：用 `vue-router`，如 `/exam`、`/result`、`/review`；用 query 或 store 传递试卷与结果。

### Step 6：判分与错题
- 判分逻辑直接复用 `isCorrect`（多选全对给分）。
- 错题本：本地用 `localStorage`；若要跨设备/长期留存/给 RL 训练做数据，则要**移到后端**（见 §9）。

### Step 7：样式
本仓库用 VitePress 的 CSS 变量（`var(--vp-c-brand)`、`var(--vp-c-bg)` 等）。独立项目建议换成你自己的变量或 Tailwind；把 `ExamPage.vue` 的 `<style scoped>` 里所有 `var(--vp-c-*)` 替换为自定义主题色即可。

---

## 9. 扩展为线上考试平台 / RL 训练平台（重点）

原系统是**纯前端、无用户、无后端**。要用于**强化学习（RL）**，建议按需增加：

### 9.1 需要补的模块
| 模块 | 说明 |
|---|---|
| 后端 API | `GET /api/questions`（按 type/module 下发）、`POST /api/exam/submit`（提交答卷并判分） |
| 用户/登录 | 账号体系（JWT / session），区分不同考生/训练实体 |
| 题目管理 | 后台增删改查题目（CRUD），对应 `quiz-mock.json` 的维护 |
| 答题记录持久化 | 把每次提交的 `{user, questions, answers, score, time}` 存库，用于统计/训练 |
| 错题本服务端化 | 错题元信息存服务器（而不是 localStorage），可跨设备 |
| 成绩统计 | 正确率、模块得分、错题分布、历史曲线 |
| 防作弊/可靠性 | 服务端判分（不信任前端分数）、限时、题序加密下发等 |

### 9.2 RL 交互接口设计（关键）
把"考试环境"抽象成 RL 需要的接口，让 agent 能"做题-拿反馈-学策略"：

| RL 概念 | 考试系统对应 |
|---|---|
| 环境（Environment） | 一场考试/一套题（题库 + 组卷规则 + 评分规则） |
| 状态（State, s） | 当前题 + 已作答序列 + 剩余题 + 模块分布（可含题干/选项的向量化表示） |
| 动作（Action, a） | 对当前题的作答（选 A/B/C…，单选题直接选一项；多选=对子集投票） |
| 奖励（Reward, r） | 交卷评分：答对得分 / 答错扣分 / 模块权重加权；可用 `-1/-0/+1` 或细粒度如"当前题答对+1、超时-0.1" |
| 回合（Episode） | 一场 60 题的考试（一次完整组卷→逐题作答→交卷） |
| 策略（Policy） | agent 如何在给定题面上选择答案（可基于语言模型、检索、或决策网络） |

建议后端提供：
- `POST /api/agent/episode/start`：按规则组一卷，返回题目（可脱敏/向量化）+ 每题作答空间。
- `POST /api/agent/episode/step`：agent 对当前题给出 `action`，返回 `reward` + `next_state` + `done`。
- `POST /api/agent/episode/end`：结算本回合累计奖励，写训练记录。
- `GET /api/agent/stats`：训练统计（历史 reward、正确率、模块表现），供 RL 循环读取。

这样 RL agent 把"考试平台"当作一个可交互的**环境**，通过"做题→得分→调整策略"不断学习。题面、奖励、状态都可以按 RL 需求自定义。

### 9.3 关于"题库来源"的提醒
- 原仓库**真题是生成产物**（`doc/A卷还原.md` → `tools/parse-quiz.mjs` → `quiz-data.json`），改题要改源再生成，别手改 `quiz-data.json`。
- 模拟题（`quiz-mock.json`）可直接增改，但要**维持题型格式**（§3.1）与**分布**（§4.1）以匹配组卷配比。
- 若 RL 平台要生成大量题目，建议题库、题目编辑器、判分规则都做成**数据驱动**，便于批量生产。

---

## 10. 常见坑与注意事项

1. **fetch 失败会整页报错**：`ExamPage` 加载题库时任一请求异常即显示"题库加载失败"。线上平台若题库在下发前就配置好，也要有加载态/错误重试。
2. **错题本只存元信息**：`localStorage` 只存 `{id, source, myAnswer, at}`，题目本体每次 `findQuestion` 从题库里取。所以**题库里被删除/改 id 的题，错题会自动失效被过滤**。
3. **选项顺序随机 vs 判分**：`shuffleOptions` 打乱选项后，用 `answerIdx`（数字下标）判分，而不是字母；错题本存的是**文本**`myAnswer`，用于二次比对文本是否等于正确答案文本。
4. **多选题全对才给分**：`isCorrect` 要求集合完全一致；部分选对不得分——这是常见评分口径，若要"选对部分给部分分"，需要自己改。
5. **组卷配比依赖题库分布**：某 `(type, module)` 池不足时会从剩余补，破坏配比。所以题库要按 `module 3:2:2:2:1`、`type 3:1:2` 供题。
6. **`useExam` 用 ref 未解包**：在模板中访问 `exam.phase.value`、`exam.currentQuestion.value`（因为从 return 对象取值，Vue 不会自动解包嵌套 ref）。
7. **两套题库要隔离**：`source` 字段区分真题/模拟题，组卷、错题、重练都要按 `source` 取值，避免混用。
8. **判断题格式固定**：`judge` 的 options 永远是 `[{A:正确},{B:错误}]`，答案 1 个（A/B）。

---

## 11. 一句话总结

> **数据驱动 + 组合式状态机**：题库 JSON 决定内容，组卷函数按"结构+比例"抽题并打乱选项；`useExam` 用 `ref/computed` 维护 `start→exam→result→review` 五态；`QuestionCard`/`AnswerSheet` 是纯展示+交互组件；判分用下标集合全等，错题本用 `localStorage` 存元信息。

把这套"题库 schema + 组卷 + 状态机 + 判分 + 错题本"抽出来，就是一个可复用的考试内核。加上**后端 API、用户体系、答题记录与 RL 环境接口**，就能从静态练习页升级成**线上考试 / RL 训练平台**。
