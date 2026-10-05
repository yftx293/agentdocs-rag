# AgentDocs RAG

面向 AI Agent / Coding Agent 技术资料的 RAG 系统：检索 · 解释 · 对比 · 追溯 · 评测。

## 文档
- PRD：`docs/PRD.md`
- 分阶段开发文档与状态：`docs/DEVELOPMENT_PLAN.md`
- 关键决策：`docs/DECISIONS.md`
- V0 验收清单：`docs/acceptance.md`
- Chunk Benchmark：`docs/benchmark-chunking.md`
- 失败归因：`docs/failure-analysis.md`

## 环境
- Python 3.12 + uv（虚拟环境 `.venv`）
- GPU：RTX 4060（CUDA torch 2.6.0+cu124，**手动 wheel 安装**）
- 模型：BGE-M3（本地 GPU）、DeepSeek（`DEEPSEEK_API_KEY` 环境变量）

> ⚠️ 运行脚本用 `.venv/Scripts/python.exe` 直接跑，**不要用 `uv run`**（会把 torch 回退成 CPU 版）。

## CLI
```bash
.venv/Scripts/python.exe scripts/ingest.py           # 语料采集（需代理）
.venv/Scripts/python.exe scripts/normalize.py        # 标准化 + 元数据 + 去重
.venv/Scripts/python.exe scripts/chunk.py            # 分块（heading-only）
.venv/Scripts/python.exe scripts/build_index.py      # embedding + FAISS + BM25（需 HF_HUB_OFFLINE=1）
.venv/Scripts/python.exe scripts/evaluate.py         # 检索评测（Hit@K/Recall@K/MRR）
.venv/Scripts/python.exe scripts/ask.py --chain      # 端到端问答 + 链路观测
.venv/Scripts/python.exe scripts/benchmark_chunking.py  # Chunk 策略 Benchmark
.venv/Scripts/python.exe scripts/failure_analysis.py    # 失败归因
```

## 检索基线
RRF 融合 hit@5=0.607 / mrr@5=0.320（28 题，section 级 golden，BGE-M3@GPU，heading-only 分块）。

## 状态
V0 完成（S0–S9）。
