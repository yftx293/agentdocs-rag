"""S2 编排：raw + manifest → documents.jsonl + dedup_report.json。"""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.schemas import Chunk, Document
from app.ingestion.dedup import deduplicate
from app.ingestion.metadata import build_metadata, make_parent_id
from app.ingestion.normalizer import normalize
from app.ingestion.splitter import chunk_document

log = get_logger(__name__)


def _read_text(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def normalize_corpus() -> dict:
    """把 data/raw 的语料标准化为 documents.jsonl，返回统计报告。"""
    settings = get_settings()
    raw_root = Path(settings.data.raw_dir)
    processed_root = Path(settings.data.processed_dir)
    processed_root.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((raw_root / "manifest.json").read_text(encoding="utf-8"))
    projects = manifest.get("projects", {})

    documents: list[Document] = []
    for project, info in projects.items():
        if "commit_sha" not in info:
            log.warning("跳过 %s（采集失败）", project)
            continue
        project_dir = raw_root / project
        files = sorted(
            p
            for p in project_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in (".md", ".mdx")
        )
        for f in files:
            rel = str(f.relative_to(project_dir)).replace("\\", "/")
            text, title = normalize(_read_text(f))
            meta = build_metadata(
                project=project,
                repo=info["repo"],
                branch=info.get("branch", "main"),
                commit_sha=info["commit_sha"],
                rel_path=rel,
                text=text,
                title=title,
            )
            documents.append(Document(parent_id=make_parent_id(project, rel), text=text, metadata=meta))

    kept, removed = deduplicate(documents)

    with open(processed_root / "documents.jsonl", "w", encoding="utf-8") as out:
        for d in kept:
            out.write(d.model_dump_json() + "\n")

    report = {
        "total_files": len(documents),
        "unique_documents": len(kept),
        "duplicate_count": len(removed),
        "duplicates": removed,
    }
    (processed_root / "dedup_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info("documents.jsonl：%d 篇（去重前 %d，去除重复 %d）", len(kept), len(documents), len(removed))
    return report


def chunk_corpus() -> dict:
    """把 documents.jsonl 分块为 parents.jsonl + chunks.jsonl，返回统计。"""
    settings = get_settings()
    processed = Path(settings.data.processed_dir)
    docs_path = processed / "documents.jsonl"
    docs = [Document.model_validate_json(line) for line in docs_path.read_text(encoding="utf-8").splitlines()]

    c = settings.chunking
    parents_all: list[Document] = []
    chunks_all: list[Chunk] = []
    for doc in docs:
        parents, chunks = chunk_document(doc, c.parent_max_tokens, c.child_max_tokens, c.overlap_tokens, heading_only=c.heading_only)
        parents_all.extend(parents)
        chunks_all.extend(chunks)

    with open(processed / "parents.jsonl", "w", encoding="utf-8") as f:
        for p in parents_all:
            f.write(p.model_dump_json() + "\n")
    with open(processed / "chunks.jsonl", "w", encoding="utf-8") as f:
        for ch in chunks_all:
            f.write(ch.model_dump_json() + "\n")

    log.info("分块完成：%d 文档 → %d parents → %d chunks", len(docs), len(parents_all), len(chunks_all))
    return {"documents": len(docs), "parents": len(parents_all), "chunks": len(chunks_all)}
