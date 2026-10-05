"""Query Analysis（V0 规则版）：识别 intent 与涉及项目。

V1 将升级为 LLM 版（PRD §16/§29 决策 12）。V0 用项目名词典 + intent 关键词规则。
"""

from __future__ import annotations

import re

from app.core.schemas import Intent, QueryPlan

_PROJECT_PATTERNS: list[tuple[str, str]] = [
    ("pi", r"\bpi\b"),
    ("tau", r"\btau\b"),
    ("mini-swe-agent", r"\bmini[- ]?swe[- ]?agent\b"),
    ("openhands", r"\bopen[- ]?hands\b"),
    ("langgraph", r"\blang[- ]?graph\b"),
]

# 顺序即优先级（compare > architecture > implementation > explain）
_INTENT_RULES: list[tuple[Intent, list[str]]] = [
    (Intent.COMPARE, ["区别", "对比", "不同", "异同", "差异", "比较", " compare ", " vs ", "versus"]),
    (Intent.ARCHITECTURE, ["架构", "结构", "模块", "组成", "architecture"]),
    (Intent.IMPLEMENTATION, ["实现", "参考", "借鉴", "implement"]),
    (Intent.EXPLAIN, ["如何", "怎么", "是什么", "工作", "原理", "explain", "how "]),
]


def analyze(question: str) -> QueryPlan:
    q = question.lower()

    projects: list[str] = []
    for name, pat in _PROJECT_PATTERNS:
        if re.search(pat, q):
            projects.append(name)

    intent = Intent.EXPLAIN
    for it, kws in _INTENT_RULES:
        if any(k in q for k in kws):
            intent = it
            break

    return QueryPlan(intent=intent, projects=projects, query=question)
