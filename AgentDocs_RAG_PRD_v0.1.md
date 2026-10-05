# AgentDocs RAG — 初版 PRD

> 文档状态：Draft v0.1  
> 项目定位：面向 AI Agent / Coding Agent 技术资料的检索、解释与跨项目比较系统  
> 建议仓库位置：`docs/PRD.md`

---

## 1. 背景

当前 AI Agent / Coding Agent 生态中的技术资料高度分散，常见来源包括：

- GitHub README
- `docs/` 技术文档
- 架构说明与设计文档
- 官方博客与技术报告
- Issue / Discussion 中的重要设计讨论
- 部分与实现强相关的源码说明

当需要回答诸如：

- Pi 如何做 Context Compression？
- Tau 与 Pi 的 Agent Loop 有什么区别？
- OpenHands 的 Sandbox 是如何设计的？
- LangGraph 的 Checkpoint 与普通 Session Persistence 有什么不同？
- 如果实现一个 Coding Agent Runtime，现有项目中有哪些可借鉴的设计？

传统搜索往往需要在多个仓库和页面之间来回切换；普通“向量检索 + LLM”式 RAG 又容易出现检索噪声、上下文缺失、无法追溯来源、跨项目比较不完整等问题。

因此，本项目希望构建一个专门面向 AI Agent 技术资料的 RAG 系统，并将“数据、检索、生成、评测”作为四个同等重要的部分，而不是只完成一个能够回答问题的 Demo。

---

## 2. 产品目标

### 2.1 核心目标

构建一个能够对 AI Agent / Coding Agent 技术资料进行：

1. 精准检索
2. 技术解释
3. 跨项目对比
4. 架构分析
5. 来源追溯
6. 可量化评测

的技术文档 RAG 系统。

### 2.2 项目成功的判断标准

项目不以“能回答问题”为唯一完成标准，而以以下能力为目标：

- 能解释每一层为什么存在。
- 能追踪一个问题经过 Query、Retrieval、Context、Generation 的完整链路。
- 能判断错误来自数据、检索还是生成。
- 能通过 benchmark 对 Chunk、Top-K、混合检索、Reranker 等方案进行比较。
- 最终回答能够回溯到明确的项目、文件、章节和原始来源。

---

## 3. 非目标

初版不追求：

- 全网 Agent 资料抓取。
- 大规模生产级爬虫。
- 通用搜索引擎能力。
- 复杂 Multi-Agent 编排。
- 一开始就构建完整 Web 前端。
- 一开始就支持几十种文件格式。
- 依赖超大模型弥补检索质量不足。

V0 的首要目标是把数据处理与检索链路做对。

---

## 4. 目标用户

### 4.1 主要用户

学习和研究 AI Agent / Coding Agent 的开发者。

### 4.2 典型需求

#### 技术解释

> Pi 的 Context Compression 是如何工作的？

#### 项目对比

> Pi 和 Tau 的 Agent Loop 有什么区别？

#### 架构理解

> OpenHands 的 Runtime、Sandbox 与 Agent 之间是什么关系？

#### 实现参考

> 如果我要实现 Checkpoint，可以参考哪些项目的设计？

#### 能力调查

> 哪些项目支持 Context Compression、Checkpoint 或 Sandbox？

---

## 5. 首批知识库范围

V0 建议控制在 5 个左右的高质量项目。

候选：

- Pi
- Tau
- mini-SWE-agent
- OpenHands
- LangGraph

后续可扩展：

- DeepAgents
- DeerFlow
- OpenAI Agents SDK
- 其他 Coding Agent / Agent Runtime 项目

### 5.1 V0 数据类型

优先收集：

- README
- `docs/**/*.md`
- `docs/**/*.mdx`
- Architecture / Design 文档
- 官方技术说明

V0 暂不默认纳入：

- 全量源码
- 所有 Issue
- 所有 Discussion
- 社区二手博客

原因是先控制知识库质量与规模。

---

# 6. 总体系统架构

系统分为两条主链路。

## 6.1 Offline Pipeline

```text
GitHub Technical Docs
        ↓
Loader
        ↓
Normalization
        ↓
Metadata Extraction
        ↓
Markdown-aware Parsing
        ↓
Parent / Child Chunking
        ↓
Deduplication
        ↓
Embedding
        ↓
Vector Index
        +
BM25 Index
```

## 6.2 Online Pipeline

```text
User Query
    ↓
Query Analysis
    ↓
Query Plan
    ↓
Metadata Filter
    ↓
Vector Search + BM25
    ↓
RRF Fusion
    ↓
Reranker
    ↓
Parent Expansion
    ↓
Context Builder
    ↓
LLM
    ↓
Answer + Citation
```

V0 不要求一次完成 Online Pipeline 中的全部组件。

---

# 7. 数据层设计

## 7.1 数据分层

知识库数据分为：

```text
data/
├── raw/
├── processed/
└── eval/
```

### Raw Corpus

保留原始技术文档，尽量不修改。

示例：

```text
data/raw/
├── pi/
├── tau/
├── mini-swe-agent/
├── openhands/
└── langgraph/
```

### Processed Data

预处理后的统一数据。

```text
data/processed/
├── documents.jsonl
└── chunks.jsonl
```

### Evaluation Dataset

独立维护评测数据。

```text
data/eval/
├── retrieval_eval.jsonl
└── generation_eval.jsonl
```

---

# 8. 文档标准化

不同项目的文档结构不同，因此 Loader 后增加 Normalization 层。

一个标准 Parent Document 至少包含：

```json
{
  "parent_id": "pi:docs/context.md:context-compression",
  "text": "...",
  "metadata": {
    "project": "pi",
    "repo": "...",
    "branch": "main",
    "commit_sha": "...",
    "source_path": "docs/context.md",
    "source_url": "...",
    "heading_path": [
      "Context Management",
      "Context Compression"
    ],
    "source_type": "docs",
    "language": "en"
  }
}
```

必须尽量保留：

- project
- repo
- branch
- commit_sha
- source_path
- source_url
- heading_path
- source_type
- language

建议增加：

- indexed_at
- content_hash
- start_line
- end_line

---

# 9. Chunking 设计

技术文档不采用简单固定长度硬切。

推荐方案：

> Markdown Heading-aware + Parent/Child + 代码块保护 + 标题注入 + 轻量 Overlap

## 9.1 Parent

一个完整、语义自洽的 Markdown Section。

建议大小：

- 约 800–2000 tokens
- 超长时再二次拆分

## 9.2 Child Chunk

用于检索的小块。

V0 初始参数：

- 300–500 tokens
- overlap 约 40–80 tokens
- overlap 不超过 10%–15% 为宜

## 9.3 Parent / Child 关系

```text
Parent Section
├── Child 001
├── Child 002
└── Child 003
```

检索时使用 Child。

生成时通过 `parent_id` 回溯 Parent。

原则：

> 小块负责找，大块负责答。

---

# 10. 特殊内容处理

## 10.1 代码块

Markdown fenced code block 默认视为不可随意拆分的结构单元。

若代码块过大，再考虑按：

- class
- function
- method

进行代码级切分。

V0 不要求 AST Parser。

## 10.2 Markdown Table

表格优先整体保留，避免列或行被拆散。

## 10.3 标题路径

每个 Chunk 保存完整 Heading Path，例如：

```text
Architecture > Context Management > Compression
```

而不仅保存当前标题 `Compression`。

## 10.4 标题注入

区分：

- `text`
- `embedding_text`

示例：

```json
{
  "text": "When the context exceeds...",
  "embedding_text": "Project: Pi\nSection: Context Management > Context Compression\n\nWhen the context exceeds..."
}
```

标题与项目名可以参与 Embedding，但不必重复展示给用户。

---

# 11. 去重策略

GitHub 项目经常在 README、Docs 和网站文档中重复同样内容。

V0 至少实现完全重复去重：

```text
normalized_text
    ↓
SHA256
    ↓
content_hash
```

相同内容只保留一份或建立来源映射。

后续版本再考虑 Near Duplicate Detection。

---

# 12. Embedding

Embedding 模型作为独立模块，不与 Vector DB 强绑定。

模块接口需要支持：

```text
embed_documents()
embed_query()
```

V0 选择一个中英文技术文档效果稳定的 Embedding 模型即可。

后续通过 Retrieval Benchmark 比较不同模型，而不是仅凭主观选择。

---

# 13. 索引与数据库

V0 可优先使用：

- FAISS：向量索引
- BM25：关键词索引

原因：

- 本地简单
- 易于实验
- 无额外服务依赖
- 便于理解检索链路

后续再评估是否升级至：

- pgvector
- Qdrant
- Milvus
- 其他 Vector DB

数据库切换不能改变上层 Retriever 接口。

---

# 14. Retrieval Strategy

V0 推荐：

```text
Question
    ↓
Vector Search Top-N
    +
BM25 Top-N
    ↓
RRF Fusion
    ↓
Top-K
```

## 14.1 Vector Search

解决语义相似问题。

例如：

```text
番茄炒蛋
≈
西红柿炒鸡蛋
```

在 Agent 技术文档中对应：

```text
conversation compaction
≈
context compression
```

## 14.2 BM25

解决：

- 项目名
- API 名
- 类名
- 方法名
- 专有术语

等强关键词问题。

## 14.3 RRF

使用 Reciprocal Rank Fusion 合并 BM25 与 Vector 排名。

V0 优先采用简单稳定方案，不急于训练复杂融合模型。

---

# 15. Reranker

V0 可不实现。

V1 增加 Reranker：

```text
BM25 + Vector
    ↓
RRF
    ↓
Candidate Top-N
    ↓
Reranker
    ↓
Final Top-K
```

需要通过评测验证 Reranker 是否真的提高检索质量，同时记录额外延迟。

---

# 16. Query Understanding

V1 增加 Query Analysis。

用户问题不直接作为普通字符串交给 Retriever，而先转成：

```python
QueryPlan(
    intent="compare",
    projects=["pi", "tau"],
    topic="context_management",
    query="context compression"
)
```

建议识别：

- intent
- project
- topic
- keywords

候选 intent：

- explain
- compare
- architecture
- implementation

---

# 17. Metadata Filter

利用 Query Plan 中的信息进行检索过滤。

例如：

> Pi 和 Tau 的 Context Compression 有什么区别？

提取：

```json
{
  "projects": ["pi", "tau"],
  "topic": "context_management"
}
```

后续限定候选知识范围。

---

# 18. Context Builder

Retriever 的 Top-K 结果不能直接简单拼接给 LLM。

Context Builder 负责：

1. 去重
2. Parent Expansion
3. 同一父文档合并
4. Token Budget
5. 来源平衡
6. 项目平衡
7. 代码块保护
8. 保留 Citation 信息

对于 Compare Query：

> Pi 和 Tau 有什么区别？

应避免 Top-K 全部来自 Pi。

可以考虑：

```text
Pi Top-N
Tau Top-N
    ↓
统一重排
```

---

# 19. Generation

Generation 层不只使用单一 Prompt。

按 Intent 使用不同回答模板。

## Explain

重点：

- 概念
- 工作流程
- 关键实现
- 来源

## Compare

重点：

- 共同点
- 差异
- 各自实现方式
- 设计取舍
- 来源证据

## Architecture

重点：

- 模块
- 数据流
- 状态流
- 边界
- 依赖关系

## Implementation

重点：

- 可以借鉴的具体设计
- 对应项目
- 实现位置
- 注意事项

---

# 20. Citation

最终答案必须尽量能够回溯原始来源。

Citation 至少包含：

- project
- source_path
- source_url
- section

条件允许时增加：

- start_line
- end_line
- commit_sha

例如：

```text
Source:
Pi / docs/context.md
Context Management > Compression
Lines 120–168
```

---

# 21. Evaluation

Evaluation 是本项目核心能力，不作为后期附加功能。

## 21.1 Retrieval Evaluation

优先实现：

- Hit@K
- Recall@K
- MRR
- NDCG（后续）

Retrieval Eval 样本：

```json
{
  "question": "Pi 如何处理 context compression？",
  "target_projects": ["pi"],
  "target_topics": ["context_management"],
  "expected_sources": [
    "pi/docs/context.md"
  ]
}
```

初期不要求完整 Reference Answer。

## 21.2 Generation Evaluation

后续加入：

- Context Relevance
- Faithfulness
- Answer Relevance
- Citation Correctness
- Comparison Completeness

---

# 22. Chunk Benchmark

V0 需要至少比较三种 Chunk 策略：

### A

```text
300 tokens
30 overlap
```

### B

```text
500 tokens
50 overlap
```

### C

```text
Heading-only
不做固定长度二次切分
```

使用约 20 个技术问题测试：

- Hit@3
- Hit@5
- MRR

Chunk 参数不通过“感觉”确定。

---

# 23. Observability

每次 Query 至少记录：

```text
trace_id
query
query_plan

vector_results
bm25_results
rrf_results
rerank_results

final_context
answer

retrieval_latency
generation_latency
total_latency

token_usage
```

目的：

能够回答：

> 这次失败到底是 Retriever 的问题，还是 Generator 的问题？

---

# 24. Online Update

V0：

```bash
python ingest.py
```

全量重新生成索引。

后续版本支持 Incremental Index：

```text
GitHub Repo
    ↓
Compare Commit SHA
    ↓
Detect Changed Docs
    ↓
Remove Old Chunks
    ↓
Re-chunk
    ↓
Re-embed
    ↓
Update Index
```

---

# 25. 推荐目录结构

```text
agentdocs-rag/
├── app/
│   ├── ingestion/
│   │   ├── loader.py
│   │   ├── normalizer.py
│   │   ├── splitter.py
│   │   ├── metadata.py
│   │   └── dedup.py
│   │
│   ├── indexing/
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   └── bm25_index.py
│   │
│   ├── retrieval/
│   │   ├── vector.py
│   │   ├── bm25.py
│   │   ├── fusion.py
│   │   └── reranker.py
│   │
│   ├── query/
│   │   └── analyzer.py
│   │
│   ├── context/
│   │   └── builder.py
│   │
│   ├── generation/
│   │   ├── prompts.py
│   │   └── generator.py
│   │
│   └── evaluation/
│       ├── dataset.py
│       ├── retrieval_metrics.py
│       └── generation_metrics.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── eval/
│
├── scripts/
│   ├── ingest.py
│   ├── build_index.py
│   └── evaluate.py
│
├── tests/
│
├── docs/
│   └── PRD.md
│
├── main.py
└── README.md
```

---

# 26. 版本规划

## V0 — 可解释的基础 RAG

目标：

完成一条清晰、可调试、可引用的 RAG Pipeline。

范围：

- 5 个左右 Agent 项目
- Markdown / MDX 加载
- 文档标准化
- Metadata
- Heading-aware Chunk
- Parent / Child
- FAISS
- BM25
- RRF
- Parent Expansion
- Context Builder
- LLM Generation
- Citation
- CLI
- 基础 Retrieval Evaluation

V0 暂不要求：

- Reranker
- Web UI
- FastAPI
- 自动 Query Router
- Incremental Index
- Dashboard

## V1 — 检索优化与评测

加入：

- Query Analysis
- Metadata Filter
- Reranker
- Retrieval Benchmark
- Generation Evaluation
- Trace
- 多策略实验

## V2 — 工程化

加入：

- FastAPI
- Web UI
- Incremental Index
- Evaluation Dashboard
- 更完整 Observability
- 更多数据源

---

# 27. V0 验收标准

满足以下条件即可认为 V0 完成：

### 数据

- 至少接入 5 个 Agent / Coding Agent 项目。
- Raw 与 Processed 数据分离。
- 每个 Chunk 有稳定 `chunk_id` 与 `parent_id`。
- 每个 Chunk 能追溯项目、路径、章节和 URL。

### Chunk

- 实现 Markdown Heading-aware。
- 默认保护 Code Fence 与 Table。
- Parent / Child 关系有效。
- 能人工抽查 Chunk。

### Retrieval

- Vector Search 可用。
- BM25 可用。
- RRF 可用。
- 能打印各阶段候选结果。

### Generation

- 能基于最终 Context 回答。
- 回答包含 Citation。
- Compare Query 能覆盖至少两个指定项目。

### Evaluation

- 有独立 Eval Dataset。
- 能计算 Hit@K、Recall@K、MRR。
- 至少完成一次 Chunk Strategy 对比实验。

### Observability

一次 Query 能够看到：

```text
Question
→ Retrieval Candidates
→ Final Context
→ Answer
```

并记录主要耗时。

---

# 28. 关键设计原则

## 原则一

不要用更大的 LLM 掩盖较差的 Retriever。

## 原则二

数据质量优先于框架复杂度。

## 原则三

小块负责检索，大块负责生成。

## 原则四

Embedding 与 Vector DB 解耦。

## 原则五

任何“优化”都尽量通过 Benchmark 验证。

## 原则六

尽量使用可确定的逻辑解决问题，不把所有步骤都交给 LLM。

## 原则七

回答必须尽可能可以追溯到 Source。

---

# 29. 待讨论问题

以下问题在开发过程中需要通过实验确定，而不在 PRD v0.1 中提前拍板：

1. 首批 5 个项目最终选择哪些？
2. 是否只抓 README/docs，还是加入部分源码？
3. Child Chunk 最优大小是 300、500 还是其他？
4. Parent 最大 Token Budget 设置多少？
5. Embedding 模型选择什么？
6. Vector DB 是否长期保留 FAISS？
7. BM25 与 Vector 的初始 Top-N 如何设置？
8. RRF 参数如何设置？
9. 是否需要 Cross-Encoder Reranker？
10. Context Builder 的最大 Token Budget？
11. Compare Query 如何保证多项目 Context 平衡？
12. Query Analysis 使用规则还是 LLM？
13. Topic Metadata 通过规则还是模型生成？
14. Evaluation Dataset 如何构建 Golden Sources？
15. 是否需要加入源码级 RAG？

这些问题应通过后续 Benchmark 与实际 Failure Case 逐步回答。

---

# 30. 当前开发建议

第一阶段不要立即接 LLM。

建议开发顺序：

```text
1. 收集 3–5 个项目技术文档
2. 完成 Loader
3. 完成 Normalizer
4. 完成 Metadata
5. 完成 Markdown-aware Splitter
6. 输出 documents.jsonl
7. 输出 chunks.jsonl
8. 随机人工检查至少 30 个 Chunk
9. 建立第一版 Retrieval Eval Dataset
10. 再开始 Embedding 与 Index
```

第一阶段的核心问题不是：

> “模型能不能回答？”

而是：

> “我们的知识究竟以什么结构进入系统？”

只有数据层稳定之后，再进入检索和生成层。
