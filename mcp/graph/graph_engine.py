"""知识图谱内核（纯标准库，无 MCP 依赖）。

把 docs/public/graph-data.json 暴露成可查询的"知识图谱"：
- read_graph：读完整图谱（节点 + 边）
- search_nodes：按名称/描述/id 模糊搜索节点
- open_node：取单个节点详情（含其关联）
- get_relations：取某节点的一跳关系
- graph_stats：图谱统计（节点/边数、按模块分布）

与 mcp-exam / mcp-manual 一致：Server 提供确定性查询逻辑，供 Host 侧 LLM 复用。
"""

import json
from collections import defaultdict
from pathlib import Path


class GraphStore:
    def __init__(self, path="graph-data.json"):
        self.path = Path(path)
        self._data = self._load()
        self._nodes = self._data.get("nodes", [])
        self._edges = self._data.get("edges", [])
        self._by_id = {n.get("id"): n for n in self._nodes if n.get("id")}
        self._neighbors = self._build_neighbors()

    def _load(self):
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"nodes": [], "edges": []}

    def _build_neighbors(self):
        m = defaultdict(list)
        for e in self._edges:
            s, t = e.get("source"), e.get("target")
            if s in self._by_id and t in self._by_id:
                m[s].append((t, e.get("relation", "")))
                m[t].append((s, e.get("relation", "")))
        return m

    # ---- 查询 ----
    def read_graph(self):
        return {"nodes": self._nodes, "edges": self._edges}

    def search_nodes(self, query):
        q = (query or "").strip().lower()
        if not q:
            return self._nodes
        out = []
        for n in self._nodes:
            hay = " ".join([n.get("id", ""), n.get("name", ""), n.get("desc", "")]).lower()
            if q in hay:
                out.append(n)
        return out

    def open_node(self, node_id):
        n = self._by_id.get(node_id)
        if n is None:
            return {"error": f"未找到节点 {node_id}"}
        return {**n, "relations": self.get_relations(node_id)}

    def get_relations(self, node_id):
        rels = []
        for other_id, relation in self._neighbors.get(node_id, []):
            other = self._by_id.get(other_id, {})
            rels.append({
                "node": other_id,
                "name": other.get("name", other_id),
                "module": other.get("module", ""),
                "relation": relation,
                "chapter": other.get("chapter", ""),
                "anchor": other.get("anchor", ""),
            })
        return rels

    def graph_stats(self):
        by_module = defaultdict(int)
        for n in self._nodes:
            by_module[n.get("module") or "unknown"] += 1
        degraded = self._edges
        return {
            "nodes": len(self._nodes),
            "edges": len(degraded),
            "modules": dict(sorted(by_module.items())),
        }

    # ---- 写入（维护图谱，自动落盘） ----
    def _save(self):
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def add_node(self, node):
        if not isinstance(node, dict):
            return {"error": "节点必须是对象"}
        missing = [k for k in NODE_REQUIRED if not node.get(k)]
        if missing:
            return {"error": f"缺字段 {missing}；节点至少需 id/name/module"}
        if node.get("module") not in VALID_MODULES:
            return {"error": f"module 非法：{node.get('module')}（应为 {VALID_MODULES}）"}
        nid = node["id"]
        if nid in self._by_id:
            return {"error": f"节点已存在：{nid}（如需修改请用 update_anchor 或直接编辑数据）"}
        clean = {k: node.get(k, "") for k in ["id", "name", "module", "chapter", "anchor", "desc"]}
        self._nodes.append(clean)
        self._by_id[clean["id"]] = clean
        self._save()
        return {"added": clean["id"], "nodes": len(self._nodes)}

    def add_edge(self, edge):
        if not isinstance(edge, dict):
            return {"error": "边必须是对象"}
        missing = [k for k in EDGE_REQUIRED if not edge.get(k)]
        if missing:
            return {"error": f"缺字段 {missing}；边需 source/target/relation"}
        s, t = edge["source"], edge["target"]
        if s not in self._by_id or t not in self._by_id:
            return {"error": f"source/target 必须存在：{s}/{t}"}
        for e in self._edges:
            if e.get("source") == s and e.get("target") == t and e.get("relation") == edge.get("relation"):
                return {"error": "该边已存在"}
        clean = {"source": s, "target": t, "relation": edge.get("relation", "")}
        self._edges.append(clean)
        self._neighbors = self._build_neighbors()
        self._save()
        return {"added": f"{s}->{t} ({clean['relation']})", "edges": len(self._edges)}

    def update_anchor(self, node_id, anchor):
        n = self._by_id.get(node_id)
        if n is None:
            return {"error": f"未找到节点 {node_id}"}
        n["anchor"] = anchor
        self._save()
        return {"updated": node_id, "anchor": anchor}

    # ---- 串联：graph 查关联 → 基于关联模块出题（读模拟题库，复用 exam 校验） ----
    def related_questions(self, node_id, count=10, exam_path=None):
        n = self._by_id.get(node_id)
        if n is None:
            return {"error": f"未找到节点 {node_id}"}
        # 1. 收集该节点 + 关联节点的 module
        rels = self.get_relations(node_id)
        modules = {n.get("module")}
        for r in rels:
            if r.get("module"):
                modules.add(r["module"])
        # 2. 读模拟题库
        path = Path(exam_path) if exam_path else DEFAULT_EXAM_PATH
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {"error": "题库加载失败"}
        pool = data.get("questions", []) if isinstance(data, dict) else []
        # 3. 优先取关联 module 的题，不足再从全库补
        by_mod = [q for q in pool if q.get("module") in modules]
        other = [q for q in pool if q not in by_mod]
        picked = by_mod[:count]
        if len(picked) < count:
            picked += other[: count - len(picked)]
        return {
            "node": {"id": n.get("id"), "name": n.get("name"), "module": n.get("module")},
            "relations": [{"name": r.get("name"), "module": r.get("module"), "relation": r.get("relation")} for r in rels],
            "modules_used": sorted(modules),
            "count": len(picked),
            "questions": picked,
        }


# 默认数据位置（相对本仓库）
DEFAULT_GRAPH_PATH = (
    Path(__file__).resolve().parent.parent.parent / "docs" / "public" / "graph-data.json"
)
DEFAULT_EXAM_PATH = (
    Path(__file__).resolve().parent.parent.parent / "docs" / "public" / "quiz-mock.json"
)

# 节点/边必填字段（落盘前校验）
NODE_REQUIRED = ["id", "name", "module"]
EDGE_REQUIRED = ["source", "target", "relation"]
VALID_MODULES = ["ai", "os", "software", "agent", "hardware"]
