"""BM25 索引：bm25s + 中英混合分词。

分词策略：先 jieba 切中文，再对 ASCII 段按非字母数字二次切分，
使英文技术术语（项目名/API/类名）在中文 query 与英文文档间一致可比。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import bm25s
import jieba

_ASCII_RE = re.compile(r"[^a-z0-9]+")


def tokenize(text: str) -> list[str]:
    text = text.lower()
    tokens: list[str] = []
    for seg in jieba.lcut(text):
        for t in _ASCII_RE.split(seg):
            t = t.strip()
            if t:
                tokens.append(t)
    return tokens


class BM25Index:
    def __init__(self) -> None:
        self.retriever: bm25s.BM25 | None = None
        self.ids: list[str] = []

    def build(self, ids: list[str], texts: list[str]) -> None:
        corpus = [tokenize(t) for t in texts]
        self.retriever = bm25s.BM25()
        self.retriever.index(corpus, show_progress=False)
        self.ids = list(ids)

    def search(self, query: str, top_k: int) -> list[tuple[str, float]]:
        if self.retriever is None:
            return []
        qt = tokenize(query)
        res = self.retriever.retrieve([qt], k=min(top_k, len(self.ids)), show_progress=False)
        out: list[tuple[str, float]] = []
        for idx, score in zip(res.documents[0], res.scores[0]):
            out.append((self.ids[int(idx)], float(score)))
        return out

    def save(self, path: Path) -> None:
        self.retriever.save(str(path))
        Path(str(path) + ".ids.json").write_text(json.dumps(self.ids, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "BM25Index":
        obj = cls()
        obj.retriever = bm25s.BM25.load(str(path))
        obj.ids = json.loads(Path(str(path) + ".ids.json").read_text(encoding="utf-8"))
        return obj
