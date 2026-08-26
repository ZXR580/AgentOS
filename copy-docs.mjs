import { copyFileSync, existsSync, mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const srcDir = join(__dirname, '..', 'KnowledgeBase')
const dstDir = join(__dirname, 'docs')

if (!existsSync(srcDir)) {
  console.log('[copy-docs] KnowledgeBase 未找到，跳过同步（docs/ 即为内容源）')
  process.exit(0)
}

const files = [
  'ch01_ai_foundation.md',
  'ch02_os_linux.md',
  'ch03_software.md',
  'ch04_agent.md',
  'ch05_hardware.md',
  'ch06_appendix.md',
  'ch07_mcp_agent_practice.md',
  'ch08_intelligent_platform.md',
]

mkdirSync(dstDir, { recursive: true })
for (const f of files) {
  const src = join(srcDir, f)
  if (!existsSync(src)) {
    console.log(`[copy-docs] 源文件缺失，跳过: ${src}（保留现有 docs/${f}）`)
    continue
  }
  copyFileSync(src, join(dstDir, f))
  console.log('copied', f)
}
