"""知识手册构建内核（纯标准库，无 MCP 依赖）。

把本仓库"知识手册"的构建方式抽成可复用的确定性逻辑：
- 手册规范（章节数 / 考核占比 / 结构约定 / 主线句式）
- 标题锚点（VitePress slug）生成与校验
- 章节标题 ↔ 知识图谱节点 的同步校验
- 把一份零散材料编排成"有逻辑有体系"的章节大纲骨架

内容生成（正文）由 Host 侧 LLM 负责；本内核提供**骨架 + 规约 + 校验**，保证构建出的手册
符合本库的逻辑体系（是什么 → 机制 → 为什么 → 对比 → 衔接）与锚点/图谱一致性。
"""

import json
import re

LANGS = ["zh", "en", "os", "software", "agent", "hardware"]

# 本库手册章节规范（供构建参考）
MANUAL_SPEC = {
    "title_template": "第 {n} 章 {name}",
    "chapters": [
        {"no": 1, "name": "人工智能基础理论", "module": "ai", "ratio": 0.3},
        {"no": 2, "name": "国产操作系统技术基础", "module": "os", "ratio": 0.2},
        {"no": 3, "name": "国产软件技术基础", "module": "software", "ratio": 0.2},
        {"no": 4, "name": "智能体技术基础", "module": "agent", "ratio": 0.2},
        {"no": 5, "name": "国产硬件技术基础", "module": "hardware", "ratio": 0.1},
        {"no": 6, "name": "附录", "module": None, "ratio": 0},
        {"no": 7, "name": "MCP 与 Agent 落地实践", "module": "agent", "ratio": 0},
        {"no": 8, "name": "智能平台", "module": "agent", "ratio": 0},
    ],
    "structure": {
        "chapter": "# 第 X 章 <名称>",
        "section": "## X.Y <小节>",
        "subsection": "### <子节>",
        "depth": {"##": "小节", "###": "子节", "####": "子子节"},
    },
    "thread_style": {
        "chapter": "> 本章主线：……（一句串联全章）",
        "section": "> 本节回答：……（本节要解决的递进问题）",
        "transitions": "每节末尾用'下一节讲…'做承上启下",
    },
    "explanatory_chain": ["是什么", "机制/怎么做", "为什么（机制根因）", "对比/边界", "衔接"],
    "exam_point_style": "每节标注高频考点/易混点（绝对化陷阱句式：只要…就…/一定/唯一/完全/无需…）",
    "synchronize": {
        "graph_data": "docs/public/graph-data.json",
        "node_fields": ["id", "name", "module", "chapter", "anchor", "desc"],
        "node_schema": "节点字段: id/name/module/chapter/anchor/desc，anchor 必须等于对应标题的 VitePress slug",
        "anchor_rule": "节点 anchor 必须等于对应标题的 VitePress slug",
    },
    "anchor_rule": "标题以数字开头时 slug 加 '_' 前缀；英文转小写；空格/标点转 '-'；中文保留",
    "terms_file": "docs/public/terms.json",
    "formula": {
        "syntax": "行内公式用 $...$，块公式用 $$...$$（LaTeX）",
        "spacing": "$ 前后需留空格或与标点相邻，不要紧贴汉字/数字（否则 markdown-it-katex 可能不解析）",
        "supported": "KaTeX 支持 \\frac \\sum \\alpha \\|w\\| h_t \\mathcal{L} \\partial \\nabla \\begin{aligned} 等常用语法",
        "avoid": "避免 \\begin{equation} 编号、\\color 等需额外扩展的宏",
        "note": "公式由前端 VitePress + KaTeX 渲染；MCP 只负责产出正确的 LaTeX 字符串（$ / $$ 包裹）",
    },
}


# ---------------------------------------------------------------------------
# 锚点（VitePress slug）
# ---------------------------------------------------------------------------
def slugify(title: str) -> str:
    """把 markdown 标题转成 VitePress 锚点 slug（复刻本库现行规则）。

    规则：丢弃 '#' 前缀；英文转小写；空格与标点转 '-'；中文保留；
    若结果以数字开头则加 '_' 前缀（HTML anchor 不能以数字开头）。
    """
    t = re.sub(r"^\s*#+\s*", "", title).strip()
    # 标点与空格 -> '-'；保留中英文与数字
    t = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", t).strip("-").lower()
    if t and t[0].isdigit():
        t = "_" + t
    return t


def validate_anchors(headings: list) -> dict:
    """对一组标题生成 slug 并校验唯一性。headings: [{'level','title'}, ...]。

    返回 {valid, items:[{level,title,slug}], duplicates, errors}。
    """
    items, seen, errors, dups = [], {}, [], []
    for h in headings:
        level = h.get("level", "##")
        title = h.get("title", "")
        slug = slugify(title)
        if slug in seen:
            dups.append(slug)
            errors.append(f"锚点重复: {title} -> {slug}")
        seen[slug] = title
        items.append({"level": level, "title": title, "slug": slug})
    return {"valid": len(errors) == 0, "items": items, "duplicates": dups, "errors": errors}


# ---------------------------------------------------------------------------
# 图谱同步校验
# ---------------------------------------------------------------------------
def check_graph_sync(chapter_anchors: list, graph_nodes: list) -> dict:
    """校验章节标题锚点与知识图谱节点 anchor 是否一一对应（防死链）。

    chapter_anchors: [{'title','slug'}]（可由 validate_anchors 产出）；
    graph_nodes: 图谱节点数组 [{id,name,chapter,anchor,...}]。
    返回 {missing_in_graph, orphan_anchors, conflicts, ok}。
    """
    node_anchors = {n.get("anchor") for n in graph_nodes}
    title_anchors = {a.get("slug") for a in chapter_anchors}
    missing = sorted(title_anchors - node_anchors)       # 标题有、图谱没记录 -> 死链风险
    orphan = sorted(node_anchors - title_anchors)        # 图谱有、标题无 -> 冗余/漂移
    return {
        "ok": len(missing) == 0,
        "missing_in_graph": missing,
        "orphan_anchors": orphan,
    }


# ---------------------------------------------------------------------------
# 章节大纲：把零散材料编排成"有逻辑有体系"的骨架
# ---------------------------------------------------------------------------
def chapter_outline(material: str, chapter_no: int, chapter_title: str) -> dict:
    """把一份材料编排成该章的**大纲骨架**（主线 + 小节树 + 每节检查要点）。

    这是"规约/骨架"而非正文：材料里的标题会被采纳为小节；若材料无标题，
    则按材料段落生成小节建议，并标注每节应覆盖的"讲解链"与考点提示。
    """
    # 1. 提取材料中的 markdown 标题作为候选小节
    lines = [ln for ln in material.splitlines()]
    raw_headings = [
        {"level": m.group(1), "title": m.group(2).strip()}
        for m in (re.match(r"^(#{1,4})\s+(.*)$", ln) for ln in lines)
        if m
    ]
    headings = raw_headings or [
        {"level": "##", "title": f"{chapter_no}.{i+1} {seg.splitlines()[0][:24]}"}
        for i, seg in enumerate(re.split(r"\n\s*\n", material.strip())) if seg.strip()
    ][:20]

    # 2. 主线：一段贯穿全章的"回答/串联"提示（占位，交由 LLM 充实）
    main_thread = (
        f"本章主线：从『{chapter_title}』的根因（是什么/为什么）出发，"
        f"经机制与对比，落到应用与边界，一节递进一节、末节承上启下。"
    )

    # 3. 每节给出"讲解链"检查要点
    chain = MANUAL_SPEC["explanatory_chain"]
    sections = []
    for h in headings:
        slug = slugify(h["title"])
        sections.append({
            "level": h["level"], "title": h["title"], "slug": slug,
            "guide": "、".join(chain),
            "must": "该节应写：解决什么问题 → 机制/怎么做 → 为什么(根因) → 对比/边界 → 衔接",
        })

    return {
        "chapter_no": chapter_no,
        "chapter_title": f"第 {chapter_no} 章 {chapter_title}",
        "main_thread": main_thread,
        "sections": sections,
        "style_checks": [
            "每节以『> 本节回答：……』开头点明要解决的问题",
            "节与节之间用『下一节讲…』承上启下",
            "标注高频考点与易混点（含绝对化陷阱句式）",
            "章节标题改动需同步 graph-data.json 对应节点 anchor 与 terms.json href",
            "数学公式用 LaTeX 并以 $ 或 $$ 包裹（$ 前后留空格，勿紧贴汉字/数字）；详见 manual_spec 的 formula",
        ],
    }
