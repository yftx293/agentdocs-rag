"""生成：调用 DeepSeek API，按 intent 模板生成，映射并渲染 citation。

红线：本模块会把 context 片段外发给 DeepSeek，S8 前已获用户确认。
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

import httpx

from app.context.builder import ContextResult
from app.core.schemas import Citation, Intent
from app.generation.prompts import COMMON_SYSTEM, build_user_prompt

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"


@dataclass
class GenerationResult:
    answer: str
    citations: list[Citation] = field(default_factory=list)
    sources_text: str = ""
    usage: dict = field(default_factory=dict)


def _number_context(ctx: ContextResult) -> str:
    parts: list[str] = []
    for i, (c, cit) in enumerate(zip(ctx.chunks, ctx.citations), 1):
        section = cit.get("section") or "(root)"
        lines = f"L{cit.get('start_line')}-{cit.get('end_line')}" if cit.get("start_line") else ""
        parts.append(f"[{i}] [{cit['project']} | {cit['source_path']} | {section} {lines}]\n{c.text}")
    return "\n\n".join(parts)


def _call_deepseek(system: str, user: str, api_key: str, model: str, temperature: float) -> tuple[str, dict]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "stream": False,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = httpx.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    usage = {k: v for k, v in data.get("usage", {}).items() if isinstance(v, int)}
    return data["choices"][0]["message"]["content"], usage


def _extract_cited(answer: str) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for n in re.findall(r"\[(\d+)\]", answer):
        n = int(n)
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def render_sources(indexed: list[tuple[int, Citation]]) -> str:
    if not indexed:
        return ""
    lines = ["\nSources:"]
    for idx, c in indexed:
        loc = f"  Lines {c.start_line}-{c.end_line}" if c.start_line else ""
        lines.append(f"[{idx}] {c.project} / {c.source_path}")
        if c.section:
            lines.append(f"    {c.section}")
        lines.append(f"    {c.source_url}{loc}")
    return "\n".join(lines)


def generate(
    question: str,
    intent: Intent,
    context: ContextResult,
    api_key: str | None = None,
    model: str = "deepseek-chat",
    temperature: float = 0.0,
) -> GenerationResult:
    api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 DEEPSEEK_API_KEY（请在环境变量中设置）")

    numbered = _number_context(context)
    user = build_user_prompt(question, intent, numbered)
    answer, usage = _call_deepseek(COMMON_SYSTEM, user, api_key, model, temperature)

    used = sorted(_extract_cited(answer))
    indexed: list[tuple[int, Citation]] = []
    for i in used:
        if 1 <= i <= len(context.citations):
            indexed.append((i, Citation(**context.citations[i - 1])))
    sources = render_sources(indexed)
    citations = [c for _, c in indexed]
    return GenerationResult(answer=answer, citations=citations, sources_text=sources, usage=usage)
