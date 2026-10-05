"""一次性 migration 脚本：给 eval 集补 section 级 golden（expected_sections）。

⚠️ 红线例外：data/eval 是手写 golden 资产，常规 pipeline 脚本只读、禁止写回。
本脚本是「封板 migration」的一次性例外——在 V0 封板时手工执行一次，把 section 级
golden 写回 retrieval_eval.jsonl。已执行完毕，请勿再运行；后续改动应手工编辑
retrieval_eval.jsonl，不要复用本脚本写回。

用法（仅封板 migration 时执行一次，勿重复）：
    .venv/Scripts/python.exe scripts/annotate_sections.py
"""

from __future__ import annotations

import json
from pathlib import Path

from app.evaluation.dataset import load_dataset
from app.core.schemas import Chunk

# qid -> 期望的 section keys（project:path :: heading）
ANNOTATION: dict[str, list[str]] = {
    "q001": [
        "pi:packages/coding-agent/docs/compaction.md :: Compaction Reference > Overview",
        "pi:packages/coding-agent/docs/compaction.md :: Compaction Reference > Compaction > How It Works",
    ],
    "q002": [
        "pi:packages/coding-agent/docs/compaction.md :: Compaction Reference > Compaction > When It Triggers",
    ],
    "q003": [
        "pi:packages/coding-agent/docs/compaction.md :: Compaction Reference > Branch Summarization",
        "pi:packages/coding-agent/docs/compaction.md :: Compaction Reference > Branch Summarization > How It Works",
        "pi:packages/coding-agent/docs/compaction.md :: Compaction Reference > Branch Summarization > When It Triggers",
    ],
    "q004": ["pi:packages/coding-agent/docs/how-pi-works.md :: How Pi Works > Agent loop"],
    "q005": ["tau:dev-notes/architecture/phase-3-agent-loop.md :: Why the loop mutates the transcript"],
    "q006": ["tau:dev-notes/architecture/phase-7-session-tree.md :: Why sessions are append-only"],
    "q007": [
        "langgraph:libs/checkpoint/README.md :: LangGraph Checkpoint > 🤔 What is this?",
        "langgraph:libs/checkpoint/README.md :: LangGraph Checkpoint > Key concepts > Checkpoint",
    ],
    "q008": ["mini-swe-agent:docs/advanced/control_flow.md :: Agent control flow"],
    "q009": ["mini-swe-agent:docs/advanced/environments.md :: Environment classes"],
    "q010": ["pi:packages/coding-agent/docs/extensions.md :: Extensions > Create and load an extension"],
    "q011": [
        "pi:packages/coding-agent/docs/how-pi-works.md :: How Pi Works > Agent loop",
        "tau:dev-notes/design/agent-loop.md :: Minimal shape",
    ],
    "q012": [
        "pi:packages/coding-agent/docs/compaction.md :: Compaction Reference > Overview",
        "pi:packages/coding-agent/docs/compaction.md :: Compaction Reference > Compaction > How It Works",
        "tau:dev-notes/architecture/phase-22-compaction-foundation.md :: Context Size Estimation",
        "tau:dev-notes/architecture/phase-22-compaction-foundation.md :: Manual Compaction",
    ],
    "q013": [
        "tau:dev-notes/architecture/phase-7-session-tree.md :: Entry types",
        "tau:dev-notes/architecture/phase-7-session-tree.md :: Why sessions are append-only",
        "langgraph:libs/checkpoint/README.md :: LangGraph Checkpoint > Key concepts > Checkpoint",
        "langgraph:libs/checkpoint/README.md :: LangGraph Checkpoint > Key concepts > Thread",
    ],
    "q014": [
        "pi:packages/coding-agent/docs/mcp.md :: MCP Servers > Configure servers",
        "pi:packages/coding-agent/docs/mcp.md :: MCP Servers > Control tool exposure",
        "openhands:specs/mcp-settings.md :: MCP Settings Specs > MCP-001: Sparse mutations preserve sibling servers",
        "openhands:specs/mcp-settings.md :: MCP Settings Specs > MCP-002: Secret patches preserve user intent",
        "openhands:specs/mcp-settings.md :: MCP Settings Specs > MCP-003: Settings map keys are stable MCP identities",
    ],
    "q015": [
        "pi:packages/coding-agent/docs/providers.md :: Providers > Authenticate interactively",
        "pi:packages/coding-agent/docs/providers.md :: Providers > Use an API key from the environment",
        "tau:dev-notes/architecture/config-driven-provider-catalog.md :: Catalog shape",
        "tau:dev-notes/architecture/config-driven-provider-catalog.md :: Overlay behavior",
    ],
    "q016": [
        "tau:dev-notes/design/agent-loop.md :: Minimal shape",
        "tau:dev-notes/architecture/phase-3-agent-loop.md :: The loop's inputs",
        "tau:dev-notes/architecture/phase-3-agent-loop.md :: Basic text-only flow",
    ],
    "q017": [
        "openhands:docs/architecture.md :: Agent Canvas architecture > System boundaries",
        "openhands:docs/architecture.md :: Agent Canvas architecture > Runtime services",
        "openhands:docs/architecture.md :: Agent Canvas architecture > Frontend modules",
    ],
    "q018": [
        "openhands:specs/workspace-upload-path.md :: Workspace Upload Path Specs > WUP-001: Relative working dirs are resolved against `/api/file/home`, not the filesystem root",
    ],
    "q019": [
        "tau:dev-notes/architecture/config-driven-provider-catalog.md :: Architecture boundary",
        "tau:dev-notes/architecture/config-driven-provider-catalog.md :: Catalog shape",
    ],
    "q020": ["tau:dev-notes/architecture/phase-7-session-tree.md :: Entry types"],
    "q021": ["pi:packages/coding-agent/docs/mcp.md :: MCP Servers > Control tool exposure"],
    "q022": ["tau:dev-notes/architecture/phase-3-agent-loop.md :: The loop's inputs"],
    "q023": [
        "langgraph:libs/checkpoint/README.md :: LangGraph Checkpoint > Key concepts > Checkpoint",
        "langgraph:libs/checkpoint/README.md :: LangGraph Checkpoint > Key concepts > Thread",
        "langgraph:libs/checkpoint/README.md :: LangGraph Checkpoint > Interface",
    ],
    "q024": [
        "tau:dev-notes/architecture/phase-22-compaction-foundation.md :: What was added",
        "tau:dev-notes/architecture/phase-22-compaction-foundation.md :: Context Size Estimation",
        "tau:dev-notes/architecture/phase-22-compaction-foundation.md :: Manual Compaction",
    ],
    "q025": [
        "tau:dev-notes/architecture/phase-7-session-tree.md :: Entry types",
        "tau:dev-notes/architecture/phase-7-session-tree.md :: Replay",
        "tau:dev-notes/architecture/phase-7-session-tree.md :: Tree paths",
    ],
    "q026": [
        "tau:dev-notes/architecture/config-driven-provider-catalog.md :: Catalog shape",
        "tau:dev-notes/architecture/config-driven-provider-catalog.md :: Overlay behavior",
        "tau:dev-notes/architecture/config-driven-provider-catalog.md :: Validation",
    ],
    "q027": [
        "pi:packages/coding-agent/docs/extensions.md :: Extensions > Follow the extension contracts",
        "pi:packages/coding-agent/docs/extensions.md :: Extensions > Follow the extension contracts > Tools",
        "pi:packages/coding-agent/docs/extensions.md :: Extensions > Follow the extension contracts > Tool exposure",
    ],
    "q028": ["mini-swe-agent:docs/advanced/environments.md :: Environment classes"],
}


def main() -> None:
    path = Path("data/eval/retrieval_eval.jsonl")
    samples = load_dataset(path)

    chunks = [Chunk.model_validate_json(l) for l in Path("data/processed/chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    chunk_sections = set()
    for c in chunks:
        heading = " > ".join(c.metadata.heading_path) if c.metadata.heading_path else ""
        chunk_sections.add(f"{c.metadata.project}:{c.metadata.source_path} :: {heading}")

    # 校验标注：每个 section key 必须真实存在
    missing = []
    for qid, secs in ANNOTATION.items():
        for sec in secs:
            if sec not in chunk_sections:
                missing.append((qid, sec))
    if missing:
        print("标注校验失败，以下 section 不存在：")
        for qid, sec in missing:
            print(f"  {qid}: {sec}")
        raise SystemExit(1)

    # 写回
    out = []
    for s in samples:
        d = json.loads(s.model_dump_json())
        d["expected_sections"] = ANNOTATION.get(s.id, [])
        out.append(d)

    lines = [json.dumps(d, ensure_ascii=False) for d in out]
    # 保持原顺序
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已更新 {len(out)} 题，其中 {sum(1 for d in out if d['expected_sections'])} 题带 section 级 golden")


if __name__ == "__main__":
    main()
