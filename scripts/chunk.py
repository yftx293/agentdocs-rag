"""S3 Markdown-aware 分块入口。

用法：
    uv run python scripts/chunk.py
"""

from app.core.logging import setup_logging
from app.ingestion.pipeline import chunk_corpus


def main() -> None:
    setup_logging()
    stats = chunk_corpus()
    print(f"\n分块完成：{stats['documents']} 文档 → {stats['parents']} parents → {stats['chunks']} chunks。")


if __name__ == "__main__":
    main()
