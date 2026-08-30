"""知识图谱 MCP Server（mcp-graph）

把 docs/public/graph-data.json 暴露成可查询的 MCP 工具，供 AI Host（opencode 等）查询/扩写知识图谱。

与 mcp-exam / mcp-manual 相同的约定：复杂入参/返回用 JSON 字符串，最稳妥、可跨 Host 复用。
用法（stdio）：
    python server.py
"""

import json
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from graph_engine import DEFAULT_GRAPH_PATH, GraphStore

# 串联：复用 mcp/exam 的题库校验逻辑（graph 关联 → exam 校题）
_EXAM_DIR = Path(__file__).resolve().parent.parent / "exam"
if str(_EXAM_DIR) not in sys.path:
    sys.path.insert(0, str(_EXAM_DIR))
from exam_engine import validate_questions as engine_validate  # noqa: E402

_store = GraphStore(str(DEFAULT_GRAPH_PATH))
mcp = FastMCP("graph-server")


@mcp.tool()
def read_graph() -> str:
    """读取完整知识图谱。返回 JSON 字符串：{nodes:[{id,name,module,chapter,anchor,desc}], edges:[{source,target,relation}]}。"""
    return json.dumps(_store.read_graph(), ensure_ascii=False)


@mcp.tool()
def search_nodes(query: str) -> str:
    """按名称/描述/id 模糊搜索知识点节点。query 为关键词。返回匹配节点数组的 JSON 字符串。"""
    return json.dumps(_store.search_nodes(query), ensure_ascii=False)


@mcp.tool()
def open_node(node_id: str) -> str:
    """获取单个知识点节点的详情（含其关联列表 relations）。返回 JSON 字符串。"""
    return json.dumps(_store.open_node(node_id), ensure_ascii=False)


@mcp.tool()
def get_relations(node_id: str) -> str:
    """获取某节点的一跳关系。返回 JSON 字符串：[{node,name,module,relation,chapter,anchor}]。"""
    return json.dumps(_store.get_relations(node_id), ensure_ascii=False)


@mcp.tool()
def graph_stats() -> str:
    """图谱统计：节点数、边数、按模块分布。返回 JSON 字符串。"""
    return json.dumps(_store.graph_stats(), ensure_ascii=False)


@mcp.tool()
def add_node(node_json: str) -> str:
    """新增知识点节点并落盘。node_json：{id,name,module,chapter,anchor,desc} 的 JSON 字符串（id/name/module 必填，module 属于 ai/os/software/agent/hardware）。"""
    return json.dumps(_store.add_node(json.loads(node_json)), ensure_ascii=False)


@mcp.tool()
def add_edge(edge_json: str) -> str:
    """新增关系边并落盘。edge_json：{source,target,relation} 的 JSON 字符串（两端节点须已存在）。"""
    return json.dumps(_store.add_edge(json.loads(edge_json)), ensure_ascii=False)


@mcp.tool()
def update_anchor(node_id: str, anchor: str) -> str:
    """更新某节点锚点（配合手册标题改动同步图谱）。返回 {updated, anchor}。"""
    return json.dumps(_store.update_anchor(node_id, anchor), ensure_ascii=False)


@mcp.tool()
def related_questions(node_id: str, count: int = 10) -> str:
    """串联：由某知识点查其关联，再从模拟题库按关联 module 抽取练习题目，并用 exam 校验题目合格。

    node_id 为知识图谱节点 id；count 为抽取题数。
    返回 {node, relations, modules_used, count, valid, errors, questions}。
    """
    r = _store.related_questions(node_id, count=count)
    if "error" in r:
        return json.dumps(r, ensure_ascii=False)
    v = engine_validate(r["questions"])
    r["valid"] = v["valid"]
    r["errors"] = v["errors"]
    return json.dumps(r, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()  # stdio
