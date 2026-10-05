"""S9 失败归因：找出检索未命中的题目，归因到 数据缺失 / 分块缺失 / 检索未命中。

用法：
    .venv/Scripts/python.exe scripts/failure_analysis.py
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.schemas import Chunk
from app.evaluation.dataset import load_dataset
from app.indexing.bm25_index import BM25Index
from app.indexing.embeddings import Embedder
from app.indexing.vector_store import FAISSVectorStore
from app.retrieval.balanced import retrieve_balanced
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.vector import VectorRetriever


def main() -> None:
    setup_logging()
    settings = get_settings()
    processed = Path(settings.data.processed_dir)
    raw = Path(settings.data.raw_dir)

    chunks = [Chunk.model_validate_json(l) for l in (processed / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    chunk_map = {c.chunk_id: c for c in chunks}

    vs = FAISSVectorStore.load(processed / "faiss.index", processed / "vector_ids.json")
    bm25 = BM25Index.load(processed / "bm25_index")
    embedder = Embedder(settings.embedding.model, device=settings.embedding.device, normalize=settings.embedding.normalize, max_seq_length=settings.embedding.max_seq_length)
    vr = VectorRetriever(vs, embedder, settings.indexing.vector.top_n)
    br = BM25Retriever(bm25, settings.indexing.bm25.top_n)

    samples = load_dataset(Path(settings.data.eval_dir) / "retrieval_eval.jsonl")
    failures: list[dict] = []
    for s in samples:
        hits = retrieve_balanced(s.question, s.target_projects, vr, br, chunk_map, rrf_k=settings.indexing.fusion.rrf_k)
        retrieved = set()
        for cid in hits:
            c = chunk_map.get(cid)
            if c:
                retrieved.add(f"{c.metadata.project}:{c.metadata.source_path}")
        golden = s.expected_source_set()
        if retrieved & golden:
            continue  # 命中

        data_gap, chunking_gap, retrieval_miss = [], [], []
        for g in golden:
            proj, _, rel = g.partition(":")
            if not (raw / proj / rel).exists():
                data_gap.append(g)
            elif not any(c.metadata.project == proj and c.metadata.source_path == rel for c in chunks):
                chunking_gap.append(g)
            else:
                retrieval_miss.append(g)
        failures.append({
            "question": s.question,
            "intent": s.intent.value,
            "projects": s.target_projects,
            "golden": sorted(golden),
            "data_gap": data_gap,
            "chunking_gap": chunking_gap,
            "retrieval_miss": retrieval_miss,
        })

    print(f"总题数 {len(samples)}，检索未命中 {len(failures)} 题")
    data_issues = sum(1 for f in failures if f["data_gap"])
    chunk_issues = sum(1 for f in failures if f["chunking_gap"])
    retrieval_issues = sum(1 for f in failures if f["retrieval_miss"])
    print(f"  数据缺失(语料无该文件): {data_issues}")
    print(f"  分块缺失(文件在但无chunk): {chunk_issues}")
    print(f"  检索未命中(chunk在但没排进): {retrieval_issues}")

    lines = ["# 失败归因分析（S9）", "", f"总题数 {len(samples)}，检索未命中 {len(failures)} 题", ""]
    lines.append("## 归因统计")
    lines.append(f"- 数据缺失：{data_issues}")
    lines.append(f"- 分块缺失：{chunk_issues}")
    lines.append(f"- 检索未命中：{retrieval_issues}")
    lines.append("")
    lines.append("## 失败题目明细")
    lines.append("")
    for f in failures:
        lines.append(f"### {f['question']}")
        lines.append(f"- intent: {f['intent']} · 项目: {f['projects']}")
        lines.append(f"- golden: {f['golden']}")
        if f["data_gap"]:
            lines.append(f"- **数据缺失**: {f['data_gap']}")
        if f["chunking_gap"]:
            lines.append(f"- **分块缺失**: {f['chunking_gap']}")
        if f["retrieval_miss"]:
            lines.append(f"- **检索未命中**: {f['retrieval_miss']}")
        lines.append("")
    Path("docs/failure-analysis.md").write_text("\n".join(lines), encoding="utf-8")
    print("报告已写入 docs/failure-analysis.md")


if __name__ == "__main__":
    main()
