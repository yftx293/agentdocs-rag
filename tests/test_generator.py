from app.core.schemas import Citation
from app.generation.generator import render_sources


def test_render_sources_preserves_original_index():
    c3 = Citation(project="pi", source_path="docs/c.md", source_url="https://x/c", section="C", start_line=1, end_line=2)
    c1 = Citation(project="pi", source_path="docs/a.md", source_url="https://x/a", section="A", start_line=1, end_line=2)
    indexed = [(3, c3), (1, c1)]
    s = render_sources(indexed)
    assert "[3] pi / docs/c.md" in s
    assert "[1] pi / docs/a.md" in s
    assert "[2]" not in s  # 不应从 1 重新编号
