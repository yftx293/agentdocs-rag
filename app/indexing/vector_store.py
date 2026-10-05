"""向量存储：抽象接口 + FAISS 实现（IndexFlatIP + L2 归一化 = 余弦）。"""

from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np


class VectorStore:
    def add(self, ids: list[str], vectors: np.ndarray) -> None:  # pragma: no cover
        raise NotImplementedError

    def search(self, query: np.ndarray, top_k: int) -> list[tuple[str, float]]:  # pragma: no cover
        raise NotImplementedError


class FAISSVectorStore(VectorStore):
    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.ids: list[str] = []

    def add(self, ids: list[str], vectors: np.ndarray) -> None:
        self.index.add(np.asarray(vectors, dtype="float32"))
        self.ids.extend(ids)

    def search(self, query: np.ndarray, top_k: int) -> list[tuple[str, float]]:
        q = np.asarray(query, dtype="float32").reshape(1, -1)
        scores, idxs = self.index.search(q, min(top_k, self.index.ntotal))
        out: list[tuple[str, float]] = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1:
                continue
            out.append((self.ids[int(idx)], float(score)))
        return out

    def save(self, index_path: Path, ids_path: Path) -> None:
        faiss.write_index(self.index, str(index_path))
        ids_path.write_text(json.dumps(self.ids, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, index_path: Path, ids_path: Path) -> "FAISSVectorStore":
        store = cls(dim=0)
        store.index = faiss.read_index(str(index_path))
        store.dim = store.index.d
        store.ids = json.loads(ids_path.read_text(encoding="utf-8"))
        return store
