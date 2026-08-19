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

### 接入 RAG

RAG 作为普通工具接入即可，模型按需调用：

```python
@mcp.tool()
def search_knowledge(query: str) -> str:
    """检索知识库，返回相关文档片段。"""
    vector = embed(query)
    results = vector_store.search(vector, top_k=3)
    return "\n".join(r["text"] for r in results)
```

- 检索函数返回文本片段，模型自行判断引用
- 检索结果与系统提示词分开，避免指令注入

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
