"""考试系统 MCP Server

把"校验 / 组卷 / 判分 / 错题本"暴露成可调用的 MCP 工具。
约定：自定义工具是**确定性逻辑**——"生成题目内容"由调用方（Host 侧 LLM）负责，
生成候选题目后再调用本 Server 的 validate / assemble 工具完成校验与装配。

出于对 mcp SDK 嵌套参数解析的兼容性考虑，**复杂入参/返回用 JSON 字符串**：
入参形如 {"questions_json": "[{...}]"}，返回是 JSON 文本。这最稳妥、可跨 Host 复用。

用法（stdio）：
    python server.py
"""

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from exam_engine import (
    assemble_paper as engine_assemble,
    grade_paper as engine_grade,
    generate_questions as engine_generate,
    validate_questions as engine_validate,
    WrongStore,
)

# 错题本持久化到本目录下 JSON 文件（跨进程复用）
STORE_FILE = Path(__file__).parent / "wrong_store.json"
_store = WrongStore(str(STORE_FILE))

mcp = FastMCP("exam-server")


def _loads(obj):
    if isinstance(obj, str):
        return json.loads(obj)
    return obj


@mcp.tool()
def validate_questions(questions_json: str) -> str:
    """校验题目数组是否符合考试系统 schema。

    入参 questions_json：题目对象数组的 JSON 字符串（字段见 README）。
    返回：JSON 字符串 {valid, total, errors}；errors 为逐题错误列表，空表示全部合格。
    """
    return json.dumps(engine_validate(_loads(questions_json)), ensure_ascii=False)


@mcp.tool()
def assemble_paper(questions_json: str, single: int = 30, multi: int = 10,
                   judge: int = 20, shuffle: bool = True) -> str:
    """按题型结构 + 模块占比组卷。

    questions_json：候选题目数组 JSON 字符串；single/multi/judge：各题型数量（默认 30/10/20）；
    shuffle：是否随机打乱选项顺序（默认 True）。
    返回：JSON 字符串 {paper, structure}；paper 为抽出的题目（打乱选项 + 换算后的 answerKeys）。
    """
    r = engine_assemble(
        _loads(questions_json), single=single, multi=multi, judge=judge, shuffle=shuffle
    )
    return json.dumps(r, ensure_ascii=False)


@mcp.tool()
def grade_paper(paper_json: str, answers_json: str) -> str:
    """判分。paper_json 为 assemble_paper 产物 JSON；answers_json 为每题所选 key 数组的 JSON 字符串。

    评分口径：单选/判断取一项正确；多选需**全对**才给分。
    返回：JSON 字符串 {score, total, wrong, results}。
    """
    r = engine_grade(_loads(paper_json), _loads(answers_json))
    return json.dumps(r, ensure_ascii=False)


@mcp.tool()
def wrong_add(wrongs_json: str) -> str:
    """把答错的题写入错题本。wrongs_json：[{id, source, myAnswer}] 的 JSON 字符串，按 (id, source) 去重。"""
    return json.dumps(_store.add(_loads(wrongs_json)), ensure_ascii=False)


@mcp.tool()
def wrong_list() -> str:
    """列出错题本全部记录（元信息：id/source/myAnswer/at）。返回 JSON 字符串数组。"""
    return json.dumps(_store.list(), ensure_ascii=False)


@mcp.tool()
def wrong_remove(qid: str, source: str = "mock") -> str:
    """从错题本移除一条记录。返回 {removed, total} 的 JSON 字符串。"""
    return json.dumps(_store.remove(qid, source), ensure_ascii=False)


@mcp.tool()
def wrong_clear() -> str:
    """清空错题本。返回 {cleared: true, total: 0} 的 JSON 字符串。"""
    return json.dumps(_store.clear(), ensure_ascii=False)


@mcp.tool()
def generate_questions(material: str, module: str = "ai", chapter: str = "/ch01_ai_foundation",
                       single: int = 10, multi: int = 3, judge: int = 7) -> str:
    """生成题目：内部调用 LLM 按出题规范生成候选，再自动校验。

    material：学习内容/知识点文本；module：ai/os/software/agent/hardware；
    chapter：考点链接；single/multi/judge：要生成的各题型数量。
    返回 JSON 字符串 {valid, errors, questions}；questions 为已校验/规范化的候选
    （id 自动从题库现有最大编号续号、source=mock）。LLM 端点由环境变量 LLM_BASE/LLM_MODEL/LLM_KEY 配置。
    """
    r = engine_generate(material, module=module, chapter=chapter,
                        single=single, multi=multi, judge=judge)
    return json.dumps(r, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()  # 默认 stdio 模式
