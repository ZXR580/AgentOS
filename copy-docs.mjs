import { copyFileSync, existsSync, mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const srcDir = join(__dirname, '..', 'KnowledgeBase')
const dstDir = join(__dirname, 'docs')

const files = [
  'ch01_ai_foundation.md',
  'ch02_os_linux.md',
  'ch03_software.md',
  'ch04_agent.md',
  'ch05_hardware.md',
  'ch06_appendix.md',
  'ch07_mcp_agent_practice.md',
]

mkdirSync(dstDir, { recursive: true })
for (const f of files) {
  const src = join(srcDir, f)
  if (!existsSync(src)) {
    // 源文件缺失时跳过并保留现有 docs 版本，避免同步脚本中断构建
    console.warn(`[copy-docs] 跳过缺失的源文件: ${src}（保留现有 docs/${f}）`)
    continue
  }
  copyFileSync(src, join(dstDir, f))
  console.log('copied', f)
}
