"""Embedding 模块：与 Vector DB 解耦的 embed_documents / embed_query 接口（PRD §12）。"""

from __future__ import annotations

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from app.core.logging import get_logger

log = get_logger(__name__)


class Embedder:
    def __init__(self, model_name: str, device: str = "cpu", normalize: bool = True,
                 max_seq_length: int = 8192):
        if device == "cuda" and not torch.cuda.is_available():
            log.warning("CUDA 不可用，回退到 CPU")
            device = "cpu"
        log.info("加载 embedding 模型 %s (device=%s, max_seq_length=%d)", model_name, device, max_seq_length)
        self.model = SentenceTransformer(model_name, device=device)
        self.model.max_seq_length = max_seq_length
        if device == "cuda":
            self.model = self.model.half()  # fp16：减半显存 + 启用 flash attention
        self.normalize = normalize

    def embed_documents(self, texts: list[str], batch_size: int = 16) -> np.ndarray:
        return self._encode(texts, batch_size)

    def embed_query(self, text: str) -> np.ndarray:
        return self._encode([text], batch_size=1)[0]

    def _encode(self, texts: list[str], batch_size: int) -> np.ndarray:
        vecs = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=self.normalize,
            show_progress_bar=False,
        )
        return np.asarray(vecs, dtype="float32")
