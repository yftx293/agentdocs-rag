"""S2 标准化 + 元数据 + 去重入口。

用法：
    .venv/Scripts/python.exe scripts/normalize.py
"""

from app.core.logging import setup_logging
from app.ingestion.pipeline import normalize_corpus


def main() -> None:
    setup_logging()
    report = normalize_corpus()
    print(
        f"\n标准化完成：总文件 {report['total_files']}，去重后 {report['unique_documents']} 篇，"
        f"去除重复 {report['duplicate_count']} 篇。"
    )


if __name__ == "__main__":
    main()
