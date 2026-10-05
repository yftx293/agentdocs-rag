"""S7 Context Builder 演示：对 compare 查询展示项目平衡 + token 用量。

用法：
    .venv/Scripts/python.exe scripts/demo_context.py
"""

from pathlib import Path

from app.context.builder import ContextBuilder
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.schemas import Chunk
from app.evaluation.dataset import load_dataset
from app.indexing.bm25_index import BM25Index
from app.indexing.embeddings import Embedder
from app.indexing.vector_store import FAISSVectorStore
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.fusion import rrf_fuse
from app.retrieval.vector import VectorRetriever
from app.retrieval.balanced import retrieve_balanced


def main() -> None:
    setup_logging()
    settings = get_settings()
    processed = Path(settings.data.processed_dir)

    chunks = [Chunk.model_validate_json(l) for l in (processed / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    chunk_map = {c.chunk_id: c for c in chunks}

    vs = FAISSVectorStore.load(processed / "faiss.index", processed / "vector_ids.json")
    bm25 = BM25Index.load(processed / "bm25_index")
    embedder = Embedder(settings.embedding.model, device=settings.embedding.device, normalize=settings.embedding.normalize, max_seq_length=settings.embedding.max_seq_length)
    vr = VectorRetriever(vs, embedder, settings.indexing.vector.top_n)
    br = BM25Retriever(bm25, settings.indexing.bm25.top_n)

    samples = [s for s in load_dataset(Path(settings.data.eval_dir) / "retrieval_eval.jsonl") if s.intent.value == "compare"][:2]

    builder = ContextBuilder(max_tokens=4000)
    for s in samples:
        hits = retrieve_balanced(s.question, s.target_projects, vr, br, chunk_map,
                                 rrf_k=settings.indexing.fusion.rrf_k)
        retrieved = [chunk_map[cid] for cid in hits if cid in chunk_map]
        r = builder.build(retrieved, projects=s.target_projects)
        print(f"\n========== 查询：{s.question} ==========")
        print(f"目标项目：{s.target_projects}")
        print(f"项目分布：{r.project_distribution}")
        print(f"token 用量：{r.tokens}")
        print(f"选中 chunk 数：{len(r.chunks)}")
        print(f"citation 数：{len(r.citations)}")
        print("--- final_context 前 1200 字符 ---")
        print(r.text[:1200])


if __name__ == "__main__":
    main()
