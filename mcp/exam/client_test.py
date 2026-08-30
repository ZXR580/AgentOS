"""标准 MCP Client 流程演示：initialize → initialized → tools/list → tools/call。

运行：
    python client_test.py

它作为"客户端（Client）"，用 stdio 拉起本地 server.py，走一遍协议握手、
列出工具，并对一组示例题依次调用 validate / assemble / grade / wrong_add / wrong_list。
"""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PATH = Path(__file__).parent / "server.py"

# 一组示例题（source 必须为 mock；multi 6 项 3~4 正确；judge 固定正确/错误）
SAMPLE = [
    {
        "id": "S001", "type": "single", "module": "ai",
        "stem": "机器学习的训练数据必须包含什么？",
        "options": [
            {"key": "A", "text": "目标标签"},
            {"key": "B", "text": "随机噪声"},
            {"key": "C", "text": "无标签样本"},
            {"key": "D", "text": "不需要数据"},
        ],
        "answerKeys": ["A"],
        "explanation": "监督学习靠标签提供正确答案。",
        "chapter": "/ch01_ai_foundation", "source": "mock",
    },
    {
        "id": "S002", "type": "multi", "module": "ai",
        "stem": "下列属于监督学习算法的有：",
        "options": [
            {"key": "A", "text": "线性回归"},
            {"key": "B", "text": "KNN"},
            {"key": "C", "text": "K-means"},
            {"key": "D", "text": "SVM"},
            {"key": "E", "text": "PCA"},
            {"key": "F", "text": "生成对抗网络"},
        ],
        "answerKeys": ["A", "B", "D"],
        "explanation": "线性回归、KNN、SVM 都是有监督；K-means、PCA、GAN 不是。",
        "chapter": "/ch01_ai_foundation", "source": "mock",
    },
    {
        "id": "S003", "type": "judge", "module": "os",
        "stem": "Linux 是单体内核。",
        "options": [{"key": "A", "text": "正确"}, {"key": "B", "text": "错误"}],
        "answerKeys": ["A"],
        "explanation": "Linux 的进程、内存、文件系统、驱动都在同一内核空间。",
        "chapter": "/ch02_os_linux", "source": "mock",
    },
]


def show(res):
    """从 CallToolResult 里取第一个 text 内容并解析 JSON 打印（若可解析）。"""
    text = res.content[0].text
    try:
        return json.loads(text)
    except Exception:
        return text


async def main():
    server_params = StdioServerParameters(
        command=sys.executable,            # 用当前 python
        args=[str(SERVER_PATH)],           # 标准操作：Client 拉起 Server 进程（stdio）
        env=None,
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. 握手：Client 发 initialize，Server 回应能力与版本；再发 initialized
            init = await session.initialize()
            print("== [1] initialize 握手 ==")
            si = init.serverInfo
            print("server:", getattr(si, "name", None), "v" + (getattr(si, "version", None) or "?"))
            print("capabilities:", str(init.capabilities)[:60], "...")

            # 2. tools/list：Server 返回工具清单
            tools = await session.list_tools()
            print("\n== [2] tools/list ==")
            for t in tools.tools:
                print(f"  - {t.name}")

            # 3. tools/call：validate
            print("\n== [3a] validate_questions ==")
            res = await session.call_tool(
                "validate_questions", {"questions_json": json.dumps(SAMPLE, ensure_ascii=False)}
            )
            print("valid:", show(res))

            # 4. tools/call：assemble_paper
            print("\n== [3b] assemble_paper ==")
            res = await session.call_tool(
                "assemble_paper",
                {"questions_json": json.dumps(SAMPLE, ensure_ascii=False),
                 "single": 1, "multi": 1, "judge": 1},
            )
            paper = show(res)["paper"]
            print(f"抽中 {len(paper)} 题:", [p["id"] for p in paper])

            # 5. tools/call：grade_paper（模拟全答对）
            answers = [sorted(p["answerKeys"]) for p in paper]
            res = await session.call_tool(
                "grade_paper",
                {"paper_json": json.dumps(paper, ensure_ascii=False),
                 "answers_json": json.dumps(answers, ensure_ascii=False)},
            )
            print("score:", show(res)["score"], "/", len(paper))

            # 6. tools/call：wrong_add + wrong_list
            print("\n== [3c] wrong_add / wrong_list ==")
            wrongs = [{"id": p["id"], "source": p["source"],
                       "myAnswer": [p["answerKeys"][0]]} for p in paper]
            print("add:", show(await session.call_tool("wrong_add", {"wrongs_json": json.dumps(wrongs, ensure_ascii=False)})))
            print("list:", show(await session.call_tool("wrong_list", {})))


if __name__ == "__main__":
    asyncio.run(main())
