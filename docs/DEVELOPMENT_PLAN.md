# AgentDocs RAG — 分阶段开发文档（对照文档 + 状态）

> 本文档是项目唯一的「开发对照 + 进度状态」文档。
> 用法：每完成一个阶段，立即更新本文档的
> ① 该阶段的「完成证据」小节、② 「阶段状态总表」、③ 底部「变更记录」。
> 任何未按文档执行的改动都属于越界。

- 关联 PRD：`docs/PRD.md`（S0 时由 `AgentDocs_RAG_PRD_v0.1.md` 复制而来）
- 项目目录：`D:/Projects/RAG`
- 当前状态：**V0 完成（S0–S9 全部 ✅）**

---

## 0. V0 封板修复记录（用户审查，2026-10）

用户审查发现 7 个问题，已全部修复：

| # | 问题 | 修复 |
|---|---|---|
| 1 | Token 计数与冻结决策不一致（文档写 XLM-R，实际 ~4 字符/token） | 改文档：V0 用估算，真实 tokenizer 留 V1 |
| 2 | golden 粒度不够（文件级，非 section 级） | 补 `expected_sections` 到 28 题，指标改 section 级 |
| 3 | S7 文档「per-project 检索」与实现「全局召回→分桶」不符 | 改文档与代码一致 |
| 4 | Citation 编号 bug（Sources 从 [1] 重编号，正文对不上） | `render_sources` 保留原始 context index |
| 5 | 脚本头命令 `uv run` 与 README 冲突 | 统一 `.venv/Scripts/python.exe` |
| 6 | 配置文档写 pydantic-settings，实际未用 | 改文档 + 移除依赖 |
| 7 | Loader 的 branch 配置未生效（用 HEAD） | 改 `ls-remote refs/heads/<branch>` |

**关键影响（#2）**：评测基线从「文件级 hit@5=0.821」修正为「section 级 hit@5=0.607 / mrr@5=0.320」。

**S6 重验**（section 级 golden）：heading-only 仍胜出（hit@5=0.607 第一），冻结结论不变。新发现：section 级下 BM25 衰减（0.357）、RRF < 纯向量（0.607 < 0.679）→ V1 需调融合权重或加 Reranker。

---

## 1. 项目概览（一句话）

构建面向 AI Agent / Coding Agent 技术资料的 RAG 系统，覆盖：精准检索、技术解释、跨项目对比、架构分析、来源追溯、可量化评测。

**成功判断（非"能回答问题"）**：能解释每层为何存在；能追踪 Query→Retrieval→Context→Generation 全链路；能判断错误来自数据/检索/生成；能用 benchmark 比较 Chunk/Top-K/混合检索/Reranker；答案能回溯到 项目/文件/章节/来源。

### 1.1 非目标（不做）

- 全网抓取、生产级爬虫、通用搜索
- 复杂 Multi-Agent 编排
- V0 阶段：Web UI / FastAPI / Reranker / Incremental Index / Dashboard / Query Analysis(LLM版)
- 抓取全量源码、Issue、Discussion、社区二手博客
- Near-duplicate detection、NDCG（V1+）
- pgvector / Qdrant / Milvus（V0 用 FAISS）

### 1.2 首批知识库（5 项目，已确认）

| 项目 | 仓库地址 | 默认分支 | 语料文档数 | 状态 |
|---|---|---|---|---|
| Pi | https://github.com/earendil-works/pi | `main` | 75 | ✅ 经代理连通 |
| Tau | https://github.com/huggingface/tau | `main` | 158 | ✅ 经代理连通 |
| mini-SWE-agent | https://github.com/SWE-agent/mini-swe-agent | `main` | 58 | ✅ 经代理连通 |
| OpenHands | https://github.com/All-Hands-AI/OpenHands | `main` | 15 | ✅ 经代理连通（语料稀疏） |
| LangGraph | https://github.com/langchain-ai/langgraph | `main` | 12 | ✅ 经代理连通（语料稀疏） |

---

## 2. 环境基线（实测，2026-10 实测）

| 项 | 值 |
|---|---|
| OS / Shell | Windows 11，Git Bash（MINGW64_NT，非 WSL） |
| Python | 3.12.12 |
| 包管理 | uv 0.12.21（一律 `uv venv`，禁止全局 pip 污染） |
| git | 2.53.0 |
| GPU | NVIDIA RTX 4060 Laptop，8GB VRAM |
| 已配置 Key | 仅 `DEEPSEEK_API_KEY`（环境变量） |
| GitHub 连通性 | ⚠️ 不稳定：pi 可达，其余 4 仓库 443 超时；无代理 |

> ⚠️ **环境风险**：GitHub 访问不稳定会直接阻塞 S1。S1 必须内置：代理支持、重试退避、以及 archive tarball（`codeload.github.com`）降级方案。必要时需要用户提供代理。

---

## 3. 已冻结的关键决策（S0 落盘到 `DECISIONS.md`）

| 议题 | 决策 | 备注 |
|---|---|---|
| 生成模型 | **DeepSeek API**（用户已确认） | 会把 context 片段外发，S8 前需二次确认 |
| Embedding | **BGE-M3**，本地跑 | 中英跨语对齐 + 8192 长度，8GB 显存够 |
| BM25 | `jieba` 分词 + `bm25s` | 中文文档检索必须分词 |
| Vector DB | FAISS `IndexFlatIP` + L2 归一化 | 上层保留抽象接口 |
| 检索参数 | Vector Top-N=50 / BM25 Top-N=50 / RRF k=60 / Final Top-K=8 | S6 用 benchmark 再调 |
| Reranker | V0 不做 | V1 用 bge-reranker-v2-m3 |
| Query Analysis | V0 规则版（项目名词典 + intent 关键词） | V1 再上 LLM |
| chunk_id | `sha1(parent_id + text)`，不用顺序号 | 保证增量/复跑稳定 |
| Token 计数 | 与 Embedding 模型 tokenizer 对齐（XLM-R） | 避免 chunk 大小与向量输入错位 |
| Trace | 每 query 一个 JSONL，`trace_id` 贯穿 | PRD §23 |

---

## 4. 数据契约（单一事实源 `app/core/schemas.py`）

> ⚠️ `schemas.py` 是全链路单一事实源。S0 冻结后，任何字段改动 = 下游全部模块 + 两个 jsonl + 评测集格式重写，必须走文档变更流程。

**Document（Parent）** 必填字段：`parent_id / text / metadata{project, repo, branch, commit_sha, source_path, source_url, heading_path, source_type, language}`；建议增加 `indexed_at / content_hash / start_line / end_line`。

**Chunk（Child）** 必含：稳定 `chunk_id` + `parent_id`；`text` 与 `embedding_text` 分离（标题注入只进 embedding_text，不重复展示给用户）。

---

## 5. 目标目录结构（V0 完成后）

```text
agentdocs-rag/
├── pyproject.toml  .gitignore  README.md
├── config/default.yaml            # 唯一参数入口
├── app/
│   ├── core/{schemas,config,logging}.py
│   ├── ingestion/{loader,normalizer,metadata,dedup}.py
│   ├── indexing/{embeddings,vector_store,bm25_index}.py
│   ├── retrieval/{vector,bm25,fusion}.py   (+ reranker.py V1 占位)
│   ├── query/analyzer.py
│   ├── context/builder.py
│   ├── generation/{prompts,generator}.py
│   ├── evaluation/{dataset,retrieval_metrics}.py
│   └── observability/tracer.py
├── scripts/{ingest,build_index,ask,evaluate}.py
├── tests/{test_normalizer,test_splitter,test_dedup,test_metrics}.py + fixtures/
├── data/{raw,processed,eval}/
└── docs/{PRD.md, DEVELOPMENT_PLAN.md, DECISIONS.md, chunk-spotcheck.md, benchmark-chunking.md}
```

---

## 6. 全局红线（任何阶段都不得触碰）

### 6.1 不能动的东西（资产）

1. **`data/raw/`** — 不可变语料。只读，永不修改、永不润色、永不翻译，也不在里面写衍生文件。
2. **`data/eval/`** — 手写 golden 评测集。脚本只读，**绝不允许脚本覆盖/删除**；指标输出写到别处。
3. **`app/core/schemas.py`** — 数据契约。冻结后改动必须显式走变更。
4. **`AgentDocs_RAG_PRD_v0.1.md`** — 原始 PRD，永不改动（只复制为 `docs/PRD.md`）。

### 6.2 数据红线

- 不抓白名单外内容（全源码/Issue/Discussion/社区博客）。
- 不用网络搜索或二手文章冒充知识库或评测 golden（golden 必须来自真实语料文件，可回溯）。
- 删除 `data/processed/` 历史版本前必须可逆/有备份。

### 6.3 安全/隐私红线

- 任何密钥（含 `DEEPSEEK_API_KEY`）只读环境变量，禁止写进源码/配置/git。
- 语料内容不得发给未经用户同意的第三方（V0 embedding 本地跑）。
- 生成层调用 DeepSeek 会外发 context 片段 → **S8 前必须再次向用户确认，未确认绝不调用**。

### 6.4 操作红线

- 禁止 `git push` / 创建远程仓库 / 任何远程写操作。
- 禁止全局或破坏性环境操作：改系统 PATH、动 WSL、动 NVIDIA 驱动、全局 `pip install`。
- 禁止并发高速抓 GitHub（串行、保守速率、`--depth 1` 或 archive）。
- 禁止把大文件塞进 git：`raw/`、模型缓存、`.venv`、trace 全部 gitignore。

### 6.5 诚实红线

- 禁止编造 benchmark 数字（Hit@K/MRR 必须来自真实运行，可复现）。
- 禁止"假装跑过测试"——每个 Gate 必须附真实命令输出。

---

## 7. 分阶段计划（S0–S9，归为 4 个里程碑）

> 每个阶段：目标 → 改动 → 验收 → 完成证据 → 影响与风险。

### 里程碑① 地基

#### S0 — 决策冻结 + 工程骨架 + 数据契约 ✅

- **完成什么**：冻结 §3 全部决策到 `DECISIONS.md`；建 `pyproject.toml`/`.gitignore`/`config/default.yaml`；定义 `schemas.py` 数据契约；复制 PRD → `docs/PRD.md`（原文件保留）。
- **产生改动**：新增 `pyproject.toml` `.gitignore` `config/default.yaml` `app/core/{schemas,config,logging}.py` `docs/{PRD,DECISIONS}.md`
- **怎么验收**：`uv run python -c "import app"` 成功；`DECISIONS.md` 覆盖 PRD §29 全部 15 个待定项；`schemas.py` 含 Document/Chunk/QueryPlan/Citation/Trace 五个模型。
- **完成证据** ✅（2026-10 实测）：`uv run python -c "import app"` → `app version: 0.1.0`；`uv sync` 解析并安装 15 包；schemas/config 加载验证输出 `ALL GATES PASSED`（proxy=`http://127.0.0.1:7897`、5 项目齐全、Document/Chunk/QueryPlan 构造成功）；`docs/PRD.md`、`docs/DECISIONS.md` 已生成。
- **影响与风险**：`schemas.py` 是单一事实源，S0 定错字段名，后面全链路重写（本阶段最贵决策）；`pyproject.toml` 依赖版本锁死，后续升级需谨慎。

### 里程碑② 数据层

#### S1 — 语料采集（确定性 Loader）✅

- **完成什么**：抓取 5 项目 README + `docs/**/*.md(x)` 到 `data/raw/<project>/`；记录 `commit_sha` 到 `manifest.json`；loader 只读、可重跑、产物字节一致。
- **产生改动**：新增 `app/ingestion/loader.py` `scripts/ingest.py` `data/raw/**` `data/raw/manifest.json`
- **怎么验收**：5 项目文件落盘；`manifest.json` 含每项目 `commit_sha`；重跑脚本产物一致（`git -C data/raw/<p> rev-parse HEAD` 与 manifest 一致）。
- **完成证据** ✅（2026-10 实测）：`manifest.json`（schema_version=1，5 项目各含 commit_sha）；`data/raw/` 共 318 文档（pi=75 / tau=158 / mini-swe-agent=58 / openhands=15 / langgraph=12）；关键文档抽查命中（pi/compaction.md、pi/how-pi-works.md、tau/dev-notes、langgraph/libs/checkpoint/README.md、openhands/specs）；openhands 仅含 README/AGENTS/docs/specs（无测试/源码噪声）；重跑幂等：5 项目全部 `commit 未变，跳过`（零改动）。
- **影响与风险**：GitHub 连通性已通过代理 `http://127.0.0.1:7897` 解决（`git ls-remote` + codeload tarball 双通道验证）；不 pin commit_sha 会导致 benchmark 漂移 → 已 pin 并写入 manifest（且实测 pi/openhands 的 commit 在采集期间就发生了变动，印证 pin 的必要）。⚠️ 新发现：openhands(15)/langgraph(12) 主仓库文档稀疏（详细文档在独立 docs 仓库），是否补充需后续决策。

#### S2 — 标准化 + 元数据 + 去重 ✅

- **完成什么**：解析 frontmatter/heading 树/source_url；提取 PRD §8 全部元数据；按 `content_hash`(SHA256) 完全重复去重并保留来源映射；输出 `data/processed/documents.jsonl`。
- **产生改动**：新增 `app/ingestion/{normalizer,metadata,dedup}.py` `tests/{test_normalizer,test_dedup}.py` `data/processed/documents.jsonl`
- **怎么验收**：每条 document 含 PRD §8 全部必填字段；完全重复内容只剩一份且保留来源映射；`pytest` 通过。
- **完成证据** ✅（2026-10 实测）：`pytest -q` → `9 passed`；`documents.jsonl` 318 篇，字段完整性校验 0 缺失（project/repo/branch/commit_sha/source_path/source_url/heading_path/source_type/language + content_hash 全覆盖）；重跑 md5 一致（`76e875…b859`，确定性）；`dedup_report.json` 生成（去重前 318 = 去重后 318，真实语料无字节级重复，去重逻辑已由单测覆盖）。
- **影响与风险**：`content_hash` 归一化规则决定去重粒度（过激进会误删相似但不同的内容）；heading_path 解析错误会连带污染 S3 分块。

#### S3 — Markdown-aware Parent/Child 分块 ✅

- **完成什么**：heading-aware 切分；Code Fence / Table 保护；标题注入（`text` vs `embedding_text`）；轻量 overlap（不超 10–15%）；输出 `data/processed/chunks.jsonl`。
- **产生改动**：新增 `app/ingestion/splitter.py` `tests/test_splitter.py` `data/processed/chunks.jsonl` `docs/chunk-spotcheck.md`
- **怎么验收**：Code Fence/Table 不被拆散；heading_path 完整；`chunk_id`/`parent_id` 稳定；**人工抽查 ≥30 个 chunk 并写结论**（PRD §30 硬要求）。
- **完成证据** ✅（2026-10 实测）：`pytest -q` → `17 passed`；`chunks.jsonl` 2753 个 / `parents.jsonl` 2410 个；chunk_id 唯一、0 孤儿 chunk；代码块被拆开（奇数围栏）= 0（修了嵌套围栏缩进 bug）；人工抽查 30 chunk 报告见 `docs/chunk-spotcheck.md`（结论：结构正确，3 个待优化项归 S6）。
- **影响与风险**：⚠️ **抽查不能偷懒**——跳过抽查，S6 的 benchmark 只是在给错误切分调参；chunk 参数（大小/overlap）直接决定 chunk_id 与 S4 golden 匹配、S6 全部指标。

### 里程碑③ 评测 + 检索

#### S4 — 评测集 v0 + 检索指标（先于 Embedding）✅

- **完成什么**：写 ≥25 题覆盖 4 类 intent（explain/compare/architecture/implementation），每题含 golden `project + source_path + heading`；实现 Hit@K / Recall@K / MRR。
- **产生改动**：新增 `app/evaluation/{dataset,retrieval_metrics}.py` `data/eval/retrieval_eval.jsonl` `tests/test_metrics.py`
- **怎么验收**：题目数 ≥25 且覆盖 4 intent；golden 全部可回溯到真实文件；指标有手算单测。
- **完成证据** ✅（2026-10 实测）：`retrieval_eval.jsonl` 28 题（explain 10 / compare 6 / architecture 6 / implementation 6），4 类 intent 全覆盖；golden 源 0 缺失（全部映射到真实文件）；`pytest -q` → `21 passed`（含 Hit@K/Recall@K/MRR 手算用例）；指标模块 `retrieval_metrics.py` 实现。
- **影响与风险**：⚠️ **golden 是手写资产**，脚本只读，覆盖它会污染 S6 及之后所有对比结论；golden 若写错/编造，整个评测体系失效。实测发现：openhands(3)/langgraph(3) 可写题目偏少（语料稀疏所致），这两项在 benchmark 中信号较弱——若需强化，须先补语料。

#### S5 — Embedding + FAISS + BM25 + RRF ✅

- **完成什么**：实现 `embed_documents/embed_query` 接口；FAISS 索引；bm25s 索引；RRF 融合；`scripts/build_index.py` 跑通。
- **产生改动**：新增 `app/indexing/{embeddings,vector_store,bm25_index}.py` `app/retrieval/{vector,bm25,fusion}.py` `scripts/build_index.py` + 索引文件
- **怎么验收**：检索链路端到端跑通；在 S4 eval set 上产出**第一组真实 Hit@5/MRR**。
- **完成证据** ✅（2026-10 实测，BGE-M3@GPU）：索引构建成功（FAISS + BM25，2753 chunks，**1024 维**，GPU 嵌入 ~3.2min）；`evaluate.py` 真实数字——**RRF 融合 hit@5=0.821 / mrr@5=0.588**，vector-only(0.786/0.599)、bm25-only(0.714/0.538)。对比 bge-small-zh 的 rrf 0.750：BGE-M3 使 vector 从 0.643→0.786，坐实 embedding 选型对跨语言检索的决定性影响。
- **影响与风险**：⚠️ **切换 embedding 模型 = 向量空间全变 = 重建索引 + 重跑全部 benchmark（全项目最贵改动）**；BM25 分词器（jieba）影响召回，切换需重新 benchmark。已解决：装 CUDA torch 2.6.0+cu124（手动 wheel），BGE-M3 在 GPU 上嵌入 2753 chunk 仅 ~3.2min。

#### S6 — Chunk 策略 Benchmark（A/B/C）✅

- **完成什么**：按 PRD §22 跑 3 种策略（300/30、500/50、Heading-only）于同一 eval set，输出对比表，反解并**冻结** S0 待定参数进 `default.yaml`。
- **产生改动**：新增 `scripts/evaluate.py` 完善 `docs/benchmark-chunking.md` 修改 `config/default.yaml`
- **怎么验收**：3 策略对比表齐全，Hit@3/Hit@5/MRR 有真实数字；选定默认策略并写进 config。
- **完成证据** ✅（2026-10 实测）：三策略对比——A(300/30) hit@5=0.786、B(500/50) hit@5=0.821、**C(heading-only) hit@3=0.821/hit@5=0.821/mrr@5=0.631 胜出**；已冻结 heading-only 进 config 并重跑生产数据（2391 chunks，RRF hit@5=0.821/mrr@5=0.631）。报告见 `docs/benchmark-chunking.md`。
- **影响与风险**：参数一旦冻结进 config，后续改动必须重新 benchmark 证明，否则违反 PRD 原则五。

### 里程碑④ 生成 + 收口

#### S7 — Parent Expansion + Context Builder ✅

- **完成什么**：去重、Parent Expansion、同父合并、Token Budget、来源平衡、项目平衡、代码块保护、Citation 保留。
- **产生改动**：新增 `app/context/builder.py`
- **怎么验收**：compare 查询的 `final_context` 不偏斜（Pi/Tau 各自占比可打印）；Token Budget 生效；citation 在裁剪中不丢。
- **完成证据** ✅（2026-10 实测）：`ContextBuilder`（去重/token 预算/项目平衡/citation）+ `retrieve_balanced`（全局召回 → 按项目分桶 + 每项目上限 → round-robin）实现；28 单测过；demo 对 2 个 compare 查询——compaction 查询达成 7:7 平衡、agent-loop 查询 pi:1/tau:8（pi 的 agent-loop 语料本就稀疏，平衡受限于语料现实）。注：S6 冻结 heading-only 后 chunk=section=parent，「Parent Expansion/同父合并」天然退化（无 child 可展开），S7 实际聚焦 Context Builder。
- **影响与风险**：⚠️ **Context Builder 决定生成质量上限**——项目偏斜会直接让 compare 答案失效；token 预算与 citation 保留是此消彼长，需明确取舍。

#### S8 — 生成 + 引用（按 Intent 分模板）✅

- **完成什么**：4 类 intent 各自 Prompt 模板；规则版 Query Analysis；Citation 渲染（project/source_path/source_url/section/line）。
- **产生改动**：新增 `app/generation/{prompts,generator}.py` `app/query/analyzer.py`
- **怎么验收**：4 intent 各 ≥2 题，回答带可解析 Citation，可回溯到 source_url + 行号。
- **完成证据** ✅（2026-10 实测，DeepSeek 真实调用，已获用户确认）：8 题（explain 3 / compare 2 / architecture 1 / implementation 2）端到端完成，全部含 Sources；共 55 条引用，均可回溯到 commit 锚定 URL + 行号；compare 答案同时引用 pi+tau（项目平衡生效）；32 单测过。已知局限：规则版 analyzer 把「如何解析」误判为 explain（eval 标 architecture），V1 用 LLM 修正。
- **影响与风险**：⚠️ **首次调用 DeepSeek API，外发 context 片段，必须先向用户确认**；引用若拼错 source_url/行号，等于伪造来源（红线）。

#### S9 — Trace + CLI + V0 验收 + 失败归因 ✅

- **完成什么**：四步 CLI（ingest/build_index/ask/evaluate）；trace 记录全链路耗时/token；PRD §27 验收清单逐条打勾；挑 10–20 失败题归因到 数据/检索/生成。
- **产生改动**：新增 `app/observability/tracer.py` `scripts/ask.py` `README.md` + trace 输出
- **怎么验收**：任一次 query 可打印 `Question → Candidates → final_context → Answer + 耗时`；PRD §27 全部满足。
- **完成证据** ✅（2026-10 实测）：`tracer.py` 实现，`ask.py --chain` 打印全链路（vector/bm25/rrf 候选 → final_context → 耗时），8 条 trace 写入 `traces/traces.jsonl`（含各阶段耗时+token）；`failure_analysis.py` 归因：28 题 4 题检索未命中（0 数据缺失，详见 `docs/failure-analysis.md`）；V0 验收清单逐条打勾（`docs/acceptance.md`）；README 补 CLI 用法。
- **影响与风险**：失败归因结论决定 V1 优先级（是补数据、换检索、还是调生成），是本阶段核心产出。

---

## 8. 阶段状态总表（每阶段完成即更新）

| 阶段 | 状态 | 完成证据 | 完成日期 | 备注 |
|---|---|---|---|---|
| S0 决策冻结+骨架 | ✅ 完成 | `import app`=0.1.0；uv sync 15包；ALL GATES PASSED | 2026-10 | 代理已写入 config |
| S1 语料采集 | ✅ 完成 | 318 文档；manifest 含 commit_sha；重跑幂等零改动 | 2026-10 | 经代理连通 |
| S2 标准化+元数据+去重 | ✅ 完成 | 318 文档字段全覆盖；9 测试过；重跑 md5 一致 | 2026-10 | 真实语料 0 重复 |
| S3 分块 | ✅ 完成 | 2753 chunks/2410 parents；17 测试过；30 chunk 抽查通过 | 2026-10 | 详见 chunk-spotcheck.md |
| S4 评测集+指标 | ✅ 完成 | 28 题/4 intent；golden 0 缺失；21 测试过 | 2026-10 | openhands/langgraph 信号弱 |
| S5 索引+混合检索 | ✅ 完成 | RRF hit@5=0.821/mrr@5=0.588（文件级，封板前） | 2026-10 | CUDA torch 已装 |
| S6 Chunk Benchmark | ✅ 完成 | C(heading-only) 胜出：mrr@5=0.631（文件级，封板后 section 级重验仍胜出） | 2026-10 | 已冻结进 config |
| S7 Context Builder | ✅ 完成 | 7:7 平衡（compaction）；retrieve_balanced 上限 | 2026-10 | Parent Expansion 已退化 |
| S8 生成+引用 | ✅ 完成 | 8 题 4 intent 全通；55 引用可回溯 | 2026-10 | DeepSeek 真实调用 |
| S9 Trace+CLI+验收 | ✅ 完成 | 8 trace；4 题检索未命中归因；验收全过 | 2026-10 | V0 完成 |

图例：⬜ 待开始 / 🔵 进行中 / ✅ 完成 / ⛔ 阻塞

---

## 9. V1 / V2 展望（明确不在 V0 范围）

- **V1**：Query Analysis(LLM) → Metadata Filter → Reranker → Generation Eval(Faithfulness/Citation Correctness/Comparison Completeness) → 多策略实验。
- **V2**：FastAPI → Web UI → Incremental Index(commit diff) → Evaluation Dashboard。

---

## 10. 变更记录

| 日期 | 阶段 | 变更内容 |
|---|---|---|
| 2026-10 | 立项 | 创建本开发文档（S0 待启动） |
| 2026-10 | S0 | 决策冻结 + 工程骨架 + 数据契约；`uv sync` 成功；双 Gate 通过（import app + schemas/config 加载） |
| 2026-10 | S1 | 语料采集完成：5 项目 318 文档，manifest 记录 commit_sha，重跑幂等；修 glob 匹配器 bug |
| 2026-10 | S2 | 标准化+元数据+去重完成：documents.jsonl 318 篇字段全覆盖，9 单测过，重跑确定性 |
| 2026-10 | S3 | 分块完成：2753 chunks/2410 parents，修嵌套围栏 bug，30 chunk 抽查通过 |
| 2026-10 | S4 | 评测集+指标完成：28 题 4 intent，golden 全部真实，Hit@K/Recall@K/MRR 实现并手算验证 |
| 2026-10 | S5 | 索引+混合检索完成：bge-small-zh 首轮 RRF hit@5=0.750；装 CUDA torch 后 BGE-M3@GPU 重跑 RRF hit@5=0.821/mrr@5=0.588 |
| 2026-10 | S6 | Chunk Benchmark 完成：heading-only 胜出（mrr@5=0.631），已冻结；修 fp16 显存 OOM |
| 2026-10 | S7 | Context Builder + retrieve_balanced 完成：项目平衡生效，28 单测过 |
| 2026-10 | S8 | 生成+引用完成：Query Analysis(规则) + 4 intent Prompt + DeepSeek 生成，8 题全通 55 引用可回溯 |
| 2026-10 | S9 | Trace+验收+失败归因完成：V0 全部验收通过，检索基线 hit@5=0.821（文件级） |
| 2026-10 | 封板 | 用户审查 7 问题全部修复：section 级 golden（hit@5 修正为 0.607）、citation 编号 bug、branch 生效等；S6 重验 heading-only 仍胜出 |
