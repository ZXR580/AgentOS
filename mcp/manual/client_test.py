"""mcp-manual 标准 Client 流程演示：initialize → tools/list → tools/call。

运行：
    py -3 client_test.py

它作为 Client 用 stdio 拉起本地 server.py，走握手、列工具，并对示例材料
依次调用 manual_spec / slugify / validate_anchors / chapter_outline / check_graph_sync。
"""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PATH = Path(__file__).parent / "server.py"

SAMPLE_MATERIAL = """# 模型生成文本与智能体执行任务

## 本节回答：为什么"会聊天"不等于"会干活"？

LLM 是文本生成器，无法直接操作文件。

## Agent 中的分工

LLM 负责决策，执行层负责调用工具。
"""


def show(res):
    text = res.content[0].text
    try:
        return json.loads(text)
    except Exception:
        return text


async def main():
    p = StdioServerParameters(command=sys.executable, args=[str(SERVER_PATH)], env=None)
    async with stdio_client(p) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("== [1] initialize 握手 ==  (manual-server)")

            tools = await session.list_tools()
            print("\n== [2] tools/list ==")
            for t in tools.tools:
                print(f"  - {t.name}")

            print("\n== [3a] manual_spec ==")
            spec = show(await session.call_tool("manual_spec", {}))
            print("章节数:", len(spec["chapters"]), "| 首章:", spec["chapters"][0]["name"])

            print("\n== [3b] slugify ==")
            for t in ["4.10 RAG 与向量检索", "Agent 型 RAG", "支持向量机与朴素贝叶斯"]:
                print(f"   {t}  ->  {show(await session.call_tool('slugify', {'title': t}))}")

            print("\n== [3c] validate_anchors ==")
            r = show(await session.call_tool("validate_anchors", {
                "headings_json": json.dumps([
                    {"level": "##", "title": "4.10 RAG 与向量检索"},
                    {"level": "###", "title": "Agent 型 RAG"},
                ], ensure_ascii=False)
            }))
            print("valid:", r["valid"], "| anchors:", [i["slug"] for i in r["items"]])

            print("\n== [3d] chapter_outline ==")
            r = show(await session.call_tool("chapter_outline", {
                "material": SAMPLE_MATERIAL, "chapter_no": 4, "chapter_title": "智能体技术基础",
            }))
            print("主线:", r["main_thread"][:40], "...")
            print("小节数:", len(r["sections"]), "| 首节:", r["sections"][0]["title"], "->", r["sections"][0]["slug"])

            print("\n== [3e] check_graph_sync ==")
            anchors = r["sections"]
            graph = [{"id": "rag", "name": "RAG", "anchor": "slug-placeholder"},
                     {"id": "agent", "name": "Agent", "anchor": "agent-型-rag"}]
            res = show(await session.call_tool("check_graph_sync", {
                "chapter_anchors_json": json.dumps(
                    [{"title": s["title"], "slug": s["slug"]} for s in anchors], ensure_ascii=False),
                "graph_nodes_json": json.dumps(graph, ensure_ascii=False),
            }))
            print("ok:", res["ok"], "| 缺失于图谱:", res["missing_in_graph"])


if __name__ == "__main__":
    asyncio.run(main())
