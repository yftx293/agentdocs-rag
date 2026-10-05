from app.core.schemas import Document, DocumentMetadata
from app.ingestion.splitter import chunk_document


def _doc(text: str) -> Document:
    meta = DocumentMetadata(
        project="pi",
        repo="https://github.com/earendil-works/pi",
        branch="main",
        commit_sha="abc",
        source_path="docs/x.md",
        source_url="https://github.com/earendil-works/pi/blob/abc/docs/x.md",
    )
    return Document(parent_id="pi:docs/x.md", text=text, metadata=meta)


def test_code_fence_never_split():
    code = "```python\n" + "x = 1\n" * 300 + "```"
    text = "# H\n\n" + code
    _, chunks = chunk_document(_doc(text), 4000, 500, 50)
    # 代码块完整出现在某个 chunk 中，且不被切开
    assert any(c.text.count("x = 1") == 300 for c in chunks)


def test_table_kept_whole():
    n = 200
    rows = "\n".join(f"| r{i} | v{i} |" for i in range(n))
    table = "| col1 | col2 |\n|---|---|\n" + rows
    _, chunks = chunk_document(_doc("# H\n\n" + table), 4000, 500, 50)
    header_chunks = [c for c in chunks if "|---|---|" in c.text]
    assert len(header_chunks) == 1, "表头应只在一个 chunk 中"
    assert f"r{n - 1}" in header_chunks[0].text, "表格最后一行应与表头在同一 chunk（未被拆散）"


def test_heading_path_propagates():
    text = "# Architecture\n\nintro\n\n## Context\n\ncompression details."
    _, chunks = chunk_document(_doc(text), 4000, 500, 50)
    assert any(c.metadata.heading_path == ["Architecture", "Context"] for c in chunks)


def test_every_chunk_parent_exists():
    text = "# A\n\np1\n\n## B\n\np2\n\n## C\n\np3\n\n# D\n\np4"
    parents, chunks = chunk_document(_doc(text), 4000, 500, 50)
    parent_ids = {p.parent_id for p in parents}
    for c in chunks:
        assert c.parent_id in parent_ids


def test_chunk_id_deterministic():
    text = "# T\n\nsome content here for stable chunking"
    _, c1 = chunk_document(_doc(text), 4000, 500, 50)
    _, c2 = chunk_document(_doc(text), 4000, 500, 50)
    assert [c.chunk_id for c in c1] == [c.chunk_id for c in c2]


def test_duplicate_heading_gets_distinct_parent_ids():
    text = "# Same\n\na\n\n# Same\n\nb"
    parents, _ = chunk_document(_doc(text), 4000, 500, 50)
    ids = [p.parent_id for p in parents if p.metadata.heading_path == ["Same"]]
    assert len(ids) == 2
    assert ids[0] != ids[1]


def test_embedding_text_has_title_injection():
    text = "# Compaction\n\nsome text about compaction"
    _, chunks = chunk_document(_doc(text), 4000, 500, 50)
    c = [x for x in chunks if x.metadata.heading_path == ["Compaction"]][0]
    assert "Project: pi" in c.embedding_text
    assert "Section: Compaction" in c.embedding_text
    assert c.embedding_text != c.text


def test_nested_fence_not_split():
    # 4 空格缩进的外层代码块，内部含 8 空格缩进的纯 ``` 行，不应被误判为闭合
    text = (
        "??? example\n\n"
        "    ```yaml\n"
        "    model:\n"
        "      action_regex: ```mswea_bash_command\\s*\\n(.*?)\\n```\n"
        "    agent:\n"
        "      system_template: |\n"
        "        ```mswea_bash_command\n"
        "        your_command_here\n"
        "        ```\n"
        "    ```\n"
    )
    _, chunks = chunk_document(_doc(text), 4000, 500, 50)
    assert any("action_regex" in c.text and "your_command_here" in c.text for c in chunks)


def test_heading_only_one_chunk_per_section():
    text = "# A\n\np1\n\n## B\n\np2\n\np3"
    _, chunks = chunk_document(_doc(text), 2000, 500, 50, heading_only=True)
    assert len(chunks) == 2  # 两个 section 各一个 chunk
    assert any("A" in c.text and "p1" in c.text for c in chunks)
    assert any("B" in c.text and "p2" in c.text for c in chunks)
