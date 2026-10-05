# 失败归因分析（S9）

总题数 28，检索未命中 9 题

## 归因统计
- 数据缺失：0
- 分块缺失：0
- 检索未命中：9

## 失败题目明细

### Pi 的 compaction 在什么条件下触发？
- intent: explain · 项目: ['pi']
- golden: ['pi:packages/coding-agent/docs/compaction.md :: Compaction Reference > Compaction > When It Triggers']
- **检索未命中**: ['pi:packages/coding-agent/docs/compaction.md :: Compaction Reference > Compaction > When It Triggers']

### mini-SWE-agent 的 agent 控制流是怎样的？
- intent: explain · 项目: ['mini-swe-agent']
- golden: ['mini-swe-agent:docs/advanced/control_flow.md :: Agent control flow']
- **检索未命中**: ['mini-swe-agent:docs/advanced/control_flow.md :: Agent control flow']

### Pi 和 Tau 配置 provider 的方式有什么异同？
- intent: compare · 项目: ['pi', 'tau']
- golden: ['pi:packages/coding-agent/docs/providers.md :: Providers > Authenticate interactively', 'pi:packages/coding-agent/docs/providers.md :: Providers > Use an API key from the environment', 'tau:dev-notes/architecture/config-driven-provider-catalog.md :: Catalog shape', 'tau:dev-notes/architecture/config-driven-provider-catalog.md :: Overlay behavior']
- **检索未命中**: ['pi:packages/coding-agent/docs/providers.md :: Providers > Authenticate interactively', 'tau:dev-notes/architecture/config-driven-provider-catalog.md :: Overlay behavior', 'pi:packages/coding-agent/docs/providers.md :: Providers > Use an API key from the environment', 'tau:dev-notes/architecture/config-driven-provider-catalog.md :: Catalog shape']

### Tau 的 agent loop 设计文档（design/agent-loop）与实现文档（phase-3）关注点有什么不同？
- intent: compare · 项目: ['tau']
- golden: ['tau:dev-notes/architecture/phase-3-agent-loop.md :: Basic text-only flow', "tau:dev-notes/architecture/phase-3-agent-loop.md :: The loop's inputs", 'tau:dev-notes/design/agent-loop.md :: Minimal shape']
- **检索未命中**: ['tau:dev-notes/architecture/phase-3-agent-loop.md :: Basic text-only flow', "tau:dev-notes/architecture/phase-3-agent-loop.md :: The loop's inputs", 'tau:dev-notes/design/agent-loop.md :: Minimal shape']

### Tau 的 phase-3 agent loop 的输入有哪些？
- intent: architecture · 项目: ['tau']
- golden: ["tau:dev-notes/architecture/phase-3-agent-loop.md :: The loop's inputs"]
- **检索未命中**: ["tau:dev-notes/architecture/phase-3-agent-loop.md :: The loop's inputs"]

### 如果我要实现 Checkpoint，可以参考 LangGraph 的哪些设计？
- intent: implementation · 项目: ['langgraph']
- golden: ['langgraph:libs/checkpoint/README.md :: LangGraph Checkpoint > Interface', 'langgraph:libs/checkpoint/README.md :: LangGraph Checkpoint > Key concepts > Checkpoint', 'langgraph:libs/checkpoint/README.md :: LangGraph Checkpoint > Key concepts > Thread']
- **检索未命中**: ['langgraph:libs/checkpoint/README.md :: LangGraph Checkpoint > Interface', 'langgraph:libs/checkpoint/README.md :: LangGraph Checkpoint > Key concepts > Checkpoint', 'langgraph:libs/checkpoint/README.md :: LangGraph Checkpoint > Key concepts > Thread']

### 如果我要实现 session tree / branching，可以参考什么设计？
- intent: implementation · 项目: ['tau']
- golden: ['tau:dev-notes/architecture/phase-7-session-tree.md :: Entry types', 'tau:dev-notes/architecture/phase-7-session-tree.md :: Replay', 'tau:dev-notes/architecture/phase-7-session-tree.md :: Tree paths']
- **检索未命中**: ['tau:dev-notes/architecture/phase-7-session-tree.md :: Replay', 'tau:dev-notes/architecture/phase-7-session-tree.md :: Entry types', 'tau:dev-notes/architecture/phase-7-session-tree.md :: Tree paths']

### 如果我要实现一个 config-driven 的 provider catalog，可以参考什么？
- intent: implementation · 项目: ['tau']
- golden: ['tau:dev-notes/architecture/config-driven-provider-catalog.md :: Catalog shape', 'tau:dev-notes/architecture/config-driven-provider-catalog.md :: Overlay behavior', 'tau:dev-notes/architecture/config-driven-provider-catalog.md :: Validation']
- **检索未命中**: ['tau:dev-notes/architecture/config-driven-provider-catalog.md :: Overlay behavior', 'tau:dev-notes/architecture/config-driven-provider-catalog.md :: Validation', 'tau:dev-notes/architecture/config-driven-provider-catalog.md :: Catalog shape']

### 如果我要实现 sandbox / environment，mini-SWE-agent 提供了哪些类型？
- intent: implementation · 项目: ['mini-swe-agent']
- golden: ['mini-swe-agent:docs/advanced/environments.md :: Environment classes']
- **检索未命中**: ['mini-swe-agent:docs/advanced/environments.md :: Environment classes']
