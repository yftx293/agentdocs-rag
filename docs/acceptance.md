# V0 验收清单（PRD §27）

> 逐条对照 PRD §27 的 V0 验收标准，标注证据与状态。

## 数据
| 验收项 | 状态 | 证据 |
|---|---|---|
| 至少接入 5 个 Agent/Coding Agent 项目 | ✅ | pi(75) / tau(158) / mini-swe-agent(58) / openhands(15) / langgraph(12) |
| Raw 与 Processed 数据分离 | ✅ | `data/raw/`（不可变）+ `data/processed/`（可重建） |
| 每个 Chunk 有稳定 `chunk_id` 与 `parent_id` | ✅ | chunk_id=sha1(parent_id+text)，content 哈希稳定 |
| 每个 Chunk 能追溯项目/路径/章节/URL | ✅ | metadata 含 project/source_path/source_url/heading_path，source_url commit 锚定 |

## Chunk
| 验收项 | 状态 | 证据 |
|---|---|---|
| Markdown Heading-aware | ✅ | heading_path 完整多级追踪 |
| 默认保护 Code Fence 与 Table | ✅ | 全量 2753 chunk 代码块被拆开=0（含嵌套围栏修复） |
| Parent/Child 关系有效 | ✅ | S6 冻结 heading-only 后 chunk=section=parent（无 child 冗余） |
| 能人工抽查 Chunk | ✅ | `docs/chunk-spotcheck.md`（30 chunk 抽查 + 3 待优化项） |

## Retrieval
| 验收项 | 状态 | 证据 |
|---|---|---|
| Vector Search 可用 | ✅ | BGE-M3@GPU，vector-only hit@5=0.786 |
| BM25 可用 | ✅ | bm25s+jieba，bm25-only hit@5=0.714 |
| RRF 可用 | ✅ | RRF 融合 hit@5=0.821 超单路 |
| 能打印各阶段候选结果 | ✅ | `scripts/ask.py --chain` 打印 vector/bm25/rrf top-K |

## Generation
| 验收项 | 状态 | 证据 |
|---|---|---|
| 能基于最终 Context 回答 | ✅ | ContextBuilder + 4 intent Prompt + DeepSeek |
| 回答包含 Citation | ✅ | 8 题共 55 条引用，全部可回溯 URL+行号 |
| Compare Query 覆盖至少两个指定项目 | ✅ | Pi/Tau Agent Loop 答案同时引用 pi+tau |

## Evaluation
| 验收项 | 状态 | 证据 |
|---|---|---|
| 有独立 Eval Dataset | ✅ | `data/eval/retrieval_eval.jsonl` 28 题（4 intent） |
| 能计算 Hit@K、Recall@K、MRR | ✅ | `retrieval_metrics.py` + 手算单测 |
| 至少一次 Chunk Strategy 对比实验 | ✅ | S6：A(300/30)/B(500/50)/C(heading-only) 对比，C 胜出 |

## Observability
| 验收项 | 状态 | 证据 |
|---|---|---|
| 一次 Query 能看到 Question→Candidates→Context→Answer 并记录耗时 | ✅ | `traces/traces.jsonl`（8 条 trace，含各阶段耗时/token）；`ask.py --chain` 打印全链路 |

## 总体结论
**V0 全部验收项通过。** 检索基线 RRF hit@5=0.821 / mrr@5=0.631（BGE-M3@GPU，heading-only 分块）。
失败归因（`docs/failure-analysis.md`）：28 题中 4 题检索未命中（0 数据缺失），指向 V1 检索优化（Reranker/Query Analysis/Metadata Filter）。
