"""考试系统内核（可调用逻辑，纯标准库，无 MCP 依赖）。

把仓库前端 useExam.js 里的"校验 / 组卷 / 判分 / 错题本"移植为可复用的 Python 函数。
这样无论作为 MCP 工具、命令行还是库，都能被真正调用。
数据以"题目 dict 数组"为边界，字段与前端 quiz-mock.json 的 schema 一致。
"""

import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path

# ---- 与前端 useExam.js 对齐的常量 ----
MODULE_ORDER = ["ai", "os", "software", "agent", "hardware"]
MODULE_RATIO = {"ai": 0.3, "os": 0.2, "software": 0.2, "agent": 0.2, "hardware": 0.1}
EXAM_STRUCTURE = [("single", 30), ("multi", 10), ("judge", 20)]
REQUIRED_FIELDS = ["id", "type", "module", "stem", "options", "answerKeys",
                   "explanation", "chapter", "source"]
LETTERS = ["A", "B", "C", "D", "E", "F"]


# ---------------------------------------------------------------------------
# 一、校验
# ---------------------------------------------------------------------------
def _check_question(q):
    """返回单题的错误列表（空=合格）。"""
    errs = []
    if not isinstance(q, dict):
        return ["题不是对象"]
    qid = q.get("id", "?")
    prefix = f"[{qid}] "

    for k in REQUIRED_FIELDS:
        if q.get(k) in (None, ""):
            errs.append(prefix + f"缺字段 {k}")

    t = q.get("type")
    if t not in ("single", "multi", "judge"):
        errs.append(prefix + f"type 非法: {t}")

    if q.get("source") != "mock":
        errs.append(prefix + "source 必须为 'mock'")

    if q.get("module") not in MODULE_ORDER:
        errs.append(prefix + f"module 非法: {q.get('module')}")

    opts = q.get("options")
    keys = [o.get("key") for o in opts] if isinstance(opts, list) else []
    ans = q.get("answerKeys") or []

    if not isinstance(ans, list) or len(ans) == 0:
        errs.append(prefix + "answerKeys 非空数组")
    else:
        for a in ans:
            if a not in keys:
                errs.append(prefix + f"answerKey {a} 不在 options 中")
        if len(ans) != len(set(ans)):
            errs.append(prefix + "answerKeys 有重复")

    if t == "judge":
        if len(opts) != 2 or opts[0].get("key") != "A" or opts[0].get("text") != "正确" \
                or opts[1].get("key") != "B" or opts[1].get("text") != "错误":
            errs.append(prefix + "judge options 应为 [A=正确, B=错误]")
        if len(ans) != 1 or ans[0] not in ("A", "B"):
            errs.append(prefix + "judge 答案应为 1 个 A 或 B")
    elif t == "single":
        if len(opts) != 4:
            errs.append(prefix + "single 选项数应为 4")
        if len(ans) != 1:
            errs.append(prefix + "single 答案应为 1 个")
    elif t == "multi":
        if len(opts) != 6:
            errs.append(prefix + "multi 选项数应为 6")
        if not (3 <= len(ans) <= 4):
            errs.append(prefix + "multi 正确项应为 3~4 个")

    return errs


def validate_questions(questions, autofix=False):
    """校验题目数组。返回 {valid, total, errors[]}；autofix=True 时给出修复报告。"""
    errors = []
    seen = set()
    for q in questions:
        e = _check_question(q)
        qid = q.get("id", "?")
        if qid in seen:
            e.append(f"[{qid}] id 重复")
        seen.add(qid)
        errors.extend(e)

    return {
        "valid": len(errors) == 0,
        "total": len(questions),
        "errors": errors,
        "autofix": autofix,
    }


# ---------------------------------------------------------------------------
# 二、组卷（对齐 useExam.js 的 draw + buildPaper + shuffleOptions）
# ---------------------------------------------------------------------------
def _shuffle_options(q):
    """打乱选项顺序，并同步换算 answerKeys 为新顺序下的字母。"""
    order = list(range(len(q["options"])))
    random.shuffle(order)
    new_opts = [q["options"][i] for i in order]
    old_index = {o["key"]: i for i, o in enumerate(q["options"])}
    new_keys = sorted(
        [LETTERS[order.index(old_index[k])] for k in q["answerKeys"] if k in old_index]
    )
    return new_opts, new_keys


def _draw(pool, count, ratio):
    """按模块占比从池里抽 count 道；不足时从剩余补。"""
    by_module = {}
    for q in pool:
        by_module.setdefault(q["module"], []).append(q)
    rest = list(pool)
    drawn = []
    expected = {}
    assigned = 0
    last = MODULE_ORDER[-1]
    for m in MODULE_ORDER:
        if m == last:
            expected[m] = count - assigned
        else:
            expected[m] = round(count * (ratio.get(m, 0) or 0))
            assigned += expected[m]
    for m in MODULE_ORDER:
        pool_m = by_module.get(m, [])
        take = min(expected.get(m, 0), len(pool_m))
        picked = random.sample(pool_m, take) if pool_m else []
        drawn.extend(picked)
        for q in picked:
            if q in rest:
                rest.remove(q)
    if len(drawn) < count:
        drawn.extend(random.sample(rest, count - len(drawn)) if rest else [])
    return drawn


def assemble_paper(questions, single=30, multi=10, judge=20,
                   ratio=None, shuffle=True):
    """按题型结构 + 模块配比组卷。返回 {paper, structure}。"""
    ratio = ratio or MODULE_RATIO
    structure = [("single", single), ("multi", multi), ("judge", judge)]
    picked = []
    for t, cnt in structure:
        type_pool = [q for q in questions if q["type"] == t]
        picked.extend(_draw(type_pool, cnt, ratio))

    paper = []
    for q in picked:
        if shuffle:
            opts, keys = _shuffle_options(q)
        else:
            opts, keys = q["options"], sorted(q["answerKeys"])
        paper.append({
            "id": q["id"], "type": q["type"], "module": q["module"],
            "stem": q["stem"], "options": opts, "answerKeys": keys,
            "explanation": q.get("explanation", ""),
            "chapter": q.get("chapter", ""), "source": q.get("source", "mock"),
        })
    return {"paper": paper, "structure": structure}


# ---------------------------------------------------------------------------
# 三、判分（多选全对才给分）
# ---------------------------------------------------------------------------
def grade_paper(paper, answers):
    """answers: 每题所选 key 数组（长度与 paper 相同）。返回评分结果。"""
    if not isinstance(answers, list) or len(answers) != len(paper):
        return {"error": "answers 需与 paper 题数一致"}
    results = []
    correct_cnt = 0
    for q, ans in zip(paper, answers):
        ans = sorted(ans or [])
        correct = sorted(q["answerKeys"]) == ans and len(ans) > 0
        if correct:
            correct_cnt += 1
        results.append({
            "id": q["id"], "type": q["type"], "answer": ans,
            "correct": correct, "correct_keys": sorted(q["answerKeys"]),
            "explanation": q.get("explanation", ""),
            "source": q.get("source", "mock"),
        })
    return {
        "score": correct_cnt,
        "total": len(paper),
        "wrong": [r["id"] for r in results if not r["correct"]],
        "results": results,
    }


# ---------------------------------------------------------------------------
# 四、错题本（持久化到本地 JSON 文件）
# ---------------------------------------------------------------------------
class WrongStore:
    """错题本：只存元信息，持久化到 JSON 文件（跨进程可复用）。"""

    def __init__(self, path="wrong_store.json"):
        self.path = Path(path)
        self._data = self._load()

    def _load(self):
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save(self):
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def add(self, wrongs):
        """wrongs: [{id, source, myAnswer}]，答错的题。
        同一个 (id, source) 去重，更新 myAnswer 与时间。"""
        added = 0
        for w in wrongs:
            key = (w.get("id"), w.get("source", "mock"))
            found = next(
                (x for x in self._data
                 if x.get("id") == key[0] and x.get("source") == key[1]), None
            )
            record = {
                "id": key[0], "source": key[1],
                "myAnswer": w.get("myAnswer", []),
                "at": datetime.now(timezone.utc).isoformat(),
            }
            if found is not None:
                self._data.remove(found)
            self._data.append(record)
            added += 1
        self._save()
        return {"added": added, "total": len(self._data)}

    def list(self):
        return self._data

    def remove(self, qid, source="mock"):
        before = len(self._data)
        self._data = [x for x in self._data
                      if not (x.get("id") == qid and x.get("source") == source)]
        self._save()
        return {"removed": before - len(self._data), "total": len(self._data)}

    def clear(self):
        self._data = []
        self._save()
        return {"cleared": True, "total": 0}


# ---------------------------------------------------------------------------
# 五、题目生成（MCP 工具封装：内部调 LLM 生成候选，再自动校验——不依赖 skill）
# ---------------------------------------------------------------------------
DEFAULT_EXAM_PATH = (
    Path(__file__).resolve().parent.parent.parent / "docs" / "public" / "quiz-mock.json"
)

# LLM 端点：默认 Ollama 的 OpenAI 兼容接口，可用环境变量覆盖
LLM_BASE = os.environ.get("LLM_BASE", "http://localhost:11434/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen2.5:7b")
LLM_KEY = os.environ.get("LLM_KEY", "")

# 科目无关的出题规范（内置，不再依赖 exam-builder skill）
PROMPT_TEMPLATE = """你是一名严谨的测评命题专家。请依据下面的学习内容，按要求生成标准化考试题目 JSON 数组。

# 学习内容（材料）
{material}

# 题型与数量要求
- 单选题（single，4 个选项 A-D，恰 1 个正确）：{single} 题
- 多选题（multi，6 个选项 A-F，恰 3~4 个正确）：{multi} 题
- 判断题（judge，选项固定 [{A:正确,B:错误}]，1 个答案）：{judge} 题
- 所有题的 module 均为 {module}，chapter 均为 {chapter}
- id 从 {start_id} 起连续编号（如 {start_id}、{start_id_plus}），source 均为 "mock"

# 每题硬性要求
- 每题只考一个明确、无歧义的知识点；题干自包含。
- 干扰项用"真实但错误"（因果颠倒/张冠李戴/以偏概全/过度绝对化），不要明显荒谬或与题干同义。
- 解析必须两部分：正确项为何对 + 每个错项错在哪。
- 判断题错误项用绝对化陷阱句式（只要…就…/一定/唯一/所有/完全/无需…），正向题描述机制事实。
- 严格忠实于材料，不臆造材料之外的内容。

# 输出
只输出 JSON 数组，不要多余文字。每个元素形如：
{"id":"M001","type":"single","module":"ai","stem":"…","options":[{"key":"A","text":"…"},{"key":"B","text":"…"},{"key":"C","text":"…"},{"key":"D","text":"…"}],"answerKeys":["A"],"explanation":"…","chapter":"/ch01_ai_foundation","source":"mock"}"""


def _call_llm(messages):
    """调用 OpenAI 兼容 chat/completions（Ollama 亦兼容）。返回助手文本。"""
    import json as _json
    import urllib.request

    url = LLM_BASE.rstrip("/") + "/chat/completions"
    body = {"model": LLM_MODEL, "messages": messages, "temperature": 0.7}
    req = urllib.request.Request(
        url, data=_json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    if LLM_KEY:
        req.add_header("Authorization", "Bearer " + LLM_KEY)
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = _json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def _extract_json_array(text):
    import re
    m = re.search(r"\[[\s\S]*\]", text or "")
    return m.group(0) if m else (text or "").strip()


def next_id_start(exam_path=None):
    """从题库现有最大 M 编号 +1。"""
    path = Path(exam_path) if exam_path else DEFAULT_EXAM_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return 1
    qs = data.get("questions", []) if isinstance(data, dict) else []
    mx = 0
    for q in qs:
        try:
            mx = max(mx, int(str(q.get("id", "")).lstrip("M")))
        except ValueError:
            pass
    return mx + 1


def generate_questions(material, module="ai", chapter="/ch01_ai_foundation",
                       single=10, multi=3, judge=7, start_id=None, exam_path=None):
    """按出题规范用 LLM 生成候选，再自动校验。

    返回 {valid, errors, questions}；questions 为已校验/规范化的候选（id 连续、source=mock）。
    若 LLM 不可用或生成内容无法解析，返回 {error}。
    """
    if start_id is None:
        start_id = next_id_start(exam_path)
    fmt_id = lambda n: f"M{n:03d}"
    user_prompt = PROMPT_TEMPLATE
    repl = {
        "{material}": material, "{single}": str(single), "{multi}": str(multi),
        "{judge}": str(judge), "{module}": module, "{chapter}": chapter,
        "{start_id}": fmt_id(start_id), "{start_id_plus}": fmt_id(start_id + 1),
    }
    for k, v in repl.items():
        user_prompt = user_prompt.replace(k, v)
    try:
        raw = _call_llm([
            {"role": "system", "content": "你是出题助手，只输出 JSON 数组。"},
            {"role": "user", "content": user_prompt},
        ])
    except Exception as e:  # noqa: BLE001
        return {"error": f"LLM 调用失败（请检查 LLM_BASE / LLM_MODEL / LLM_KEY）：{e}"}

    try:
        candidates = json.loads(_extract_json_array(raw))
    except Exception as e:  # noqa: BLE001
        return {"error": f"生成内容无法解析为 JSON 数组：{e}"}

    if not isinstance(candidates, list):
        return {"error": "生成结果不是数组"}
    if not candidates:
        return {"error": "生成结果为空"}

    # 规范化：id 连续、source=mock
    for i, c in enumerate(candidates):
        if not isinstance(c, dict):
            continue
        c["id"] = fmt_id(start_id + i)
        c["module"] = module
        c["chapter"] = chapter
        c["source"] = "mock"

    v = validate_questions(candidates)
    return {"valid": v["valid"], "errors": v["errors"], "questions": candidates}
