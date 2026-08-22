<script setup>
import { ref, onMounted, computed } from 'vue'
import { useExam } from './useExam'
import QuestionCard from './QuestionCard.vue'
import AnswerSheet from './AnswerSheet.vue'

const realQuestions = ref([])
const mockQuestions = ref([])
const loadError = ref('')
const exam = useExam(realQuestions, mockQuestions)
const activeSource = ref('real')

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

onMounted(async () => {
  try {
    const [realRes, mockRes] = await Promise.all([
      fetch('/quiz-data.json'),
      fetch('/quiz-mock.json'),
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

function startExam(source) {
  activeSource.value = source
  if (!exam.start(source)) {
    alert('当前题库暂无可用题目')
  }
}

function fmtAnswer(idxArr) {
  return idxArr.map((i) => LETTERS[i]).join(',') || '未作答'
}

function sectionTitle(i) {
  if (i < 30) return '一、单项选择题'
  if (i < 40) return '二、多项选择题'
  return '三、判断题'
}

const wrongTotal = computed(() => exam.wrongCount())

const reviewItem = computed(() => {
  const q = exam.paper.value[exam.reviewIndex.value]
  if (!q) return null
  const texts = q.myAnswerTexts || []
  const myIdx = q.options
    .map((o) => o.text)
    .map((t, i) => (texts.includes(t) ? i : -1))
    .filter((i) => i >= 0)
    .sort((a, b) => a - b)
  const correct =
    myIdx.length === q.answerIdx.length && myIdx.every((v, i) => v === q.answerIdx[i])
  return { q, myIdx, correct }
})

function removeCurrentWrong() {
  const q = exam.paper.value[exam.reviewIndex.value]
  if (!q) return
  exam.removeWrong(q.id, q.source)
  exam.startReview()
  exam.reviewIndex.value = 0
}
</script>

<template>
  <div class="exam">
    <p v-if="loadError" class="exam-error">{{ loadError }}</p>

    <!-- 入口页 -->
    <div v-else-if="exam.phase.value === 'start'" class="exam-start">
      <h2>模拟考试</h2>
      <div class="exam-start-cards">
        <div class="exam-entry-card">
          <h3>真题练习</h3>
          <p>从 A/B 卷 120 道真题题库随机组卷 60 题，按官方结构（单选 30 + 多选 10 + 判断 20）与模块占比抽取，选项顺序随机。</p>
          <button class="eq-btn eq-btn-primary" @click="startExam('real')">开始真题练习</button>
        </div>
        <div class="exam-entry-card">
          <h3>模拟练习</h3>
          <p>从 AI 生成的 300 道模拟题库随机组卷，覆盖相同知识点与模块配比，与真题题库完全隔离。</p>
          <button class="eq-btn eq-btn-primary" @click="startExam('mock')">开始模拟练习</button>
        </div>
        <div class="exam-entry-card">
          <h3>错题本</h3>
          <p>
            真题与模拟练习中答错的题自动收录于此，包含解析与正确答案，可反复回顾或重练。
            当前错题：<strong>{{ wrongTotal }}</strong> 题。
          </p>
          <div class="exam-entry-actions">
            <button class="eq-btn" :disabled="wrongTotal === 0" @click="exam.startReview()">
              回顾错题
            </button>
            <button class="eq-btn" :disabled="wrongTotal === 0" @click="startExam('wrong')">
              重练错题
            </button>
            <button class="eq-btn eq-btn-danger" :disabled="wrongTotal === 0" @click="exam.clearWrongs()">
              清空错题
            </button>
          </div>
        </div>
      </div>
      <p class="exam-start-note">考试不限时。答题阶段不显示答案与解析，提交后打分，之后可逐题查看解析。</p>
    </div>

    <!-- 考试页 -->
    <div v-else-if="exam.phase.value === 'exam'" class="exam-body">
      <div class="exam-main">
        <div class="exam-source-tag">
          {{ activeSource === 'mock' ? '模拟练习' : activeSource === 'wrong' ? '错题重练' : '真题练习' }}
        </div>
        <QuestionCard
          :question="exam.currentQuestion.value"
          :selected="exam.answers.value[exam.current.value] || []"
          :interactive="true"
          @select="exam.toggleOption"
        />
        <div class="exam-nav">
          <button class="eq-btn" :disabled="exam.current.value === 0" @click="exam.current.value--">
            上一题
          </button>
          <span class="exam-progress">{{ exam.current.value + 1 }} / {{ exam.total.value }}</span>
          <button
            class="eq-btn"
            :disabled="exam.current.value >= exam.total.value - 1"
            @click="exam.current.value++"
          >
            下一题
          </button>
          <button class="eq-btn eq-btn-primary" @click="exam.confirmVisible.value = true">
            提交试卷
          </button>
        </div>
      </div>
      <aside class="exam-side">
        <AnswerSheet
          :total="exam.total.value"
          :answers="exam.answers.value"
          :current="exam.current.value"
          @jump="(i) => (exam.current.value = i)"
        />
      </aside>
    </div>

    <!-- 结果页 -->
    <div v-else-if="exam.phase.value === 'result'" class="exam-result">
      <div class="exam-result-score">
        <span class="exam-score-num">{{ exam.score.value }}</span>
        <span class="exam-score-total">/ {{ exam.total.value }}</span>
      </div>
      <div class="exam-result-stats">
        <span>答对 {{ exam.score.value }} 题</span>
        <span>答错 {{ exam.wrongCountInExam.value }} 题</span>
        <span>未答 {{ exam.total.value - exam.answeredCount.value }} 题</span>
      </div>
      <div class="exam-result-actions">
        <button class="eq-btn eq-btn-primary" @click="exam.gotoReview(0)">查看解析</button>
        <button class="eq-btn" :disabled="wrongTotal === 0" @click="startExam('wrong')">
          错题重练（{{ wrongTotal }}）
        </button>
        <button class="eq-btn" @click="exam.restart()">返回</button>
      </div>
    </div>

    <!-- 解析页（考试交卷后） -->
    <div v-else-if="exam.phase.value === 'review' && !reviewItem?.q?.myAnswerTexts" class="exam-review">
      <div class="exam-review-head">
        <span class="exam-review-section">{{ sectionTitle(exam.reviewIndex.value) }}</span>
        <span class="exam-review-counter">
          {{ exam.reviewIndex.value + 1 }} / {{ exam.total.value }}
        </span>
      </div>
      <QuestionCard
        :question="exam.results.value[exam.reviewIndex.value].q"
        :selected="exam.results.value[exam.reviewIndex.value].answer"
        :show-result="true"
        :correct="exam.results.value[exam.reviewIndex.value].correct"
      />
      <div class="exam-analysis">
        <p><strong>我的答案：</strong>{{ fmtAnswer(exam.results.value[exam.reviewIndex.value].answer) }}</p>
        <p>
          <strong>正确答案：</strong>{{ fmtAnswer(exam.results.value[exam.reviewIndex.value].q.answerIdx) }}
          <a class="exam-link" :href="exam.results.value[exam.reviewIndex.value].q.chapter" target="_blank">查看考点</a>
        </p>
        <div class="exam-analysis-text">{{ exam.results.value[exam.reviewIndex.value].q.explanation }}</div>
      </div>
      <div class="exam-nav">
        <button
          class="eq-btn"
          :disabled="exam.reviewIndex.value === 0"
          @click="exam.reviewIndex.value--"
        >
          上一题
        </button>
        <button
          class="eq-btn"
          :disabled="exam.reviewIndex.value >= exam.total.value - 1"
          @click="exam.reviewIndex.value++"
        >
          下一题
        </button>
        <button class="eq-btn eq-btn-primary" @click="exam.restart()">返回</button>
      </div>
    </div>

    <!-- 错题回顾页 -->
    <div v-else-if="exam.phase.value === 'review' && reviewItem" class="exam-review">
      <div class="exam-review-head">
        <span class="exam-review-section">错题回顾</span>
        <span class="exam-review-counter">
          {{ exam.reviewIndex.value + 1 }} / {{ exam.total.value }}
        </span>
      </div>
      <QuestionCard
        :question="reviewItem.q"
        :selected="reviewItem.myIdx"
        :show-result="true"
        :correct="reviewItem.correct"
      />
      <div class="exam-analysis">
        <p>
          <strong>我的答案：</strong>{{ fmtAnswer(reviewItem.myIdx) }}
          <span :class="reviewItem.correct ? 'exam-mark-good' : 'exam-mark-bad'">
            {{ reviewItem.correct ? '（已掌握）' : '（答错）' }}
          </span>
        </p>
        <p>
          <strong>正确答案：</strong>{{ fmtAnswer(reviewItem.q.answerIdx) }}
          <a class="exam-link" :href="reviewItem.q.chapter" target="_blank">查看考点</a>
        </p>
        <div class="exam-analysis-text">{{ reviewItem.q.explanation }}</div>
      </div>
      <div class="exam-nav">
        <button
          class="eq-btn"
          :disabled="exam.reviewIndex.value === 0"
          @click="exam.reviewIndex.value--"
        >
          上一题
        </button>
        <button
          class="eq-btn"
          :disabled="exam.reviewIndex.value >= exam.total.value - 1"
          @click="exam.reviewIndex.value++"
        >
          下一题
        </button>
        <button class="eq-btn eq-btn-danger" @click="removeCurrentWrong">移出本错题</button>
        <button class="eq-btn eq-btn-primary" @click="exam.restart()">返回</button>
      </div>
      <aside class="exam-side-review">
        <AnswerSheet
          :total="exam.total.value"
          :answers="exam.answers.value"
          :current="exam.reviewIndex.value"
          :review="true"
          @jump="(i) => (exam.reviewIndex.value = i)"
        />
      </aside>
    </div>

    <!-- 提交确认弹窗 -->
    <Teleport to="body">
      <div v-if="exam.confirmVisible.value" class="exam-mask" @click.self="exam.confirmVisible.value = false">
        <div class="exam-dialog">
          <h3>确认交卷？</h3>
          <p>
            已答 <strong>{{ exam.answeredCount.value }}</strong> 题，未答
            <strong>{{ exam.total.value - exam.answeredCount.value }}</strong> 题。
          </p>
          <p class="exam-dialog-tip">交卷后无法修改答案，将立即评分，答错的题会自动进入错题本。</p>
          <div class="exam-dialog-actions">
            <button class="eq-btn" @click="exam.confirmVisible.value = false">继续作答</button>
            <button class="eq-btn eq-btn-primary" @click="exam.submit()">确认交卷</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.exam {
  min-height: 60vh;
}
.exam-error {
  color: #ef4444;
  text-align: center;
  padding: 60px 0;
}
.exam-start {
  max-width: 860px;
  margin: 0 auto;
  padding: 20px 0 60px;
  text-align: center;
}
.exam-start h2 {
  font-size: 24px;
  margin-bottom: 20px;
}
.exam-start-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  text-align: left;
}
.exam-entry-card {
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.exam-entry-card h3 {
  margin: 0;
  font-size: 17px;
}
.exam-entry-card p {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--vp-c-text-2);
  flex: 1;
}
.exam-entry-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.exam-start-note {
  margin-top: 20px;
  font-size: 13px;
  color: var(--vp-c-text-3);
}
.exam-body {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}
.exam-main {
  flex: 1;
  min-width: 0;
}
.exam-side {
  width: 260px;
  flex-shrink: 0;
  position: sticky;
  top: 90px;
}
.exam-side-review {
  margin-top: 18px;
  max-width: 360px;
}
.exam-source-tag {
  display: inline-block;
  font-size: 12px;
  color: var(--vp-c-brand);
  background: var(--vp-c-brand-soft);
  border-radius: 10px;
  padding: 2px 12px;
  margin-bottom: 10px;
}
.exam-nav {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
  flex-wrap: wrap;
}
.exam-progress {
  color: var(--vp-c-text-2);
  font-size: 13px;
}
.exam-result {
  text-align: center;
  padding: 60px 0;
}
.exam-result-score {
  font-size: 72px;
  font-weight: 700;
  color: var(--vp-c-brand);
  line-height: 1;
}
.exam-score-total {
  font-size: 24px;
  color: var(--vp-c-text-3);
  font-weight: 400;
}
.exam-result-stats {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin: 20px 0 30px;
  color: var(--vp-c-text-2);
}
.exam-result-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}
.exam-review-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.exam-review-section {
  font-weight: 600;
  color: var(--vp-c-text-1);
}
.exam-review-counter {
  color: var(--vp-c-text-3);
  font-size: 13px;
}
.exam-analysis {
  margin-top: 18px;
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: 10px;
  padding: 16px 18px;
  font-size: 14px;
  line-height: 1.8;
  color: var(--vp-c-text-1);
}
.exam-analysis-text {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--vp-c-divider);
  color: var(--vp-c-text-2);
}
.exam-link {
  margin-left: 12px;
  color: var(--vp-c-brand);
  font-size: 13px;
  text-decoration: none;
}
.exam-link:hover {
  text-decoration: underline;
}
.exam-mark-good {
  color: #22c55e;
  font-size: 12px;
  margin-left: 6px;
}
.exam-mark-bad {
  color: #ef4444;
  font-size: 12px;
  margin-left: 6px;
}
.exam-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.exam-dialog {
  background: var(--vp-c-bg);
  border-radius: 12px;
  padding: 26px 30px;
  width: 420px;
  max-width: calc(100vw - 40px);
  color: var(--vp-c-text-1);
}
.exam-dialog h3 {
  margin: 0 0 12px;
}
.exam-dialog-tip {
  color: var(--vp-c-text-3);
  font-size: 13px;
}
.exam-dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}
.eq-btn {
  padding: 8px 18px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s;
}
.eq-btn:hover:not(:disabled) {
  border-color: var(--vp-c-brand);
  color: var(--vp-c-brand);
}
.eq-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.eq-btn-primary {
  background: var(--vp-c-brand);
  border-color: var(--vp-c-brand);
  color: #fff;
}
.eq-btn-primary:hover:not(:disabled) {
  background: var(--vp-c-brand-2);
  color: #fff;
}
.eq-btn-danger {
  border-color: #ef4444;
  color: #ef4444;
}
.eq-btn-danger:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}
@media (max-width: 900px) {
  .exam-body {
    flex-direction: column-reverse;
  }
  .exam-side {
    width: 100%;
    position: static;
  }
}
</style>
