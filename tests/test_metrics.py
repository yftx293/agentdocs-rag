import pytest

from app.evaluation.retrieval_metrics import hit_at_k, mrr, recall_at_k, reciprocal_rank


def test_hit_at_k():
    assert hit_at_k(["a", "b", "c"], {"c"}, 3) == 1
    assert hit_at_k(["a", "b", "c"], {"d"}, 3) == 0
    assert hit_at_k(["a", "b", "c"], {"b"}, 1) == 0  # b 在 rank2，k=1 时不命中


def test_recall_at_k():
    assert recall_at_k(["a", "b", "c"], {"a", "d"}, 3) == 0.5
    assert recall_at_k(["a", "b", "c"], {"a", "b"}, 3) == 1.0
    assert recall_at_k(["a", "b", "c"], set(), 3) == 0.0


def test_reciprocal_rank():
    assert reciprocal_rank(["a", "b", "c"], {"c"}, 3) == pytest.approx(1 / 3)
    assert reciprocal_rank(["a"], {"a"}, 1) == 1.0
    assert reciprocal_rank(["a", "b"], {"z"}, 2) == 0.0


def test_mrr_hand_computed():
    ranked = [["a", "b"], ["x", "y"], ["p", "q"]]
    expected = [{"a"}, {"y"}, {"z"}]
    # 三个查询的 RR：1.0、0.5、0.0
    assert mrr(ranked, expected, 2) == pytest.approx((1.0 + 0.5 + 0.0) / 3)
