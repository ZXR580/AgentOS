import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = join(__dirname, '..')

const MODULE_OF_CHAPTER = {
  ch01: 'ai', ch02: 'os', ch03: 'software', ch04: 'agent', ch05: 'hardware',
}
const CHAPTER_PATH = {
  ch01: '/ch01_ai_foundation', ch02: '/ch02_os_linux', ch03: '/ch03_software',
  ch04: '/ch04_agent', ch05: '/ch05_hardware',
}

// 题号 -> 章节（来自覆盖度验证映射）
const A_MAP = {
  1:'ch01',2:'ch02',3:'ch02',4:'ch01',5:'ch02',6:'ch02',7:'ch04',8:'ch05',9:'ch04',10:'ch03',
  11:'ch01',12:'ch03',13:'ch04',14:'ch02',15:'ch04',16:'ch05',17:'ch01',18:'ch04',19:'ch05',20:'ch04',
  21:'ch03',22:'ch01',23:'ch02',24:'ch04',25:'ch04',26:'ch04',27:'ch04',28:'ch04',29:'ch02',30:'ch03',
  31:'ch03',32:'ch05',33:'ch04',34:'ch05',35:'ch02',36:'ch04',37:'ch01',38:'ch04',39:'ch02',40:'ch01',
  41:'ch05',42:'ch02',43:'ch01',44:'ch05',45:'ch01',46:'ch04',47:'ch02',48:'ch04',49:'ch04',50:'ch01',
  51:'ch02',52:'ch04',53:'ch04',54:'ch03',55:'ch04',56:'ch04',57:'ch05',58:'ch05',59:'ch03',60:'ch04',
}
const B_MAP = {
  1:'ch02',2:'ch02',3:'ch01',4:'ch04',5:'ch04',6:'ch01',7:'ch02',8:'ch03',9:'ch04',10:'ch01',
  11:'ch05',12:'ch04',13:'ch05',14:'ch02',15:'ch01',16:'ch02',17:'ch01',18:'ch02',19:'ch02',20:'ch04',
  21:'ch02',22:'ch03',23:'ch04',24:'ch03',25:'ch03',26:'ch04',27:'ch01',28:'ch05',29:'ch04',30:'ch04',
  31:'ch01',32:'ch02',33:'ch02',34:'ch02',35:'ch04',36:'ch04',37:'ch04',38:'ch02',39:'ch01',40:'ch03',
  41:'ch05',42:'ch02',43:'ch04',44:'ch01',45:'ch05',46:'ch03',47:'ch02',48:'ch01',49:'ch04',50:'ch02',
  51:'ch03',52:'ch02',53:'ch04',54:'ch02',55:'ch01',56:'ch04',57:'ch05',58:'ch04',59:'ch04',60:'ch04',
}

function parsePaper(file, prefix, chapterMap) {
  const text = readFileSync(join(root, 'doc', file), 'utf-8')
  const lines = text.split(/\r?\n/)
  const questions = []
  let section = null
  let cur = null

  const TYPE_MAP = { '一、单项选择题': 'single', '二、多项选择题': 'multi', '三、判断题': 'judge' }

  for (const line of lines) {
    const secMatch = line.match(/^## (一、单项选择题|二、多项选择题|三、判断题)/)
    if (secMatch) { section = TYPE_MAP[secMatch[1]]; continue }

    const qMatch = line.match(/^### (\d+)\.\s*(.+?)(?:（\s*）|\(\s*\))?\s*$/)
    if (qMatch) {
      if (cur) questions.push(cur)
      const num = parseInt(qMatch[1], 10)
      cur = {
        id: `${prefix}${num}`,
        type: section,
        module: MODULE_OF_CHAPTER[chapterMap[num]] || 'ai',
        stem: qMatch[2].trim(),
        options: [],
        answerKeys: [],
        explanation: '',
        chapter: CHAPTER_PATH[chapterMap[num]] || '/',
        source: prefix + '卷',
      }
      continue
    }

    if (!cur) continue

    const optMatch = line.match(/^- ([A-F])\.\s*(.+)$/)
    if (optMatch) { cur.options.push({ key: optMatch[1], text: optMatch[2].trim() }); continue }

    const ansMatch = line.match(/^<summary>参考答案[：:]\s*([A-F]+)(?:（[^）]*）)?\s*<\/summary>/)
    if (ansMatch) {
      cur.answerKeys = ansMatch[1].split('')
      continue
    }

    if (line === '</details>') {
      if (cur) questions.push(cur)
      cur = null
      continue
    }

    if (cur && cur.answerKeys.length > 0 && cur.explanation === '') {
      if (line.trim()) cur.explanation += line.trim() + '\n'
    }
  }
  if (cur) questions.push(cur)
  return questions
}

const all = [
  ...parsePaper('A卷还原.md', 'A', A_MAP),
  ...parsePaper('B卷还原.md', 'B', B_MAP),
]

all.forEach((q) => { q.explanation = q.explanation.trim() })

const out = join(root, 'docs', 'public', 'quiz-data.json')
mkdirSync(dirname(out), { recursive: true })
writeFileSync(out, JSON.stringify({ questions: all }, null, 2), 'utf-8')

const count = (t) => all.filter((q) => q.type === t).length
console.log(`total=${all.length} single=${count('single')} multi=${count('multi')} judge=${count('judge')}`)
const bad = all.filter((q) => !q.stem || q.options.length === 0 || q.answerKeys.length === 0 || !q.explanation)
console.log(`问题条目: ${bad.length}`)
bad.forEach((q) => console.log('  BAD:', q.id, q.stem.slice(0, 30)))
