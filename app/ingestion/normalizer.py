"""文档标准化：frontmatter 剥离、换行统一、标题提取、来源类型分类。"""

from __future__ import annotations

import re

from app.core.schemas import SourceType

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def strip_frontmatter(text: str) -> tuple[str, dict]:
    """剥离 YAML frontmatter，返回 (剩余文本, frontmatter 字典)。"""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return text, {}
    meta: dict = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            k = k.strip().lower()
            v = v.strip().strip('"').strip("'")
            meta[k] = v
    return text[m.end() :], meta


def normalize(text: str) -> tuple[str, str | None]:
    """返回 (规范化文本, 标题)。标题优先 frontmatter.title，其次第一个 H1。"""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    body, meta = strip_frontmatter(text)
    title = meta.get("title") or extract_title(body)
    return body.strip(), title


def extract_title(text: str) -> str | None:
    """提取第一个 H1 标题。"""
    m = _H1_RE.search(text)
    return m.group(1).strip() if m else None


def classify_source_type(rel_path: str) -> SourceType:
    """按路径/文件名分类来源类型。"""
    name = rel_path.rsplit("/", 1)[-1].lower()
    if name == "readme.md":
        return SourceType.README
    low = rel_path.lower()
    if any(seg in low for seg in ("specs/", "dev-notes/", "architecture", "/adr", "design")):
        return SourceType.DESIGN
    return SourceType.DOCS
