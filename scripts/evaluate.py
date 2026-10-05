"""S5 检索评测：在 S4 评测集上跑 vector/bm25/rrf，输出真实 Hit@K / Recall@K / MRR。

用法：
    uv run python scripts/evaluate.py
"""

from pathlib import Path

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.schemas import Chunk
from app.evaluation.dataset import load_dataset
from app.evaluation.retrieval_metrics import evaluate
from app.indexing.bm25_index import BM25Index
from app.indexing.embeddings import Embedder
from app.indexing.vector_store import FAISSVectorStore
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.fusion import rrf_fuse
from app.retrieval.vector import VectorRetriever


def _source_keys(chunk_ids: list[str], chunk_map: dict[str, Chunk]) -> list[str]:
    out = []
    for cid in chunk_ids:
        c = chunk_map.get(cid)
        if c:
            out.append(f"{c.metadata.project}:{c.metadata.source_path}")
    return out


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

    samples = load_dataset(Path(settings.data.eval_dir) / "retrieval_eval.jsonl")

    vec_ranked, bm25_ranked, rrf_ranked = [], [], []
    expected = []
    for s in samples:
        vhits = [cid for cid, _ in vr.retrieve(s.question)]
        bhits = [cid for cid, _ in br.retrieve(s.question)]
        rhits = [cid for cid, _ in rrf_fuse(vr.retrieve(s.question), br.retrieve(s.question),
                                             k=settings.indexing.fusion.rrf_k,
                                             top_k=settings.indexing.fusion.final_top_k)]
        vec_ranked.append(_source_keys(vhits, chunk_map))
        bm25_ranked.append(_source_keys(bhits, chunk_map))
        rrf_ranked.append(_source_keys(rhits, chunk_map))
        expected.append(s.expected_source_set())

    ks = settings.evaluation.k_values
    print("\n========== 检索评测结果（真实数字） ==========")
    for name, ranked in [("vector-only", vec_ranked), ("bm25-only", bm25_ranked), ("rrf-fused", rrf_ranked)]:
        m = evaluate(ranked, expected, ks)
        print(f"\n[{name}]  ({len(samples)} 题)")
        for k in ks:
            print(f"  k={k}: hit@{k}={m[f'hit@{k}']:.3f}  recall@{k}={m[f'recall@{k}']:.3f}  mrr@{k}={m[f'mrr@{k}']:.3f}")


if __name__ == "__main__":
    main()
