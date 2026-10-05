from app.core.schemas import Intent
from app.query.analyzer import analyze


def test_detect_compare_and_projects():
    plan = analyze("Pi 和 Tau 的 Agent Loop 有什么区别？")
    assert plan.intent == Intent.COMPARE
    assert "pi" in plan.projects and "tau" in plan.projects


def test_detect_explain_single_project():
    plan = analyze("Pi 的 Context Compaction 是如何工作的？")
    assert plan.intent == Intent.EXPLAIN
    assert plan.projects == ["pi"]


def test_detect_implementation_no_project():
    plan = analyze("如果我要实现 Checkpoint，可以参考什么？")
    assert plan.intent == Intent.IMPLEMENTATION
    assert plan.projects == []


def test_word_boundary_no_false_positive():
    # "pipeline" 不应误判为 pi
    plan = analyze("OpenHands 的架构是什么？")
    assert plan.intent == Intent.ARCHITECTURE
    assert "openhands" in plan.projects
    assert "pi" not in plan.projects
