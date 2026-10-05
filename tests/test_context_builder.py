from app.context.builder import ContextBuilder
from app.core.schemas import Chunk, DocumentMetadata


def _chunk(chunk_id: str, project: str, source_path: str, text: str,
           heading_path: list[str] | None = None) -> Chunk:
    meta = DocumentMetadata(
        project=project,
        repo=f"https://github.com/{project}/x",
        commit_sha="abc",
        source_path=source_path,
        source_url=f"https://github.com/{project}/x/blob/abc/{source_path}",
        heading_path=heading_path or [],
    )
    return Chunk(
        chunk_id=chunk_id,
        parent_id=f"{project}:{source_path}",
        text=text,
        embedding_text=text,
        metadata=meta,
        start_line=1,
        end_line=10,
    )


def test_dedup_by_chunk_id():
    a = _chunk("id1", "pi", "docs/a.md", "content A")
    b = _chunk("id1", "pi", "docs/a.md", "content A")  # 重复 chunk_id
    c = _chunk("id2", "pi", "docs/b.md", "content B")
    r = ContextBuilder(max_tokens=10000).build([a, b, c])
    assert len(r.chunks) == 2


def test_token_budget_respected():
    chunks = [_chunk(f"id{i}", "pi", f"docs/{i}.md", "x" * 1000) for i in range(20)]
    r = ContextBuilder(max_tokens=3000).build(chunks)
    assert r.tokens <= 3000 + 1000  # 整 chunk 不截断，允许最后一个超出
    assert len(r.chunks) < 20


def test_project_balance_round_robin():
    pi = [_chunk(f"pi{i}", "pi", f"docs/p{i}.md", "pi content") for i in range(3)]
    tau = [_chunk(f"tau{i}", "tau", f"dev-notes/t{i}.md", "tau content") for i in range(3)]
    r = ContextBuilder(max_tokens=100000).build(pi + tau, projects=["pi", "tau"])
    # round-robin 后首两个 chunk 应分属不同项目
    assert r.chunks[0].metadata.project != r.chunks[1].metadata.project
    assert set(r.project_distribution.keys()) == {"pi", "tau"}
    assert r.project_distribution["pi"] == 3 and r.project_distribution["tau"] == 3


def test_citation_preserved():
    c = _chunk("id1", "pi", "docs/compaction.md", "body", heading_path=["Compaction"])
    r = ContextBuilder(max_tokens=10000).build([c])
    assert len(r.citations) == 1
    assert r.citations[0]["source_url"].startswith("https://github.com/pi")
    assert r.citations[0]["section"] == "Compaction"
    assert "docs/compaction.md" in r.text


def test_single_chunk_over_budget_still_included():
    huge = _chunk("big", "pi", "docs/huge.md", "y" * 8000)  # 超预算的单 chunk
    r = ContextBuilder(max_tokens=1000).build([huge])
    assert len(r.chunks) == 1  # 不截断，保护内容完整


def test_retrieve_balanced_represents_both_projects_and_caps():
    from app.retrieval.balanced import retrieve_balanced

    class _Fake:
        def __init__(self, hits):
            self.hits = hits

        def retrieve(self, q):
            return self.hits

    vr = _Fake([("pi1", 1.0)])
    br = _Fake([("t1", 1.0), ("t2", 0.9), ("t3", 0.8)])
    cm = {
        "pi1": _chunk("pi1", "pi", "p1.md", "x"),
        "t1": _chunk("t1", "tau", "t1.md", "x"),
        "t2": _chunk("t2", "tau", "t2.md", "x"),
        "t3": _chunk("t3", "tau", "t3.md", "x"),
    }
    result = retrieve_balanced("q", ["pi", "tau"], vr, br, cm, per_project_n=2)
    projects = [cm[cid].metadata.project for cid in result]
    assert "pi" in projects and "tau" in projects
    assert projects.count("tau") == 2  # tau 被 cap 到 2
    assert projects.count("pi") == 1
    assert projects[0] != projects[1]  # round-robin 交错
