"""S1 语料采集入口。

用法：
    .venv/Scripts/python.exe scripts/ingest.py
"""

from app.core.logging import setup_logging
from app.ingestion.loader import ingest


def main() -> None:
    setup_logging()
    manifest = ingest()
    projects = manifest.get("projects", {})
    ok = {k: v for k, v in projects.items() if "commit_sha" in v}
    failed = {k: v for k, v in projects.items() if "commit_sha" not in v}
    total = sum(p.get("files_count", 0) for p in ok.values())
    print(f"\n采集完成：成功 {len(ok)} 个项目，共 {total} 个文档。")
    if failed:
        print(f"失败 {len(failed)} 个：{list(failed)}")


if __name__ == "__main__":
    main()
