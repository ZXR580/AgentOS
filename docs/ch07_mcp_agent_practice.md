# 第 7 章 MCP 服务器与 Agent 落地实践

本章以实操模拟题为模板，给出可运行的落地方法，与第 4 章的概念内容互补。

## 7.1 环境准备

比赛环境为 UOS 桌面系统，Python 3.10 及以上版本。

```bash
# 创建项目目录和虚拟环境
mkdir -p ~/student-score-mcp
cd ~/student-score-mcp
python3 -m venv .venv
source .venv/bin/activate

# 安装 MCP SDK
pip install mcp fastmcp
```

- 虚拟环境隔离项目依赖，避免污染系统 Python
- MCP 官方 SDK 提供 FastMCP 类，一行装饰器即可注册工具
- 若环境无网络，可提前准备依赖包离线安装

## 7.2 MCP 传输方式

MCP 支持两种传输模式：

| 传输 | 说明 | 适用 |
|---|---|---|
| stdio | 客户端启动服务器进程，通过标准输入输出通信 | 本地工具，比赛场景 |
| HTTP/SSE | 服务器独立运行，客户端通过网络访问 | 远程服务 |

- stdio 模式下客户端配置文件指定启动命令，客户端负责拉起进程
- 服务器通过 stdout 输出协议消息，日志必须写到 stderr 或文件，避免污染协议流

## 7.3 从零开发 MCP 服务器

以学生成绩查询服务为模板，完成三个工具：查询成绩、成绩统计、新增成绩。

### 项目结构

```
student-score-mcp/
├── server.py          # MCP 服务器入口，注册工具
├── data.py            # 数据读写层，JSON 持久化
└── students.json      # 数据文件，程序启动时自动创建
```

### 数据层：JSON 持久化

数据必须存到本地文件，服务重启后重新加载，保证数据不丢失。

```python
import json
from pathlib import Path

DATA_FILE = Path(__file__).parent / "students.json"

def load_students() -> list[dict]:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return [
        {"name": "李明", "course": "智能体应用开发", "score": 85},
        {"name": "王雪", "course": "智能体应用开发", "score": 58},
    ]

def save_students(students: list[dict]) -> None:
    DATA_FILE.write_text(
        json.dumps(students, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
```

- ensure_ascii=False 保证中文以原文写入，indent=2 方便人工检查
- 每次修改数据后立即写回文件

### 服务器与工具实现

```python
from fastmcp import FastMCP

mcp = FastMCP("student-score")


@mcp.tool()
def query_student(name: str) -> str:
    """按姓名查询学生成绩，返回课程、分数和是否通过。"""
    students = load_students()
    for s in students:
        if s["name"] == name:
            passed = "通过" if s["score"] >= 60 else "未通过"
            return f"{s['name']} | {s['course']} | {s['score']} | {passed}"
    return "未找到相关学生"


@mcp.tool()
def score_statistics() -> str:
    """统计全部学生：总人数、通过人数、未通过人数、最高分、最低分、平均分。"""
    students = load_students()
    if not students:
        return "暂无学生数据"
    scores = [s["score"] for s in students]
    passed = sum(1 for v in scores if v >= 60)
    avg = sum(scores) / len(scores)
    return (
        f"总人数:{len(students)} 通过:{passed} 未通过:{len(students)-passed} "
        f"最高:{max(scores)} 最低:{min(scores)} 平均:{avg:.2f}"
    )


@mcp.tool()
def add_student(name: str, course: str, score: int) -> str:
    """新增一名学生的成绩，保存到本地数据文件。"""
    students = load_students()
    students.append({"name": name, "course": course, "score": score})
    save_students(students)
    return f"已新增学生 {name}"


if __name__ == "__main__":
    mcp.run()  # 默认 stdio 模式
```

- 工具参数由函数签名自动生成 schema，类型注解和默认值会反映到参数定义
- 工具返回值统一用字符串，客户端易读
- 查询不存在的学生返回明确提示，服务进程继续运行

### 本地调试

```bash
# 方式一：在 MCP 客户端中调试
mcp dev server.py

# 方式二：直接用 Python 脚本调用工具函数
python3 -c "from server import query_student; print(query_student('李明'))"
```

- 先单测工具函数逻辑，再测 MCP 协议层
- 服务日志写到 stderr，用 2> 重定向保存

## 7.4 接入客户端

客户端配置文件以 JSON 声明服务器启动命令，常见配置如下：

```json
{
  "mcpServers": {
    "student-score": {
      "command": "python3",
      "args": ["/home/student/student-score-mcp/server.py"],
      "env": {
        "PATH": "/home/student/student-score-mcp/.venv/bin:/usr/bin"
      }
    }
  }
}
```

- command 和 args 组合成实际启动命令，必须能独立运行
- 使用虚拟环境的 python 时通过 env 指定 PATH，否则可能找不到依赖
- 配置修改后重启客户端，让客户端重新发现工具
- 接入后先在客户端列出工具，确认三个工具均已注册

## 7.5 验证流程

1. 客户端调用 query_student 查询"李明"，核对课程、分数和是否通过
2. 调用 add_student 新增赵峰，75 分
3. 调用 query_student 查询赵峰，确认可查到
4. 调用 score_statistics，确认统计包含新增学生，平均分保留两位小数
5. 关闭并重启 MCP 服务，再次查询赵峰，确认数据仍存在

- 重启验证是持久化检查的核心步骤
- 统计结果必须实时计算，写入固定数值会随数据变化失效

## 7.6 从零制作 Agent

### 核心循环

Agent 本质是一个循环：思考 → 调用工具 → 读取结果 → 再思考，直到输出最终答案。

```python
import json

import requests

OLLAMA_URL = "http://127.0.0.1:11434/v1/chat/completions"
MAX_STEPS = 10

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_student",
            "description": "按姓名查询学生成绩",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    },
]


def execute_tool(name: str, args: dict) -> str:
    if name == "query_student":
        return query_student(args["name"])
    return f"未知工具 {name}"


def run_agent(system_prompt: str, user_message: str) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    messages.append({"role": "user", "content": user_message})

    for _ in range(MAX_STEPS):
        resp = requests.post(
            OLLAMA_URL,
            json={"model": "qwen2.5:7b", "messages": messages, "tools": TOOLS},
            timeout=120,
        ).json()
        msg = resp["choices"][0]["message"]
        messages.append(msg)

        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            return msg["content"]

        for call in tool_calls:
            fn = call["function"]
            result = execute_tool(fn["name"], json.loads(fn["arguments"]))
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": result,
                }
            )
    return "达到最大迭代次数，任务未完成"
```

- messages 列表同时承载历史、模型回复和工具结果，是 Agent 的短期记忆
- 模型返回 tool_calls 时执行工具，结果以 role=tool 追加
- 没有 tool_calls 时模型输出即最终答案
- MAX_STEPS 限制循环次数，防止死循环浪费 Token

### 系统提示词设计

```python
SYSTEM_PROMPT = """你是一个成绩查询助手，负责回答学生成绩相关问题。
规则：
1. 查询成绩必须调用 query_student 工具
2. 涉及统计必须调用 score_statistics 工具
3. 只根据工具返回的结果回答
4. 查询不到学生时如实说明
"""
```

- 提示词明确工具使用边界和回答约束
- 需要更新的知识通过 RAG 检索注入上下文

### 把流程封装成 Skill

前面把单个工具直接暴露给模型；当"查某学生成绩 + 汇总班级统计"这类**固定流程**要反复做时，与其让模型每轮自己组合多次调用，不如**用一个 Skill 把流程装成"一个入口"**（对应 ch04 §4.7 的"整机"）——模型只决定"要不要报告"，内部步骤交给 Skill。

底层仍是 §7.3 的两个工具（原子操作）：

```python
def query_student(name: str) -> str: ...       # 查单个学生（返回字符串）
def score_statistics() -> str: ...             # 全班统计（返回字符串）
```

Skill 把它们按固定流程编排成"一个入口"：

```python
def student_report(name: str) -> str:
    """生成某学生的成绩分析报告：个人成绩 + 班级统计。"""
    score = query_student(name)        # 步骤1：查该生
    stats = score_statistics()         # 步骤2：查统计
    return f"{name} 的成绩：{score}\n班级统计：{stats}"   # 步骤3：按口径组装
```

与"直接暴露两个底层工具"的区别：模型在 `TOOLS` 里**只看到 Skill 一个入口**，内部自动编排多次调用：

```python
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "student_report",
            "description": "生成某学生的成绩分析报告（个人成绩 + 班级统计）",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    },
]

def execute_tool(name: str, args: dict) -> str:
    if name == "student_report":
        return student_report(args["name"])   # 内部按剧本编排两个底层工具
    return f"未知工具 {name}"
```

- **入口与 Tool 一致**：模型看到的是 `student_report`，只需传 `name`，感知不到内部要调两个工具
- **流程在"设计时"写死**：固定剧本替代"模型每轮临场组合多次调用"——更快、更稳、更省 Token（对应 ch04 §4.7 三层成本账）
- **幻觉面变小**：顺序、参数映射、产出口径都定了，模型只需决定"要不要出报告"
- **循环不变**：思考 → 调用 → 读结果 → 再思考 与核心循环完全一致——Skill 只是"打包了调用"，并不改变循环本身
- 兜底技巧：可在 `TOOLS` 里**同时保留底层工具**（如 `add_student`）——Skill 是"速装入口"，底层工具是"可自由组合的小零件"

### 接入 RAG：给 Agent 补"知识"

前面的例子都是查**结构化表格数据**（学生成绩）。但 Agent 还要能回答"训练时没见过"的文档型知识，比如学校制度。这类知识模型没学过，需要在生成前从知识库**检索注入上下文**——这就是 RAG（对应 ch04 §4.10）。

**第一步 · 准备知识库并切块**

把几篇制度文档写入字典，再按固定大小切成块（这里以字符数近似 Token 数）：

```python
KB_DOCS = {
    "请假制度": "学生请假需提前一天向辅导员提交申请，病假须附医院证明，事假须说明原因；请假超过三天需由系主任审批。",
    "考试规则": "考试不得携带手机或任何电子设备，迟到十五分钟以上不得进入考场，作弊按违纪处理并记入档案。",
    "成绩复议": "成绩公布后一周内可向教务处申请复核，逾期不再受理；复核仅核对累分是否准确，不重新评阅。",
}

def chunk_docs(docs: dict[str, str], size: int = 60, overlap: int = 10) -> list[dict]:
    """把每篇文档切成若干带 overlap 的文本块，返回 [{doc, text}]。"""
    chunks = []
    for doc, content in docs.items():
        for start in range(0, len(content), size - overlap):
            chunk = content[start:start + size]
            if len(chunk) >= 10:                 # 丢弃过短碎片
                chunks.append({"doc": doc, "text": chunk})
    return chunks
```

**第二步 · 向量化入库**

用 Ollama 的 embedding 接口把每个块编码为向量：

```python
EMBED_URL = "http://127.0.0.1:11434/api/embed"

def embed(text: str) -> list[float]:
    resp = requests.post(EMBED_URL, json={"model": "qwen2.5:7b", "input": text}).json()
    return resp["embeddings"][0]

def build_index(chunks: list[dict]) -> list[dict]:
    for c in chunks:
        c["vec"] = embed(c["text"])              # 逐块向量化，可离线提前算好
    return chunks

INDEX = build_index(chunk_docs(KB_DOCS))
```

**第三步 · 余弦相似度检索**

```python
import math

def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb + 1e-9)

def search_knowledge(query: str, top_k: int = 2) -> str:
    """检索制度知识库，返回最相关的条文片段。"""
    qvec = embed(query)
    scored = sorted(INDEX, key=lambda c: cosine(qvec, c["vec"]), reverse=True)
    return "\n".join(f"[{c['doc']}] {c['text']}" for c in scored[:top_k])
```

**第四步 · 完全离线的降级检索（无 Embedding 模型时）**

比赛环境若无法运行 Embedding，可用"查询与切块的关键词重合数"粗打分，得到一个最小可用的 RAG（缺点：吃不进同义词，语义能力弱）：

```python
def search_knowledge_local(query: str, top_k: int = 2) -> str:
    q_words = set(query.split())                         # 中文可改用字符 n-gram 或更细分词
    def hit(c: dict) -> int:
        return len(q_words & set(c["text"]))
    scored = sorted(INDEX, key=hit, reverse=True)
    return "\n".join(f"[{c['doc']}] {c['text']}" for c in scored[:top_k] if hit(c) > 0)
```

**第五步 · 作为工具接入 Agent 循环**

把检索当作普通工具暴露给模型，模型自行决定要不要查、查几次：

```python
def execute_tool(name: str, args: dict) -> str:
    if name == "query_student":
        return query_student(args["name"])
    if name == "search_knowledge":
        return search_knowledge(args["query"])   # 离线时换成 search_knowledge_local
    return f"未知工具 {name}"

# TOOLS 里对应新增即可：
# {
#   "type": "function",
#   "function": {
#     "name": "search_knowledge",
#     "description": "检索学校制度知识库，返回相关制度条文",
#     "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
#   },
# }
```

**关键点**

- 检索结果与系统提示词分开存放，避免外部文本被当成新指令（指令注入，见 ch04 §4.15）
- 块文本带文档名前缀 `[请假制度]` 等，便于模型引用与溯源，回答时也能注明出处
- 检索质量取决于：切块大小、是否用 Rerank / 混合检索、知识库是否最新（详见 ch04 §4.10）
- 这里是"普通 RAG"（每问检索一次）；若把"要不要再查一次"交给模型自行判断，就进阶为"Agent 型 RAG"（见 ch04 §4.10）

### 安全与预算控制

- 设置最大迭代次数和每次调用的 Token 上限
- 高风险工具调用前请求确认，例如删除、覆盖类操作
- 记录每一步的工具调用和结果，便于回放定位
- 给模型提供只读工具时禁止写入类能力

### 调试与评测

- 日志输出每步的思考、工具调用和返回结果
- 评测集覆盖正常查询、不存在学生、边界分数等用例
- 统计指标：任务成功率、工具调用次数、平均耗时
- 失败用例回放日志，定位是提示词、检索还是工具问题

## 7.7 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| 客户端找不到工具 | 配置路径错误或进程启动失败 | 手动运行 command 和 args 验证 |
| 中文输出乱码 | 终端或文件编码问题 | JSON 读写用 encoding="utf-8" |
| 服务重启后数据丢失 | 未持久化到文件 | 数据写入本地 JSON 文件 |
| Agent 反复调用同一工具 | 无迭代上限 | 设置 MAX_STEPS 并检查提示词 |
| 工具参数报错 | 参数名与 schema 不一致 | 检查函数签名与调用参数 |
| stdout 被日志污染 | 日志写入 stdout | 日志统一走 stderr 或文件 |
