"""按 Intent 的 Prompt 模板（PRD §19）。"""

from __future__ import annotations

from app.core.schemas import Intent

COMMON_SYSTEM = """你是一个面向 AI Agent / Coding Agent 技术文档的问答助手。
只根据下方提供的上下文片段回答，不得使用外部知识或编造。
每个片段以 [编号] [项目 | 文件路径 | 章节 | 行号] 开头。
引用时在句中标注对应编号，如 [1]、[2]。
如果上下文无法回答，请明确说明「上下文不足」，不要猜测。
用与问题相同的语言回答。"""

INTENT_INSTRUCTIONS: dict[Intent, str] = {
    Intent.EXPLAIN: "请解释概念、工作流程与关键实现，并在结尾列出用到的来源编号。",
    Intent.COMPARE: "请对比两者的共同点、差异、各自实现方式与设计取舍，确保两方都被充分覆盖，并列出来源编号作为证据。",
    Intent.ARCHITECTURE: "请描述模块组成、数据流、状态流、边界与依赖关系，并列出来源编号。",
    Intent.IMPLEMENTATION: "请说明可借鉴的具体设计、对应的项目、实现位置与注意事项，并列出来源编号。",
}


def build_user_prompt(question: str, intent: Intent, numbered_context: str) -> str:
    instr = INTENT_INSTRUCTIONS.get(intent, INTENT_INSTRUCTIONS[Intent.EXPLAIN])
    return f"问题：{question}\n\n{instr}\n\n上下文：\n{numbered_context}"
