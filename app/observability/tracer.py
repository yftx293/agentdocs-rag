"""Tracer：把一次 Query 的完整链路写入 JSONL（PRD §23）。"""

from __future__ import annotations

from pathlib import Path

from app.core.schemas import Trace


class Tracer:
    def __init__(self, trace_dir: Path):
        self.trace_dir = Path(trace_dir)
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.trace_dir / "traces.jsonl"

    def save(self, trace: Trace) -> Path:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(trace.model_dump_json() + "\n")
        return self.path
