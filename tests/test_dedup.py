from app.core.schemas import Document, DocumentMetadata
from app.ingestion.dedup import deduplicate


def _make(parent_id: str, text: str, content_hash: str) -> Document:
    meta = DocumentMetadata(
        project="pi",
        repo="https://github.com/earendil-works/pi",
        commit_sha="abc123",
        source_path=parent_id.split(":", 1)[1],
        source_url=f"https://u/{parent_id.split(':', 1)[1]}",
        content_hash=content_hash,
    )
    return Document(parent_id=parent_id, text=text, metadata=meta)


def test_duplicate_content_collapses_to_one():
    d1 = _make("pi:docs/a.md", "same", "H1")
    d2 = _make("pi:docs/b.md", "same", "H1")
    kept, removed = deduplicate([d1, d2])
    assert len(kept) == 1
    assert len(removed) == 1
    assert removed[0]["kept_parent_id"] == "pi:docs/a.md"
    assert removed[0]["removed_parent_id"] == "pi:docs/b.md"


def test_distinct_content_both_kept():
    d1 = _make("pi:docs/a.md", "A", "HA")
    d2 = _make("pi:docs/b.md", "B", "HB")
    kept, removed = deduplicate([d1, d2])
    assert len(kept) == 2
    assert removed == []


def test_first_occurrence_wins_deterministically():
    docs = [_make(f"pi:docs/{c}.md", "x", "SAME") for c in "xyz"]
    kept, _ = deduplicate(docs)
    assert [d.parent_id for d in kept] == ["pi:docs/x.md"]
