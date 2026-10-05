# Chunk 策略 Benchmark（S6）

评测集：28 题（4 类 intent）

> 本节为 **section 级 golden** 的结果（封板修复 #2 后重跑）。文件级历史结果见文末。

## 三策略对比（RRF，section 级 golden）

| 策略 | chunks | hit@3 | hit@5 | mrr@5 |
|---|---|---|---|---|
| A: 300 tokens / 30 overlap | 3363 | 0.429 | 0.571 | 0.336 |
| B: 500 tokens / 50 overlap | 2753 | 0.429 | 0.571 | 0.314 |
| C: heading-only（不二次切分） | 2391 | 0.464 | 0.607 | 0.320 |

## 分阶段指标（section 级）

### A: 300 tokens / 30 overlap
- vector: hit@5=0.679 mrr@5=0.442
- bm25: hit@5=0.321 mrr@5=0.224
- rrf: hit@5=0.571 mrr@5=0.336

### B: 500 tokens / 50 overlap
- vector: hit@5=0.714 mrr@5=0.426
- bm25: hit@5=0.357 mrr@5=0.245
- rrf: hit@5=0.571 mrr@5=0.314

### C: heading-only（不二次切分）
- vector: hit@5=0.679 mrr@5=0.429
- bm25: hit@5=0.357 mrr@5=0.217
- rrf: hit@5=0.607 mrr@5=0.320

## 结论（section 级重验）

**heading-only（C）仍胜出**：hit@3（0.464）与 hit@5（0.607）均第一；A(300/30) 仅在 mrr@5 微弱领先（0.336 vs 0.320，差异 0.016，可视为噪声）。冻结决策不变。

**关键发现**：section 级下 BM25 大幅衰减（各策略 bm25 hit@5 仅 0.32~0.36），且 RRF（0.607）< 纯向量（0.679）——BM25 关键词匹配「文件准、section 不准」，section 级下融合反成负增益。→ V1 需调融合权重（降低 BM25）或引入 Reranker。

## 历史（文件级 golden，封板前）

| 策略 | chunks | hit@3 | hit@5 | mrr@5 |
|---|---|---|---|---|
| A: 300/30 | 3363 | 0.750 | 0.786 | 0.614 |
| B: 500/50 | 2753 | 0.750 | 0.821 | 0.588 |
| C: heading-only | 2391 | 0.821 | 0.821 | 0.631 |

> 文件级结论（C 胜出）与 section 级结论一致，但文件级数字系统性偏高（高估检索精度）。
