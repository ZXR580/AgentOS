"""mcp-graph 标准 Client 流程演示：initialize → tools/list → tools/call。

运行：
    py -3 client_test.py

它作为 Client 用 stdio 拉起本地 server.py，走握手、列工具，并调用 read_graph /
graph_stats / search_nodes / open_node / get_relations。
"""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PATH = Path(__file__).parent / "server.py"


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
            print("== [1] initialize 握手 ==  (graph-server)")

            tools = await session.list_tools()
            print("\n== [2] tools/list ==")
            for t in tools.tools:
                print(f"  - {t.name}")

            print("\n== [3a] graph_stats ==")
            print("stats:", show(await session.call_tool("graph_stats", {})))

            # 取一个真实节点 id 用于后续演示
            g = show(await session.call_tool("read_graph", {}))
            first = g["nodes"][0] if g["nodes"] else None
            print("\n== [3b] read_graph ==")
            print("nodes:", len(g["nodes"]), "| edges:", len(g["edges"]))
            print("示例节点:", first["id"], "|", first["name"], "|", first["module"])

            if first:
                nid = first["id"]
                print("\n== [3c] search_nodes('RAG') ==")
                hits = show(await session.call_tool("search_nodes", {"query": "RAG"}))
                print("匹配数:", len(hits), "| 首条:", hits[0]["name"] if hits else "-")

                print("\n== [3d] open_node ==")
                node = show(await session.call_tool("open_node", {"node_id": nid}))
                print("name:", node.get("name"), "| 关联数:", len(node.get("relations", [])))

                print("\n== [3e] get_relations ==")
                rels = show(await session.call_tool("get_relations", {"node_id": nid}))
                print("关系数:", len(rels), "| st:", [(r["name"], r["relation"]) for r in rels[:3]])

                # 3f. 串联：graph 关联 → exam 出题
                print("\n== [3f] related_questions（graph 关联 → exam 出题）==")
                rq = show(await session.call_tool("related_questions", {"node_id": nid, "count": 5}))
                print("node:", rq["node"]["name"], "| modules_used:", rq["modules_used"],
                      "| 抽题数:", rq["count"], "| valid:", rq.get("valid"))
                print("  首题:", (rq["questions"][0]["stem"] if rq["questions"] else "-")[:40])

                # 4. 写入工具：用非法输入演示校验（不污染真实数据）
                print("\n== [4] 写入工具（非法输入，仅演示校验，不改真实数据）==")
                print("add_node(缺字段):", show(await session.call_tool("add_node", {"node_json": json.dumps({"id": "X", "name": "x"}, ensure_ascii=False)})))
                print("add_edge(端点不存在):", show(await session.call_tool("add_edge", {"edge_json": json.dumps({"source": nid, "target": "notexist", "relation": "x"}, ensure_ascii=False)})))
                print("update_anchor(节点不存在):", show(await session.call_tool("update_anchor", {"node_id": "notexist", "anchor": "a"})))


if __name__ == "__main__":
    asyncio.run(main())
