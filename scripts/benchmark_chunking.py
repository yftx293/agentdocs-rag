"""S6 Chunk 策略 Benchmark：A(300/30) vs B(500/50) vs C(heading-only)。

用法：
    .venv/Scripts/python.exe scripts/benchmark_chunking.py
"""

from pathlib import Path

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.schemas import Chunk, Document
from app.evaluation.dataset import load_dataset
from app.evaluation.retrieval_metrics import evaluate
from app.indexing.bm25_index import BM25Index
from app.indexing.embeddings import Embedder
from app.indexing.vector_store import FAISSVectorStore
from app.ingestion.splitter import chunk_document
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.fusion import rrf_fuse
from app.retrieval.vector import VectorRetriever

STRATEGIES = [
    {"name": "A: 300 tokens / 30 overlap", "child_max": 300, "overlap": 30, "heading_only": False},
    {"name": "B: 500 tokens / 50 overlap", "child_max": 500, "overlap": 50, "heading_only": False},
    {"name": "C: heading-only（不二次切分）", "child_max": 500, "overlap": 50, "heading_only": True},
]


def _file_keys(chunk_ids: list[str], chunk_map: dict[str, Chunk]) -> list[str]:
    out = []
    for cid in chunk_ids:
        c = chunk_map.get(cid)
        if c:
            out.append(f"{c.metadata.project}:{c.metadata.source_path}")
    return out


def _section_keys(chunk_ids: list[str], chunk_map: dict[str, Chunk]) -> list[str]:
    out = []
    for cid in chunk_ids:
        c = chunk_map.get(cid)
        if c:
            heading = " > ".join(c.metadata.heading_path) if c.metadata.heading_path else ""
            out.append(f"{c.metadata.project}:{c.metadata.source_path} :: {heading}")
    return out


def main() -> None:
    setup_logging()
    settings = get_settings()
    processed = Path(settings.data.processed_dir)
    docs = [Document.model_validate_json(l) for l in (processed / "documents.jsonl").read_text(encoding="utf-8").splitlines()]
    samples = load_dataset(Path(settings.data.eval_dir) / "retrieval_eval.jsonl")

    embedder = Embedder(settings.embedding.model, device=settings.embedding.device, normalize=settings.embedding.normalize, max_seq_length=settings.embedding.max_seq_length)
    parent_max = settings.chunking.parent_max_tokens

    results = []
    for strat in STRATEGIES:
        print(f"\n===== 策略 {strat['name']} =====")
        chunks: list[Chunk] = []
        for doc in docs:
            _, cs = chunk_document(doc, parent_max, strat["child_max"], strat["overlap"], heading_only=strat["heading_only"])
            chunks.extend(cs)
        chunk_map = {c.chunk_id: c for c in chunks}
        print(f"  chunks: {len(chunks)}")

        ids = [c.chunk_id for c in chunks]
        texts = [c.embedding_text for c in chunks]
        vectors = embedder.embed_documents(texts)
        vs = FAISSVectorStore(dim=vectors.shape[1])
        vs.add(ids, vectors)
        bm25 = BM25Index()
        bm25.build(ids, texts)

        vr = VectorRetriever(vs, embedder, settings.indexing.vector.top_n)
        br = BM25Retriever(bm25, settings.indexing.bm25.top_n)
        vec_ranked, bm25_ranked, rrf_ranked, expected = [], [], [], []
        for s in samples:
            vh = vr.retrieve(s.question)
            bh = br.retrieve(s.question)
            rh = rrf_fuse(vh, bh, k=settings.indexing.fusion.rrf_k, top_k=settings.indexing.fusion.final_top_k)
            use_sections = bool(s.expected_sections)
            keyfn = _section_keys if use_sections else _file_keys
            vec_ranked.append(keyfn([x for x, _ in vh], chunk_map))
            bm25_ranked.append(keyfn([x for x, _ in bh], chunk_map))
            rrf_ranked.append(keyfn([x for x, _ in rh], chunk_map))
            expected.append(set(s.expected_sections) if use_sections else s.expected_source_set())

        ks = settings.evaluation.k_values
        r = {
            "name": strat["name"],
            "chunks": len(chunks),
            "vector": evaluate(vec_ranked, expected, ks),
            "bm25": evaluate(bm25_ranked, expected, ks),
            "rrf": evaluate(rrf_ranked, expected, ks),
        }
        results.append(r)
        for k in ks:
            print(f"  rrf k={k}: hit={r['rrf'][f'hit@{k}']:.3f} recall={r['rrf'][f'recall@{k}']:.3f} mrr={r['rrf'][f'mrr@{k}']:.3f}")

    print("\n========== 三策略对比（RRF） ==========")
    print(f"{'策略':32s} {'chunks':>7s} {'hit@3':>7s} {'hit@5':>7s} {'mrr@5':>7s}")
    for r in results:
        print(f"{r['name']:32s} {r['chunks']:7d} {r['rrf']['hit@3']:7.3f} {r['rrf']['hit@5']:7.3f} {r['rrf']['mrr@5']:7.3f}")

    lines = ["# Chunk 策略 Benchmark（S6）", "", f"评测集：{len(samples)} 题（4 类 intent）", "", "## 三策略对比（RRF）", ""]
    lines.append("| 策略 | chunks | hit@3 | hit@5 | mrr@5 |")
    lines.append("|---|---|---|---|---|")
    for r in results:
        lines.append(f"| {r['name']} | {r['chunks']} | {r['rrf']['hit@3']:.3f} | {r['rrf']['hit@5']:.3f} | {r['rrf']['mrr@5']:.3f} |")
    lines.append("")
    for r in results:
        lines.append(f"## {r['name']} 分阶段指标")
        lines.append(f"- vector: hit@5={r['vector']['hit@5']:.3f} mrr@5={r['vector']['mrr@5']:.3f}")
        lines.append(f"- bm25: hit@5={r['bm25']['hit@5']:.3f} mrr@5={r['bm25']['mrr@5']:.3f}")
        lines.append(f"- rrf: hit@5={r['rrf']['hit@5']:.3f} mrr@5={r['rrf']['mrr@5']:.3f}")
        lines.append("")
    Path("docs/benchmark-chunking.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n报告已写入 docs/benchmark-chunking.md")


if __name__ == "__main__":
    main()
