"""S3 分块抽查工具：完整性检查 + 确定性抽样。

用法：
    .venv/Scripts/python.exe scripts/spotcheck.py [--n 30] [--seed 42] [--out docs/chunk-spotcheck-sample.md]
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from app.core.config import get_settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=str, default="docs/chunk-spotcheck-sample.md")
    args = parser.parse_args()

    settings = get_settings()
    chunks_path = Path(settings.data.processed_dir) / "chunks.jsonl"
    chunks = [json.loads(l) for l in chunks_path.read_text(encoding="utf-8").splitlines()]

    # 完整性：奇数个围栏符号 => 代码块被拆开
    bad_fence = [c for c in chunks if c["text"].count("```") % 2 == 1]
    bad_tilde = [c for c in chunks if c["text"].count("~~~") % 2 == 1]
    print(f"总 chunks: {len(chunks)}")
    print(f"代码块被拆开 (奇数 ```): {len(bad_fence)}")
    print(f"代码块被拆开 (奇数 ~~~): {len(bad_tilde)}")

    random.seed(args.seed)
    sample = random.sample(chunks, min(args.n, len(chunks)))
    lines = [
        "# Chunk 抽查样本（自动生成，供人工复核）",
        "",
        f"抽样 {len(sample)} / {len(chunks)} 个 chunk，seed={args.seed}",
        f"完整性：奇数 ``` 的 {len(bad_fence)} 个；奇数 ~~~ 的 {len(bad_tilde)} 个",
        "",
    ]
    for i, c in enumerate(sample, 1):
        m = c["metadata"]
        lines.append(
            f"### [{i}] {m['project']} · {m['source_path']}"
        )
        lines.append(
            f"- heading_path: `{m['heading_path']}` · 行 {c['start_line']}-{c['end_line']} · {c['token_count']} tok · id `{c['chunk_id'][:12]}`"
        )
        lines.append("")
        lines.append("```text")
        lines.append(c["text"][:400])
        lines.append("```")
        lines.append("")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"样本已写入 {out}")


if __name__ == "__main__":
    main()
