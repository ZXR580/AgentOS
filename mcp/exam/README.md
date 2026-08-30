# 考试系统 MCP（Host / Client / Server）

把本仓库的"在线考试系统"做成了**真正可调用的 MCP（Model Context Protocol）**：内核逻辑（校验 / 组卷 / 判分 / 错题本）暴露为一组 MCP 工具，任何支持 MCP 的 Host（opencode、Claude Desktop、Cursor 等）都能通过 stdio 接入并调用。

> 约定：MCP Server 提供**确定性逻辑**。"生成题目内容"由 Host 侧的 LLM 负责——先生成候选题目 JSON，再调用本 Server 的 `validate_questions` / `assemble_paper` 完成校验与装配。这样 Server 不依赖任何 LLM，且真正可执行、有返回。

## 目录

```
mcp-exam/
├── exam_engine.py     # 纯逻辑内核（校验/组卷/判分/错题本），无 MCP 依赖，可当库用
├── server.py          # MCP Server：用 FastMCP 暴露 8 个工具（stdio）
├── client_test.py     # 标准 Client 流程演示：握手→列工具→调用
├── requirements.txt   # 依赖：mcp
└── wrong_store.json   # 错题本持久化文件（运行时生成）
```

## 安装

```bash
cd mcp-exam
py -3 -m pip install -r requirements.txt   # 用装了 mcp 的解释器；GUI 环境亦可 python -m venv .venv
```

## 三大角色（标准 MCP 结构）

| 角色 | 在本项目是谁 | 做什么 |
|---|---|---|
| **Server** | `server.py` | 实际提供能力：暴露 validate / assemble / grade / wrong_* 工具 |
| **Client** | 连接器（opencode 内部自动建的 Client；或 `client_test.py` 演示） | 与 Server 保持 1:1 协议连接（stdio），发起握手、发请求、把结果转回 Host |
| **Host** | opencode（本仓库）或 Claude Desktop / Cursor | 用户直接使用的 AI 应用，决定接入哪些 Server |

- Host 与 Client 是**包含/实例化**关系（Client 住在 Host 里）；真正发生协议连接的是 **Client ↔ Server**。
- 本仓库用 **stdio**：Client 拉起 `server.py` 进程、经标准输入输出通信；协议走 stdout、日志走 stderr（已在 server 里避开 stdout 日志）。

## Server 提供的工具

| 工具 | 入参 | 返回 |
|---|---|---|
| `validate_questions` | `questions: list` | `{valid, total, errors[]}` |
| `assemble_paper` | `questions, single=30, multi=10, judge=20, shuffle=True` | `{paper, structure}` |
| `grade_paper` | `paper, answers` | `{score, total, wrong[], results[]}` |
| `wrong_add` | `wrongs: [{id, source, myAnswer}]` | `{added, total}` |
| `wrong_list` | — | 错题本记录数组 |
| `wrong_remove` | `qid, source="mock"` | `{removed, total}` |
| `wrong_clear` | — | `{cleared, total:0}` |
| `generate_questions` | `material, module, chapter, single, multi, judge` | **生成题目**：内部调用 LLM 按出题规范生成候选，自动校验，返回 `{valid, errors, questions}`（id 自动续号、source=mock） |

> **生成题目完全由 MCP 承载（不依赖 skill）**：`generate_questions` 内部调用一个 LLM（OpenAI 兼容接口，默认 Ollama），按内置出题规范生成候选 JSON，再自动做 `validate_questions` 校验。通过环境变量配置 LLM：
> ```bash
> set LLM_BASE=http://localhost:11434/v1   # 默认 Ollama 的 OpenAI 兼容端点
> set LLM_MODEL=qwen2.5:7b
> set LLM_KEY=                             # 若用云端 API 填 key
> ```
> 未配/不可用时，`generate_questions` 会返回"LLM 调用失败"提示，其余工具不受影响。

题目对象 schema（与仓库 `quiz-mock.json` 一致）：

```json
{
  "id": "M001",
  "type": "single" | "multi" | "judge",
  "module": "ai|os|software|agent|hardware",
  "stem": "题干",
  "options": [{"key":"A","text":"…"}],
  "answerKeys": ["A"],
  "explanation": "解析：对的原因 + 每个错项为何错",
  "chapter": "/ch01_ai_foundation",
  "source": "mock"
}
```

题型规则：`single` 4 项 / 1 正确；`multi` 6 项 / 3~4 正确（全对才给分）；`judge` 固定 [{A=正确},{B=错误}] / 1 答案。

## 如何接入

### 方式一：作为 opencode 的 MCP（Host = opencode，本仓库）

在 `.opencode/opencode.json` 里注册本地 Server（opencode 启动时其内部 Client 会自动建连）：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "exam": {
      "type": "local",
      "command": ["py", "-3", "mcp-exam/server.py"],
      "enabled": true
    }
  }
}
```

> 说明：`command` 用能加载 `mcp` SDK 的解释器（本机用 `py -3`，因为它指向装了 mcp 的 Python 3.13；若你的默认 `python` 已装 mcp，可直接用 `"python"`）。Windows 下若用别的绝对路径，写法如 `["D:\\Python\\python.exe", "mcp-exam\\server.py"]`。

之后 opencode（Host）会把 `validate_questions` 等当作可调用工具暴露给模型，模型直接调用。

### 方式二：任意 MCP 客户端 / Claude Desktop

Claude Desktop 的 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "exam": {
      "command": "python",
      "args": ["C:\\path\\to\\mcp-exam\\server.py"]
    }
  }
}
```

### 方式三：命令行冒烟测试（Client 标准操作）

```bash
cd mcp-exam
py -3 client_test.py
```

它会走一遍标准 MCP 流程：`initialize` 握手 → `tools/list` → `tools/call`（validate / assemble / grade / wrong_*）。

## 一个完整调用示例（用 Python 客户端）

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio

SERVER = "C:\\path\\to\\mcp-exam\\server.py"

async def main():
    p = StdioServerParameters(command="python", args=[SERVER])
    async with stdio_client(p) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()                       # 握手
            res = await s.call_tool("validate_questions", {"questions": [...]})
            print(res.content[0].text)                 # {valid, errors}
            res = await s.call_tool("assemble_paper", {"questions": [...], "single": 30, "multi": 10, "judge": 20})
            print(res.content[0].text)

asyncio.run(main())
```

## 与仓库其它部分的分工

- 前端 `ExamPage` / `useExam`：浏览器端的练习/考试 UI（`source:"mock"` 题库可继续由仓库维护）。
- 本 MCP：**服务端可调用的考试逻辑**，供 AI Host（opencode 等）编排、校验、判分、维护错题本。
- 出题内容：由 Host 侧 LLM 按 `.opencode/skills/exam-builder/SKILL.md` 的模板生成候选题 → 调 `validate_questions` 校验。
