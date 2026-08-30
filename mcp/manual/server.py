"""知识手册构建 MCP Server（mcp-manual）

把"手册构建的确定性逻辑"暴露成可调用工具：手册规范、标题锚点生成/校验、
章节标题↔图谱节点同步校验、把零散材料编排成有逻辑的章节大纲骨架。

"写正文"由 Host 侧 LLM 负责（配合 .opencode/skills/exam-builder 或 manual-refactor 流程）；
本 Server 提供**骨架 + 规约 + 校验**，保证构建结果符合本库逻辑体系与锚点/图谱一致性。

与 mcp-exam 相同的约定：复杂入参/返回用 JSON 字符串，最稳妥、可跨 Host 复用。
用法（stdio）：
    python server.py
"""

import json

from mcp.server.fastmcp import FastMCP

from manual_engine import (
    MANUAL_SPEC,
    chapter_outline as engine_outline,
    check_graph_sync as engine_check_sync,
    slugify as engine_slugify,
    validate_anchors as engine_validate_anchors,
)

mcp = FastMCP("manual-server")


def _loads(obj):
    return json.loads(obj) if isinstance(obj, str) else obj


@mcp.tool()
def manual_spec() -> str:
    """返回本库知识手册的构建规范（章节数、考核占比、结构约定、主线句式、讲解链、锚点规则、图谱同步要求）。"""
    return json.dumps(MANUAL_SPEC, ensure_ascii=False)


@mcp.tool()
def slugify(title: str) -> str:
    """把 markdown 标题转成 VitePress 锚点 slug（复刻本库规则）。返回字符串。"""
    return engine_slugify(title)


@mcp.tool()
def validate_anchors(headings_json: str) -> str:
    """校验一组标题的锚点并返回 slug。headings_json：[{'level','title'}, ...]。

    返回 {valid, items:[{level,title,slug}], duplicates, errors}。
    """
    return json.dumps(engine_validate_anchors(_loads(headings_json)), ensure_ascii=False)


@mcp.tool()
def check_graph_sync(chapter_anchors_json: str, graph_nodes_json: str) -> str:
    """校验章节标题锚点与知识图谱节点 anchor 是否一一对应（防死链）。

    chapter_anchors_json：[{'title','slug'}]；graph_nodes_json：图谱节点数组。
    返回 {ok, missing_in_graph, orphan_anchors}。
    """
    r = engine_check_sync(_loads(chapter_anchors_json), _loads(graph_nodes_json))
    return json.dumps(r, ensure_ascii=False)


@mcp.tool()
def chapter_outline(material: str, chapter_no: int = 1, chapter_title: str = "") -> str:
    """把一份零散材料编排成该章的"有逻辑有体系"大纲骨架。

    material：材料文本（可含 markdown 标题，会被采纳为小节）；chapter_no/chapter_title：章节信息。
    返回 {chapter_no, chapter_title, main_thread, sections:[{level,title,slug,guide,must}], style_checks}。
    """
    r = engine_outline(material, chapter_no, chapter_title or f"第{chapter_no}章")
    return json.dumps(r, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()  # stdio
