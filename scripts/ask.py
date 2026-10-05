"""S9 端到端问答 + 链路观测：query → analyze → retrieve → context → generate → trace。

用法：
    .venv/Scripts/python.exe scripts/ask.py [--chain]
"""

from __future__ import annotations

import argparse
import time
import uuid
from pathlib import Path

from app.context.builder import ContextBuilder
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.schemas import Answer, Chunk, RetrievalResult, Trace, TraceStage
from app.evaluation.dataset import load_dataset
from app.generation.generator import generate
from app.indexing.bm25_index import BM25Index
from app.indexing.embeddings import Embedder
from app.indexing.vector_store import FAISSVectorStore
from app.observability.tracer import Tracer
from app.query.analyzer import analyze
from app.retrieval.balanced import retrieve_balanced
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.vector import VectorRetriever


def _to_results(hits: list[tuple[str, float]], chunk_map: dict[str, Chunk], source: str, top_n: int = 5) -> list[RetrievalResult]:
    out: list[RetrievalResult] = []
    for rank, (cid, score) in enumerate(hits[:top_n], 1):
        c = chunk_map.get(cid)
        if c:
            out.append(RetrievalResult(chunk_id=cid, parent_id=c.parent_id, text=c.text[:200],
                                       metadata=c.metadata, score=float(score), source=source, rank=rank))
    return out


def _ids_to_results(ids: list[str], chunk_map: dict[str, Chunk], source: str, top_n: int = 8) -> list[RetrievalResult]:
    out: list[RetrievalResult] = []
    for rank, cid in enumerate(ids[:top_n], 1):
        c = chunk_map.get(cid)
        if c:
            out.append(RetrievalResult(chunk_id=cid, parent_id=c.parent_id, text=c.text[:200],
                                       metadata=c.metadata, score=0.0, source=source, rank=rank))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chain", action="store_true", help="打印首个查询的完整链路")
    args = parser.parse_args()

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
    builder = ContextBuilder(max_tokens=4000)
    tracer = Tracer(Path(settings.observability.trace_dir))

    samples = load_dataset(Path(settings.data.eval_dir) / "retrieval_eval.jsonl")
    questions = []
    for intent in ["explain", "compare", "architecture", "implementation"]:
        questions.extend([s for s in samples if s.intent.value == intent][:2])

    for idx, s in enumerate(questions):
        total_start = time.time()
        plan = analyze(s.question)

        t0 = time.time()
        vhits = vr.retrieve(plan.query)
        vector_ms = (time.time() - t0) * 1000
        t0 = time.time()
        bhits = br.retrieve(plan.query)
        bm25_ms = (time.time() - t0) * 1000
        t0 = time.time()
        rhits = retrieve_balanced(plan.query, plan.projects, vr, br, chunk_map, rrf_k=settings.indexing.fusion.rrf_k)
        rrf_ms = (time.time() - t0) * 1000
        retrieval_ms = vector_ms + bm25_ms + rrf_ms

        retrieved = [chunk_map[cid] for cid in rhits if cid in chunk_map]
        ctx = builder.build(retrieved, projects=plan.projects)

        t0 = time.time()
        result = generate(plan.query, plan.intent, ctx, model=settings.generation.model, temperature=settings.generation.temperature)
        generation_ms = (time.time() - t0) * 1000
        total_ms = (time.time() - total_start) * 1000

        trace = Trace(
            trace_id=uuid.uuid4().hex,
            query=plan.query,
            query_plan=plan,
            stages=[
                TraceStage(name="vector", elapsed_ms=vector_ms, results=_to_results(vhits, chunk_map, "vector")),
                TraceStage(name="bm25", elapsed_ms=bm25_ms, results=_to_results(bhits, chunk_map, "bm25")),
                TraceStage(name="rrf", elapsed_ms=rrf_ms, results=_ids_to_results(rhits, chunk_map, "rrf")),
            ],
            final_context=ctx.text,
            answer=Answer(answer=result.answer, citations=result.citations),
            retrieval_latency_ms=retrieval_ms,
            generation_latency_ms=generation_ms,
            total_latency_ms=total_ms,
            token_usage={"context_tokens": ctx.tokens, **result.usage},
        )
        tracer.save(trace)

        print(f"\n{'=' * 70}\n[{idx + 1}] 问题：{s.question}")
        print(f"意图：{plan.intent.value} · 项目：{plan.projects} · 检索 {retrieval_ms:.0f}ms · 生成 {generation_ms:.0f}ms · 总 {total_ms:.0f}ms")
        if args.chain and idx == 0:
            print("\n--- 向量候选 top5 ---")
            for r in trace.stages[0].results:
                print(f"  [{r.rank}] {r.metadata.project}:{r.metadata.source_path} ({r.score:.3f})")
            print("--- BM25 候选 top5 ---")
            for r in trace.stages[1].results:
                print(f"  [{r.rank}] {r.metadata.project}:{r.metadata.source_path} ({r.score:.3f})")
            print("--- RRF 候选 top8 ---")
            for r in trace.stages[2].results:
                print(f"  [{r.rank}] {r.metadata.project}:{r.metadata.source_path}")
            print(f"--- final_context（前 400 字符，共 {ctx.tokens} tok）---")
            print(ctx.text[:400])
        print(f"\n回答（前 300 字符）：\n{result.answer[:300]}")
        if result.sources_text:
            print(result.sources_text[:400])
        print(f"\n[trace] {trace.trace_id}")


if __name__ == "__main__":
    main()
