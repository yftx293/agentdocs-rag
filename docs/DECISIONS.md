# AgentDocs RAG — 关键决策（已冻结）

> 本文件是 S0 的交付物之一：把 PRD §29 的 15 个待定问题 + 计划文档 §3 的决策全部落盘为默认值。
> 任何一项要改，都必须：改这里 + 走 benchmark 验证（PRD 原则五），否则视为越界。

## 1. PRD §29 待定问题的默认答案

| # | 待定问题 | 冻结决策 | 最终由哪个阶段验证 |
|---|---|---|---|
| 1 | 首批 5 项目 | Pi / Tau / mini-SWE-agent / OpenHands / LangGraph（用户已确认） | 已定 |
| 2 | 只抓 README/docs 还是加源码 | 只抓 README + `docs/**/*.md(x)`，V0 不加源码 | 已定 |
| 3 | Child Chunk 最优大小 | 初始 400（300–500 区间），overlap 50 | **S6** 用 A/B/C 实验定 |
| 4 | Parent 最大 Token Budget | 2000 tokens，超长二次拆分 | S3/S7 实测再调 |
| 5 | Embedding 模型 | **BGE-M3**，本地跑（`cuda`） | S5/S6 对比 |
| 6 | Vector DB 是否长期 FAISS | V0 用 FAISS `IndexFlatIP`，上层留抽象接口；V1+ 再评 pgvector/Qdrant | 已定 |
| 7 | BM25 与 Vector 初始 Top-N | 50 / 50 | S6 调 |
| 8 | RRF 参数 | k=60 | S6 调 |
| 9 | 是否 Cross-Encoder Reranker | V0 不做；V1 用 bge-reranker-v2-m3 | V1 |
| 10 | Context Builder 最大 Token Budget | 4000 tokens | S7 实测 |
| 11 | Compare Query 多项目平衡 | per-project Top-N 再统一重排 | S7 实现 |
| 12 | Query Analysis 规则还是 LLM | V0 规则版，V1 LLM | 已定 |
| 13 | Topic Metadata 规则还是模型 | V0 规则（标题路径启发式），V1 模型 | 已定 |
| 14 | Golden Sources 如何构建 | 人工从 chunk 清单挑真实文件/章节 | S4 实现 |
| 15 | 是否源码级 RAG | V0 不做，V1+ 再评估 | 已定 |

## 2. 其余冻结决策

| 议题 | 决策 |
|---|---|
| 生成模型 | **DeepSeek API**（用户已确认）；model `deepseek-chat`；temperature 0.0 |
| 生成隐私 | 调用 DeepSeek 会外发 context 片段 → **S8 前必须再次向用户确认** |
| BM25 实现 | `jieba` 分词 + `bm25s`（非纯 Python rank_bm25） |
| chunk_id | `sha1(parent_id + text)`，不用顺序号 |
| Token 计数 | 与 embedding tokenizer（XLM-R）对齐 |
| Query Analysis | V0 规则：项目名词典 + intent 关键词 |
| Trace | 每 query 一个 JSONL，`trace_id` 贯穿 |
| 网络代理 | `http://127.0.0.1:7897`（用户提供，S1 采集用；`AGENTDOCS_PROXY` 可覆盖） |
| 语料采集规则 | 偏离 PRD §5.1 字面 `docs/**`，改为每项目显式 include/exclude（因各仓库文档位置不同：pi=monorepo `packages/**/docs`、tau=`dev-notes/`、langgraph=`libs/**/README`）；排除 CHANGELOG/LICENSE/测试/CI 等噪声 |
| 包管理 | 一律 `uv`，禁止全局 pip |
| 目录根 | 项目根 = `D:/Projects/RAG`（不嵌套 agentdocs-rag/） |

## 3. 技术选型速查

| 层 | 选择 | 说明 |
|---|---|---|
| Embedding | BAAI/bge-m3（GPU，cuda） | 已装 CUDA torch；bge-m3 GPU 嵌入 2753 chunk ~3.2min |
| CUDA torch | 手动装 torch 2.6.0+cu124（本地 wheel，`uv pip install --reinstall .wheels/...`）；`uv run` 会回退 CPU，需用 `.venv/Scripts/python.exe` 直跑或 `--no-sync` | uv 客户端无法从镜像拉 CUDA wheel（TLS 握手失败），torch 未固定进 pyproject |
| Vector DB | FAISS IndexFlatIP | L2 归一化 = 余弦 |
| BM25 | bm25s + jieba | 中文分词 |
| 融合 | RRF k=60 | 简单稳定 |
| 生成 | DeepSeek chat | 唯一已有 key |
| 配置 | pydantic-settings + YAML | 单一参数入口 config/default.yaml |
| 校验 | pydantic v2 | schemas.py 单一事实源 |
