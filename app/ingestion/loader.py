"""语料采集 Loader（确定性、只读、可重跑）。

从 GitHub 下载指定 commit 的 tarball（codeload），仅抽取技术文档
（README / AGENTS / docs / specs / dev-notes 等，按每项目 include/exclude 规则），
写入 data/raw/<project>/，并生成 manifest.json 记录 commit_sha 以保证可复现。

红线遵守：
- data/raw 只落盘目标文档，源码只在临时目录中过滤后即销毁，绝不进 raw。
- 串行单连接下载，项目间节流，不做并发爬取。
- 相同 commit_sha 时幂等跳过，重跑零改动。
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)

_USER_AGENT = "agentdocs-rag/0.1"


def _git_ls_remote(repo: str, proxy: str | None) -> str:
    """获取默认分支 HEAD 的 commit SHA。"""
    cmd = ["git"]
    if proxy:
        cmd += ["-c", f"http.proxy={proxy}", "-c", f"https.proxy={proxy}"]
    cmd += ["ls-remote", repo, "HEAD"]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
    if not out.stdout.strip():
        raise RuntimeError(f"git ls-remote 无输出: {repo}")
    return out.stdout.split()[0]


def _download(repo: str, sha: str, proxy: str | None, dest: Path) -> None:
    """下载 codeload tarball 到 dest。"""
    owner_repo = repo.rstrip("/").replace(".git", "").removeprefix("https://github.com/")
    url = f"https://codeload.github.com/{owner_repo}/tar.gz/{sha}"
    handlers = [urllib.request.ProxyHandler({"http": proxy, "https": proxy})] if proxy else []
    opener = urllib.request.build_opener(*handlers)
    opener.addheaders = [("User-Agent", _USER_AGENT)]
    log.info("  下载 %s", url)
    with opener.open(url, timeout=180) as resp, open(dest, "wb") as f:
        shutil.copyfileobj(resp, f)


_GLOB_CACHE: dict[str, re.Pattern] = {}


def _glob_to_regex(pattern: str) -> re.Pattern:
    """glob → 锚定正则：`*` 不跨目录，`**` 跨目录，`?` 单字符（不含 /）。"""
    if pattern in _GLOB_CACHE:
        return _GLOB_CACHE[pattern]
    out: list[str] = []
    i, n = 0, len(pattern)
    while i < n:
        c = pattern[i]
        if c == "*":
            if i + 1 < n and pattern[i + 1] == "*":
                i += 2
                if i < n and pattern[i] == "/":
                    out.append(r"(?:.*/)?")
                    i += 1
                else:
                    out.append(r".*")
                continue
            out.append(r"[^/]*")
            i += 1
        elif c == "?":
            out.append(r"[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    regex = re.compile("^" + "".join(out) + "$")
    _GLOB_CACHE[pattern] = regex
    return regex


def _matches(rel_path: str, patterns: list[str]) -> bool:
    return any(_glob_to_regex(pat).match(rel_path) for pat in patterns)


def _extract_docs(archive: Path, dest: Path, include: list[str], exclude: list[str]) -> list[str]:
    """从 tarball 抽取匹配的 .md/.mdx 文档，返回仓库内相对路径列表。"""
    extracted: list[str] = []
    dest_resolved = dest.resolve()
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            parts = PurePosixPath(member.name).parts
            if len(parts) < 2:
                continue
            rel = str(PurePosixPath(*parts[1:]))
            if not rel.lower().endswith((".md", ".mdx")):
                continue
            if not (_matches(rel, include) and not _matches(rel, exclude)):
                continue
            target = (dest / rel).resolve()
            if not str(target).startswith(str(dest_resolved)):
                raise ValueError(f"路径越界，拒绝写入: {member.name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(member) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)  # type: ignore[arg-type]
            extracted.append(rel)
    return sorted(extracted)


def ingest() -> dict:
    """采集全部项目语料，返回 manifest dict。"""
    settings = get_settings()
    raw_root = Path(settings.data.raw_dir)
    raw_root.mkdir(parents=True, exist_ok=True)
    proxy = settings.network.proxy

    manifest_path = raw_root / "manifest.json"
    old_manifest: dict = {}
    if manifest_path.exists():
        old_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    new_manifest: dict = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "proxy": proxy,
        "projects": {},
    }

    for name, proj in settings.corpus.projects.items():
        log.info("== 项目 %s (%s) ==", name, proj.repo)
        try:
            sha = _git_ls_remote(proj.repo, proxy)
            old = (old_manifest.get("projects") or {}).get(name) or {}
            if old.get("commit_sha") == sha and old.get("files"):
                log.info("  commit 未变(%s)，跳过", sha[:8])
                new_manifest["projects"][name] = old
                continue

            dest = raw_root / name
            if dest.exists():
                backup = raw_root / ".bak" / f"{name}-{str(old.get('commit_sha', 'unknown'))[:8]}"
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dest), str(backup))
                log.info("  commit 变化，旧语料备份到 %s", backup)

            with tempfile.TemporaryDirectory() as tmp:
                archive = Path(tmp) / f"{name}.tar.gz"
                _download(proj.repo, sha, proxy, archive)
                files = _extract_docs(archive, dest, proj.include, proj.exclude)

            new_manifest["projects"][name] = {
                "repo": proj.repo,
                "branch": proj.branch,
                "commit_sha": sha,
                "files_count": len(files),
                "files": files,
            }
            log.info("  完成：%d 个文档", len(files))
            time.sleep(1)  # 串行节流，避免高频抓取
        except Exception as e:  # noqa: BLE001
            log.error("  %s 失败: %s", name, e)
            new_manifest["projects"][name] = {"repo": proj.repo, "error": str(e)}

    manifest_path.write_text(
        json.dumps(new_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return new_manifest
