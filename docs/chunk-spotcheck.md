# Chunk 抽查报告（S3 人工复核）

- 日期：2026-10
- 抽样：30 / 2753 chunk（seed=42，确定性），完整样本见 `chunk-spotcheck-sample.md`

## 结论：✅ 通过

核心结构不变量全部成立：**未发现代码块/表格被拆散、heading_path 缺失、chunk_id 不稳定、孤儿 chunk**。发现 3 个「待优化」问题，均不影响 V0 结构正确性，归入 S6 调优处理。

## 完整性自动检查（全量 2753 chunk）

| 检查项 | 结果 |
|---|---|
| 代码块被拆开（奇数 ```` ``` ````） | 0 |
| 代码块被拆开（奇数 `~~~`） | 0 |
| chunk_id 唯一 | ✅ 是 |
| 孤儿 chunk（parent_id 不存在） | 0 |
| chunk token 分布 | p50=151 / p90=457 / max=2969（88 个 >500，均为超大原子块） |

## 人工复核要点

**正确的部分：**
- `heading_path` 完整且多级（如 `['RPC Commands', 'Thinking']`、`['Agent Canvas architecture', 'Quality gates']`）。
- 代码块完整（python/json/typescript/bash/bibtex 均带完整围栏）。
- 表格完整（如 pi `windows.md` 的 Environment 表）。
- `chunk_id` 稳定、`start_line/end_line` 可追溯到原文件行号。
- 标题注入生效（`Project: pi` + `Section: ...` 进入 embedding_text）。

## 待优化问题（归入 S6）

### A. 标题-only Section 产生空 chunk
`pi/rpc-commands.md` 的 `## Thinking` 下面直接跟下一个标题，产生 2-token 的空 chunk。
- 影响：低价值噪声，不破坏正确性。
- S6 处理：合并/丢弃「无正文的标题 section」。

### B. 列表项被句子切分，续接 chunk 丢列表前缀
- `mini-swe-agent/AGENTS.md` 的编号列表因「1. 后跟空行」被段落切分拆散（`1.` 与正文分离）。
- `pi/mcp.md` 的 `- description: ...in a sentence.` 被句子切分后，`It lists...` 落入下一 chunk，丢失 `description` 前缀。
- 影响：续接 chunk 的独立可读性略降，内容未丢失。
- S6/S7 处理：列表感知切分，或列表项作为原子 piece。

### C. 语料含低价值「meta」内容
部分 README/AGENTS 含贡献指南、CI quality gates、致谢/引用块（如 mini-swe-agent README 的 bibtex、openhands 的 Quality gates）。
- 影响：占用检索噪声，非 chunking 问题，属语料策展。
- 后续处理：S4 建评测集时回避；或 V1 增加内容过滤。

## 结论

S3 的 Markdown-aware Parent/Child 分块结构正确、可复现、可追溯。三个待优化项均为「检索质量调优」范畴，按 PRD 原则五放到 S6 用 benchmark 数据决定，不在 S3 主观改动。
