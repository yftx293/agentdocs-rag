"""S5 索引构建入口：embedding + FAISS + BM25。

用法：
    uv run python scripts/build_index.py
"""

from pathlib import Path

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.schemas import Chunk
from app.indexing.bm25_index import BM25Index
from app.indexing.embeddings import Embedder
from app.indexing.vector_store import FAISSVectorStore


def main() -> None:
    setup_logging()
    settings = get_settings()
    processed = Path(settings.data.processed_dir)

    chunks = [Chunk.model_validate_json(l) for l in (processed / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    ids = [c.chunk_id for c in chunks]
    texts = [c.embedding_text for c in chunks]

    embedder = Embedder(settings.embedding.model, device=settings.embedding.device, normalize=settings.embedding.normalize, max_seq_length=settings.embedding.max_seq_length)
    vectors = embedder.embed_documents(texts)

    vs = FAISSVectorStore(dim=vectors.shape[1])
    vs.add(ids, vectors)
    vs.save(processed / "faiss.index", processed / "vector_ids.json")

    bm25 = BM25Index()
    bm25.build(ids, texts)
    bm25.save(processed / "bm25_index")

    print(f"\n索引构建完成：{len(chunks)} chunks，向量维度 {vectors.shape[1]}，FAISS + BM25 已保存。")


if __name__ == "__main__":
    main()
