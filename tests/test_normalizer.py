from app.core.schemas import SourceType
from app.ingestion.normalizer import classify_source_type, extract_title, normalize, strip_frontmatter


def test_strip_frontmatter_and_title_from_frontmatter():
    text = '---\ntitle: "ADR 0001 — Use Textual"\n---\n\n# Fallback\n\nbody'
    normalized, title = normalize(text)
    assert normalized == "# Fallback\n\nbody"
    assert title == "ADR 0001 — Use Textual"


def test_title_falls_back_to_first_h1():
    _, title = normalize("# Compaction Reference\n\nbody")
    assert title == "Compaction Reference"


def test_normalize_unifies_newlines():
    text = "a\r\nb\rc"
    normalized, _ = normalize(text)
    assert "\r" not in normalized
    assert normalized == "a\nb\nc"


def test_strip_frontmatter_no_frontmatter_is_noop():
    body, meta = strip_frontmatter("# Title\nbody")
    assert body == "# Title\nbody"
    assert meta == {}


def test_extract_title_none_when_no_h1():
    assert extract_title("just a paragraph\nno heading") is None


def test_classify_source_type():
    assert classify_source_type("README.md") == SourceType.README
    assert classify_source_type("docs/usage.md") == SourceType.DOCS
    assert classify_source_type("specs/backend-management.md") == SourceType.DESIGN
    assert classify_source_type("dev-notes/adr/0001.md") == SourceType.DESIGN
