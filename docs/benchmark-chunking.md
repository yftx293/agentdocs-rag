# Chunk 策略 Benchmark（S6）

评测集：28 题（4 类 intent）

## 三策略对比（RRF）

| 策略 | chunks | hit@3 | hit@5 | mrr@5 |
|---|---|---|---|---|
| A: 300 tokens / 30 overlap | 3363 | 0.750 | 0.786 | 0.614 |
| B: 500 tokens / 50 overlap | 2753 | 0.750 | 0.821 | 0.588 |
| C: heading-only（不二次切分） | 2391 | 0.821 | 0.821 | 0.631 |

## A: 300 tokens / 30 overlap 分阶段指标
- vector: hit@5=0.786 mrr@5=0.620
- bm25: hit@5=0.714 mrr@5=0.535
- rrf: hit@5=0.786 mrr@5=0.614

## B: 500 tokens / 50 overlap 分阶段指标
- vector: hit@5=0.786 mrr@5=0.599
- bm25: hit@5=0.714 mrr@5=0.538
- rrf: hit@5=0.821 mrr@5=0.588

## C: heading-only（不二次切分） 分阶段指标
- vector: hit@5=0.786 mrr@5=0.612
- bm25: hit@5=0.714 mrr@5=0.517
- rrf: hit@5=0.821 mrr@5=0.631

## 结论与决策

**选定策略 C（heading-only）**，理由：

1. hit@3 最高（0.821，vs A/B 的 0.750）
2. mrr@5 最高（0.631，vs A 0.614 / B 0.588）——命中 chunk 排名更靠前
3. hit@5 并列最高（0.821）
4. chunks 最少（2391 vs A 3363 / B 2753）——更少存储与检索开销

**反直觉但合理的解释**：这批技术文档的 heading 边界天然语义自洽，硬切成 300/500 token 会把概念切碎、稀释上下文；保留整段 section 反而让检索命中更完整、排名更靠前。

**注意**：heading-only 下超长 section 会被 embedding 截断到 max_seq_length(8192)，这是已知限制（当前语料中占比极低，未影响整体结果）。

**已冻结**：`config/default.yaml` 的 `chunking.strategy=heading_only`、`heading_only=true`；生产数据已按此重跑（2391 chunks，RRF hit@5=0.821 / mrr@5=0.631）。
