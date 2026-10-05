"""元数据提取：构建 DocumentMetadata + source_url + parent_id。"""

from __future__ import annotations

import hashlib

from app.core.schemas import DocumentMetadata
from app.ingestion.normalizer import classify_source_type


def make_source_url(repo: str, commit_sha: str, rel_path: str) -> str:
    """构造 commit 锚定的原始来源 URL。"""
    owner_repo = repo.rstrip("/").replace(".git", "").removeprefix("https://github.com/")
    return f"https://github.com/{owner_repo}/blob/{commit_sha}/{rel_path}"


def make_parent_id(project: str, rel_path: str) -> str:
    """文件级稳定 ID：{project}:{source_path}。"""
    return f"{project}:{rel_path}"


def build_metadata(
    project: str,
    repo: str,
    branch: str,
    commit_sha: str,
    rel_path: str,
    text: str,
    title: str | None,
) -> DocumentMetadata:
    """构建一个文件的完整元数据（PRD §8）。"""
    return DocumentMetadata(
        project=project,
        repo=repo,
        branch=branch,
        commit_sha=commit_sha,
        source_path=rel_path,
        source_url=make_source_url(repo, commit_sha, rel_path),
        heading_path=[title] if title else [],
        source_type=classify_source_type(rel_path),
        language="en",
        content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )
