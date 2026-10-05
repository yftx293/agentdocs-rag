"""Markdown-aware Parent/Child 分块。

- 按标题切 Section（Parent），heading_path 完整追踪
- Code Fence 与 Table 视为原子块，绝不在内部切分
- Child chunk 用段落/句子级滑动窗口 + 轻量 overlap
- chunk_id = sha1(parent_id + text)，稳定可复现

Token 计数暂用 ~4 字符/token 估算，S5 接入真实 XLM-R tokenizer 后替换。
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.core.schemas import Chunk, Document, DocumentMetadata

_HEADING_RE = re.compile(r"^(\s{0,3})(#{1,6})\s+(.+?)\s*$")
_FENCE_OPEN_RE = re.compile(r"^(\s*)(`{3,}|~{3,})")
_TABLE_LINE_RE = re.compile(r"^\s*\|")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")

_CHARS_PER_TOKEN = 4        # 估算常数
_MAX_PIECE_TOKENS = 150     # 段落超过该值才做句子切分


def estimate_tokens(text: str) -> int:
    """粗略 token 估算（英文技术文本 ~4 字符/token）。S5 替换为真实 tokenizer。"""
    return max(1, len(text) // _CHARS_PER_TOKEN)


@dataclass
class Block:
    type: str                 # heading / code / table / text
    text: str
    level: int = 0
    heading_text: str = ""
    start_line: int = 0
    end_line: int = 0


@dataclass
class Piece:
    text: str
    start_line: int
    end_line: int
    atomic: bool = False


@dataclass
class Section:
    heading_path: list[str]
    blocks: list[Block]
    start_line: int
    end_line: int


def parse_blocks(text: str) -> list[Block]:
    """把 markdown 文本解析为 heading/code/table/text 块序列。"""
    lines = text.split("\n")
    blocks: list[Block] = []
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i]

        m = _HEADING_RE.match(line)
        if m:
            blocks.append(
                Block("heading", line, level=len(m.group(2)), heading_text=m.group(3).strip(),
                      start_line=i + 1, end_line=i + 1)
            )
            i += 1
            continue

        m = _FENCE_OPEN_RE.match(line)
        if m:
            open_indent = len(m.group(1))
            fence_char = m.group(2)[0]
            fence_len = len(m.group(2))
            start = i
            j = i + 1
            max_close_indent = max(3, open_indent)
            while j < n:
                cm = re.match(rf"^(\s*)({re.escape(fence_char)}{{{fence_len},}})\s*$", lines[j])
                if cm and len(cm.group(1)) <= max_close_indent:
                    break
                j += 1
            if j >= n:
                j = n - 1
            blocks.append(Block("code", "\n".join(lines[start:j + 1]), start_line=start + 1, end_line=j + 1))
            i = j + 1
            continue

        if _TABLE_LINE_RE.match(line):
            start = i
            j = i
            while j < n and _TABLE_LINE_RE.match(lines[j]):
                j += 1
            blocks.append(Block("table", "\n".join(lines[start:j]), start_line=start + 1, end_line=j))
            i = j
            continue

        start = i
        j = i
        while j < n:
            l = lines[j]
            if _HEADING_RE.match(l) or _FENCE_OPEN_RE.match(l) or _TABLE_LINE_RE.match(l):
                break
            j += 1
        text = "\n".join(lines[start:j])
        if text.strip():
            blocks.append(Block("text", text, start_line=start + 1, end_line=j))
        i = j

    return blocks


def build_sections(blocks: list[Block]) -> list[Section]:
    """按标题层级把块序列组装成 Section，追踪完整 heading_path。"""
    sections: list[Section] = []
    heading_stack: list[tuple[int, str]] = []
    current: list[Block] | None = None
    current_path: list[str] = []

    for b in blocks:
        if b.type == "heading":
            if current:
                sections.append(Section(list(current_path), current,
                                        current[0].start_line, current[-1].end_line))
            while heading_stack and heading_stack[-1][0] >= b.level:
                heading_stack.pop()
            heading_stack.append((b.level, b.heading_text))
            current_path = [t for _, t in heading_stack]
            current = [b]
        else:
            if current is None:
                current = [b]
            else:
                current.append(b)
    if current:
        sections.append(Section(list(current_path), current, current[0].start_line, current[-1].end_line))
    return sections


def _slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "untitled"


def _split_section_into_groups(blocks: list[Block], parent_max_tokens: int) -> list[list[Block]]:
    """超长 Section 二次拆分成多个 Parent 组；原子块绝不在内部拆分。"""
    groups: list[list[Block]] = []
    cur: list[Block] = []
    cur_tokens = 0
    for b in blocks:
        bt = estimate_tokens(b.text)
        if bt > parent_max_tokens:
            if cur:
                groups.append(cur)
                cur = []
                cur_tokens = 0
            groups.append([b])
        elif cur_tokens + bt > parent_max_tokens:
            if cur:
                groups.append(cur)
            cur = [b]
            cur_tokens = bt
        else:
            cur.append(b)
            cur_tokens += bt
    if cur:
        groups.append(cur)
    return groups


def _text_pieces(block: Block) -> list[Piece]:
    """把 text 块切成段落；长段落再切句子。行号精确到段落级。"""
    pieces: list[Piece] = []
    lines = block.text.split("\n")
    cur: list[str] = []
    cur_start = block.start_line
    line_no = block.start_line

    def flush(end_line: int) -> None:
        nonlocal cur, cur_start
        if cur:
            para = "\n".join(cur).strip()
            if para:
                if estimate_tokens(para) <= _MAX_PIECE_TOKENS:
                    pieces.append(Piece(para, cur_start, end_line))
                else:
                    for s in _SENTENCE_RE.split(para):
                        s = s.strip()
                        if s:
                            pieces.append(Piece(s, cur_start, end_line))
            cur = []

    for ln in lines:
        if ln.strip() == "":
            flush(line_no - 1)
            cur_start = line_no + 1
        else:
            cur.append(ln)
        line_no += 1
    flush(line_no - 1)
    return pieces


def _section_pieces(blocks: list[Block]) -> list[Piece]:
    """把 Section 的块转为可滑动窗口的 piece 列表（code/table 原子）。"""
    pieces: list[Piece] = []
    for b in blocks:
        if b.type in ("code", "table"):
            pieces.append(Piece(b.text, b.start_line, b.end_line, atomic=True))
        elif b.type == "heading":
            pieces.append(Piece(b.heading_text, b.start_line, b.end_line))
        else:
            pieces.extend(_text_pieces(b))
    return pieces


def _overlap_tail(pieces: list[Piece], overlap_tokens: int) -> list[Piece]:
    """从尾部取整块 piece 凑够 overlap 的 token，返回新列表。"""
    tail: list[Piece] = []
    total = 0
    for p in reversed(pieces):
        tail.append(p)
        total += estimate_tokens(p.text)
        if total >= overlap_tokens:
            break
    return list(reversed(tail))


def _pieces_to_chunk(parent_id: str, pieces: list[Piece], base_meta: DocumentMetadata,
                     heading_path: list[str], project: str) -> Chunk:
    text = "\n\n".join(p.text for p in pieces).strip()
    meta = base_meta.model_copy(deep=True)
    meta.heading_path = list(heading_path)
    meta.content_hash = None
    chunk_id = hashlib.sha1(f"{parent_id}\x00{text}".encode("utf-8")).hexdigest()
    parts = [f"Project: {project}"]
    if heading_path:
        parts.append("Section: " + " > ".join(heading_path))
    embedding_text = "\n".join(parts) + "\n\n" + text
    return Chunk(
        chunk_id=chunk_id,
        parent_id=parent_id,
        text=text,
        embedding_text=embedding_text,
        metadata=meta,
        start_line=pieces[0].start_line,
        end_line=pieces[-1].end_line,
        token_count=estimate_tokens(text),
    )


def _build_child_chunks(parent_id: str, pieces: list[Piece], base_meta: DocumentMetadata,
                        heading_path: list[str], project: str,
                        child_max_tokens: int, overlap_tokens: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    current: list[Piece] = []
    current_tokens = 0
    for p in pieces:
        pt = estimate_tokens(p.text)
        if pt > child_max_tokens:
            if current:
                chunks.append(_pieces_to_chunk(parent_id, current, base_meta, heading_path, project))
                current = []
                current_tokens = 0
            chunks.append(_pieces_to_chunk(parent_id, [p], base_meta, heading_path, project))
            continue
        if current_tokens + pt <= child_max_tokens:
            current.append(p)
            current_tokens += pt
        else:
            chunks.append(_pieces_to_chunk(parent_id, current, base_meta, heading_path, project))
            current = _overlap_tail(current, overlap_tokens)
            current.append(p)
            current_tokens = sum(estimate_tokens(x.text) for x in current)
    if current:
        chunks.append(_pieces_to_chunk(parent_id, current, base_meta, heading_path, project))
    return chunks


def chunk_document(doc: Document, parent_max_tokens: int, child_max_tokens: int,
                   overlap_tokens: int, heading_only: bool = False) -> tuple[list[Document], list[Chunk]]:
    """把一篇文件级 Document 切成 parents + chunks。

    heading_only=True 时：每个 section 直接作为一个 chunk（不二次切分），
    用于 benchmark 的策略 C。
    """
    parents: list[Document] = []
    chunks: list[Chunk] = []
    project = doc.metadata.project
    source_path = doc.metadata.source_path
    sections = build_sections(parse_blocks(doc.text))
    slug_counts: dict[str, int] = {}

    for section in sections:
        base_slug = _slugify(" ".join(section.heading_path)) if section.heading_path else "untitled"
        n = slug_counts.get(base_slug, 0) + 1
        slug_counts[base_slug] = n
        slug = base_slug if n == 1 else f"{base_slug}-{n}"

        groups = [section.blocks] if heading_only else _split_section_into_groups(section.blocks, parent_max_tokens)
        for gi, group in enumerate(groups):
            part_suffix = f"#part{gi + 1}" if len(groups) > 1 else ""
            parent_id = f"{project}:{source_path}:{slug}{part_suffix}"
            parent_text = "\n\n".join(b.text for b in group).strip()
            if not parent_text:
                continue
            pmeta = doc.metadata.model_copy(deep=True)
            pmeta.heading_path = list(section.heading_path)
            pmeta.start_line = group[0].start_line
            pmeta.end_line = group[-1].end_line
            pmeta.content_hash = hashlib.sha256(parent_text.encode("utf-8")).hexdigest()
            parents.append(Document(parent_id=parent_id, text=parent_text, metadata=pmeta))

            if heading_only:
                single = Piece(parent_text, group[0].start_line, group[-1].end_line, atomic=True)
                chunks.append(_pieces_to_chunk(parent_id, [single], doc.metadata, section.heading_path, project))
            else:
                pieces = _section_pieces(group)
                chunks.extend(_build_child_chunks(
                    parent_id, pieces, doc.metadata, section.heading_path, project,
                    child_max_tokens, overlap_tokens,
                ))

    return parents, chunks
