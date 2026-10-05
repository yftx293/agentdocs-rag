# Chunk 抽查样本（自动生成，供人工复核）

抽样 30 / 2753 个 chunk，seed=42
完整性：奇数 ``` 的 0 个；奇数 ~~~ 的 0 个

### [1] tau · dev-notes/tui-coding-agent-footprint.md
- heading_path: `['TUI on the Coding Agent Layer: Development Footprint', 'Roadblocks and lessons learned', 'Roadblock: prompt display felt delayed in long sessions']` · 行 562-579 · 188 tok · id `fb0cef62acef`

```text
Roadblock: prompt display felt delayed in long sessions

**Seen in:** issue #166, branch `tui-yield-before-persist` commit
`a4ff9fa Improve prompt event immediacy`.

**Symptom:** pressing Enter could feel slow because the TUI waited for
`MessageEndEvent`, and `CodingSession.prompt()` persisted the message before
yielding it.

**Root cause:** event-authoritative display plus synchronous persistence
```

### [2] pi · AGENTS.md
- heading_path: `['Development Rules', 'Commands']` · 行 30-41 · 298 tok · id `ee49252c435b`

```text
Commands

- After code changes (not docs): `npm run check` (full output, no tail).

Fix all errors, warnings, and infos before committing.

Does not run tests.
- Never run `npm run build` or `npm test` unless requested by the user.
- Never run the full vitest suite directly: it includes e2e tests that activate when endpoint/auth env vars are present.

For all non-e2e tests, run `./test.sh` from th
```

### [3] langgraph · libs/sdk-py/README.md
- heading_path: `['LangGraph Python SDK', 'Quick Start']` · 行 27-50 · 156 tok · id `20916f59533d`

```text
Quick Start

```python
from langgraph_sdk import get_client

# If you're using a remote server, initialize the client with `get_client(url=REMOTE_URL)`
client = get_client()

# List all assistants
assistants = await client.assistants.search()

# We auto-create an assistant for each graph you register in config.
agent = assistants[0]

# Start a new thread
thread = await client.threads.create()

# S
```

### [4] pi · packages/coding-agent/docs/windows.md
- heading_path: `['Run Pi on Windows', 'Choose native Windows or WSL']` · 行 7-13 · 139 tok · id `f5ee290e5788`

```text
Choose native Windows or WSL

| Environment | Command environment | Use it when |
|---|---|---|
| Native Windows with Git Bash | Git Bash for the built-in `bash` tool and `!` commands | Your files and development tools primarily live on Windows |
| Native Windows with the `powershell` tool | PowerShell for model tool calls; Bash remains available for `!` commands | The task depends on PowerShell m
```

### [5] pi · packages/coding-agent/docs/session-format.md
- heading_path: `['Session File Format', 'Entry Types', 'CompactionEntry']` · 行 123-137 · 355 tok · id `b34d23a1bfde`

```text
CompactionEntry

Created when context is compacted. Stores a summary of earlier messages and a complete system prompt/tool checkpoint.

```json
{"type":"compaction","id":"f6g7h8i9","parentId":"e5f6g7h8","timestamp":"2024-12-03T14:10:00.000Z","summary":"User discussed X, Y, Z...","firstKeptEntryId":"c3d4e5f6","tokensBefore":50000,"systemMessage":{"role":"system","content":"You are a coding assistan
```

### [6] pi · packages/coding-agent/docs/rpc-commands.md
- heading_path: `['RPC Commands', 'Thinking']` · 行 272-272 · 2 tok · id `45f2ceef091c`

```text
Thinking
```

### [7] pi · packages/ai/README.md
- heading_path: `['@earendil-works/pi-ai', 'Faux Provider for Tests']` · 行 1430-1504 · 462 tok · id `6ebe5687ae5e`

```text
Faux Provider for Tests

`fauxProvider()` builds an in-memory provider with scripted responses for tests and demos:

```typescript
import {
  createModels,
  fauxAssistantMessage,
  fauxProvider,
  fauxText,
  fauxThinking,
  fauxToolCall,
} from '@earendil-works/pi-ai';

const faux = fauxProvider({
  tokensPerSecond: 50 // optional
});

const models = createModels();
models.setProvider(faux.provi
```

### [8] openhands · docs/architecture.md
- heading_path: `['Agent Canvas architecture', 'Quality gates']` · 行 68-78 · 97 tok · id `8e0ec678364e`

```text
Quality gates

The main CI workflow installs dependencies with `npm ci` and runs:

- Typecheck, ESLint, and Prettier through `npm run lint`.
- Unit and component tests through `npm test`.
- Standalone app build through `npm run build`.
- Library build through `npm run build:lib`.
- Package verification through `npm pack --dry-run`.

Additional workflows run optional live end-to-end QA.
```

### [9] tau · dev-notes/design/agent-loop.md
- heading_path: `['Minimal shape']` · 行 11-31 · 168 tok · id `4e637779d913`

```text
Minimal shape

```python
async for event in run_agent_loop(
    provider=provider,
    model="...",
    system="...",
    messages=messages,
    tools=tools,
):
    ...
```

The loop is intentionally independent of the CLI, Rich, Textual, and session file locations.

The current loop also accepts optional queue-drain hooks from `AgentHarness`.
Those hooks let the loop inject steering messages afte
```

### [10] openhands · docs/DEVELOPMENT.md
- heading_path: `['Development', 'Alternative development workflows', 'Multiple local backends (shared persistence)']` · 行 221-226 · 77 tok · id `92bf303ac243`

```text
Multiple local backends (shared persistence)

To run a second standalone agent-server alongside `npm run dev` while sharing
its conversation history and encrypted secrets, you can use the
`npm run dev:extra-backend` helper. It launches an extra server on `:18002` that
reuses the bundled instance's state dir.
```

### [11] tau · dev-notes/herdr-textual-mouse-compatibility.md
- heading_path: `['Herdr/Textual mouse compatibility', 'Tau workaround']` · 行 25-39 · 145 tok · id `3d3cacaf7888`

```text
Tau workaround

Before starting the TUI under `HERDR_ENV=1`, Tau defaults
`TEXTUAL_SMOOTH_SCROLL` to `0` and updates Textual's loaded setting. In Textual
8.2.8 this disables the in-band resize/pixel-mouse path, retaining SIGWINCH-based
resizing and cell-coordinate mouse events. Tau does not need sub-cell pointer
precision.

The workaround:

- applies only inside Herdr;
- preserves an explicit `TEX
```

### [12] tau · dev-notes/architecture/phase-11-print-event-rendering.md
- heading_path: `['Why this exists']` · 行 28-46 · 131 tok · id `795faa298566`

```text
Why this exists

Pi keeps terminal output modes outside the reusable agent core:

```text
agent/session emits events
print mode consumes events for final text or JSON output
interactive mode uses a separate TUI layer
```

Tau now follows the same architectural boundary:

```text
tau_agent     portable event-producing harness
tau_coding    CLI mode selection and event rendering
future TUI    anothe
```

### [13] mini-swe-agent · docs/advanced/cookbook.md
- heading_path: `['Cookbook']` · 行 1-23 · 449 tok · id `ba7b064a97d6`

```text
Cookbook

!!! abstract "Remixing & extending mini"

* This guide shows how to mix the different components of the `mini` agent to create your own custom version.
    * You might want to first take a look at the [control flow of the default agent](control_flow.md) first

!!! note "Development setup"

Make sure to follow the dev setup instructions in [quickstart.md](../quickstart.md).

We provide se
```

### [14] mini-swe-agent · README.md
- heading_path: `['The minimal AI software engineering agent', 'Attribution']` · 行 189-217 · 503 tok · id `21e47ab927a9`

```text
Attribution

If you found this work helpful, please consider citing the [SWE-agent paper](https://arxiv.org/abs/2405.15793) in your work:

```bibtex
@inproceedings{yang2024sweagent,
  title={{SWE}-agent: Agent-Computer Interfaces Enable Automated Software Engineering},
  author={John Yang and Carlos E Jimenez and Alexander Wettig and Kilian Lieret and Shunyu Yao and Karthik R Narasimhan and Ofir P
```

### [15] openhands · docs/DefenseClaw.md
- heading_path: `['Integrating DefenseClaw with Agent Canvas', 'Future Work: Code-Level Extensions', '1. Native `SecurityAnalyzer` hook']` · 行 250-266 · 260 tok · id `0919ac35ccd5`

```text
1. Native `SecurityAnalyzer` hook

The OpenHands SDK exposes a [`SecurityAnalyzer`](https://docs.openhands.dev/sdk/arch/security.md) interface. A custom implementation could call DefenseClaw's `/api/v1/inspect/tool` endpoint before every tool invocation — mirroring the inspection the OpenClaw TypeScript plugin performs. This would gate bash commands, file writes, and other tool calls through Defen
```

### [16] pi · packages/coding-agent/docs/quickstart.md
- heading_path: `['Quickstart', 'Next steps']` · 行 96-100 · 63 tok · id `b3de6ee7e742`

```text
Next steps

- [Use Pi interactively](usage.md) to learn input, commands, shortcuts, and queued messages.
- [Add instructions](configuration.md#context-files) that Pi should follow whenever it works in a folder.
- [Choose a model and provider](models.md).
```

### [17] pi · packages/coding-agent/docs/rpc-extension-ui.md
- heading_path: `['RPC Extension UI', 'Requests from Pi', 'setStatus']` · 行 113-127 · 79 tok · id `14ccdc84ccc7`

```text
setStatus

Set or clear a status entry in the footer/status bar. Fire-and-forget.

```json
{
  "type": "extension_ui_request",
  "id": "uuid-6",
  "method": "setStatus",
  "statusKey": "my-ext",
  "statusText": "Turn 3 running..."
}
```

Send `statusText: undefined` (or omit it) to clear the status entry for that key.
```

### [18] tau · dev-notes/architecture/startup-update-check.md
- heading_path: `['Startup update check']` · 行 1-3 · 41 tok · id `27f756afcedb`

```text
Startup update check

Tau now performs a small, best-effort update check in CLI startup paths that launch the product experience: the Textual TUI and text print mode.
```

### [19] tau · dev-notes/models-dev-catalog.md
- heading_path: `['Generated models.dev catalog', 'Validation']` · 行 88-94 · 84 tok · id `5c80ec3c88e1`

```text
Validation

Focused coverage lives in `tests/test_models_dev.py` and the provider catalog,
configuration, runtime, and thinking suites. It covers Pi-compatible effort
conversion, distinct `max`, full model generation, new-model discovery,
provider aliases, malformed-resource fallback, user preference fallback, and
GLM-5.2 wire behavior.
```

### [20] mini-swe-agent · AGENTS.md
- heading_path: `['Style guide']` · 行 19-44 · 251 tok · id `61127f113b29`

```text
Style guide

1.

Target python 3.10 or higher
2.

Use python with type annotations.

Use `list` instead of `List`.

3.

Use `pathlib` instead of `os.path`.

Use `Path.read_text()` over `with ...open()` constructs.

4.

Use `typer` to add interfaces
5.

Keep code comments to a minimum and only highlight particularly logically challenging things
6.

Do not append to the README unless specifically re
```

### [21] tau · dev-notes/design/pi-event-migration-audit.md
- heading_path: `['Pi-like Event Migration Audit', '2. `tau_agent` layer', 'What changed']` · 行 44-53 · 157 tok · id `e93cad450613`

```text
What changed

- New event model in `src/tau_agent/events.py`:
  - `AgentStartEvent`, `AgentEndEvent`
  - `TurnStartEvent`, `TurnEndEvent`
  - `MessageStartEvent`, `MessageUpdateEvent`, `MessageEndEvent`
  - `ToolExecutionStartEvent`, `ToolExecutionUpdateEvent`, `ToolExecutionEndEvent`
- `MessageDeltaEvent` and `ThinkingDeltaEvent` are gone.

Text/thinking deltas now arrive as `MessageUpdateEvent` 
```

### [22] pi · packages/coding-agent/docs/mcp.md
- heading_path: `['MCP Servers', 'Configure servers']` · 行 68-73 · 110 tok · id `0085c980bc3a`

```text
It lists the server in the system prompt (see [Control tool exposure](#control-tool-exposure)), tool search ranks the server's tools by it, and codemode's `describeNamespace()` returns it.

Without it, the first line of the server instructions is used once the server connects.

Keep personal servers and servers with credentials in the user-level file. Use the project file only for servers the proj
```

### [23] tau · dev-notes/tui-grouped-read-calls.md
- heading_path: `['Grouped file calls in the TUI']` · 行 1-5 · 58 tok · id `6b3aa34babc5`

```text
Grouped file calls in the TUI

Models often request several files in one assistant response. Rendering every
batched `read` as a separate collapsed row made exploration-heavy turns noisy,
even though the calls formed one logical batch.
```

### [24] tau · dev-notes/design/agent-loop.md
- heading_path: `[]` · 行 1-9 · 52 tok · id `04329abe2166`

```text
Tau's pure agent loop is implemented by `run_agent_loop()` in `tau_agent.loop`.

It connects:

```text
transcript + tools + provider
```

and emits agent events while appending new messages to the transcript.
```

### [25] tau · dev-notes/architecture/phase-10-system-prompt.md
- heading_path: `['Why this exists']` · 行 25-27 · 75 tok · id `c76d51a3b987`

```text
Why this exists

Earlier phases added tools, skills, prompt templates, and coding sessions. Before this phase, the CLI used a small local prompt builder that only listed tools. Tau now has one shared prompt assembly layer that can be used by print mode, coding sessions, and later UI/session frontends.
```

### [26] pi · packages/coding-agent/docs/rpc-commands.md
- heading_path: `['RPC Commands', 'Prompting', 'steer']` · 行 46-68 · 255 tok · id `07003247c8dc`

```text
steer

Queue a steering message while the agent is running. It is delivered after the current assistant turn finishes executing its tool calls, before the next LLM call. Skill commands and prompt templates are expanded. Extension commands are not allowed (use `prompt` instead).

```json
{"type": "steer", "message": "Stop and do this instead"}
```

With images:

```json
{"type": "steer", "message":
```

### [27] tau · dev-notes/architecture/phase-20-4-session-export.md
- heading_path: `['How it maps to Pi']` · 行 56-61 · 82 tok · id `eccd440e62f8`

```text
How it maps to Pi

Pi has an HTML session export flow for inspecting conversation state outside the
interactive interface. Tau mirrors the core product behavior while keeping the
implementation smaller: the exporter renders static HTML from the existing
`SessionEntry` JSONL records instead of adding a separate client-side app.
```

### [28] tau · dev-notes/google-stream-completion.md
- heading_path: `['Google stream completion validation', "How this maps to Tau's architecture"]` · 行 28-33 · 82 tok · id `71778300421a`

```text
How this maps to Tau's architecture

The Google-specific terminal-marker rule stays in `tau_ai.google`. It emits the
existing provider-neutral error event, and `tau_ai.stream` converts that into the
canonical assistant error consumed by `tau_agent`. No Google protocol knowledge
is added to the reusable agent loop or coding UI.
```

### [29] pi · packages/coding-agent/examples/extensions/README.md
- heading_path: `['Extension Examples', 'Usage']` · 行 5-13 · 53 tok · id `ac3ce6be35db`

```text
Usage

```bash
# Load an extension with --extension flag
pi --extension examples/extensions/permission-gate.ts

# Or copy to extensions directory for auto-discovery
cp permission-gate.ts ~/.pi/agent/extensions/
```
```

### [30] langgraph · libs/checkpoint-postgres/README.md
- heading_path: `['LangGraph Checkpoint Postgres', '📖 Documentation']` · 行 23-25 · 67 tok · id `a0e266e0fa46`

```text
📖 Documentation

For full documentation, see the [API reference](https://reference.langchain.com/python/langgraph.checkpoint.postgres). For conceptual guides on persistence and memory, see the [LangGraph Docs](https://docs.langchain.com/oss/python/langgraph/overview).
```
