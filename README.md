# Academic Agent RAG – MCP‑Native, Orchestrated, and Verifiable

A modern, MCP‑native AI agent system for academic research that combines Retrieval‑Augmented Generation (RAG) with robust tool orchestration, planner/verifier loops, and layered memory/context handling. This redesign is framework‑agnostic and integrates popular agent frameworks (LangChain/LangGraph, CrewAI, AutoGen) behind a single protocol boundary via Model Context Protocol (MCP).

---

## Why this redesign

- Unify tools behind MCP so agents can call any capability (APIs, DBs, file systems, search, RAG) via a single protocol.
- Add a planner/verifier loop for reliability: plans are generated, executed, and verified with corrective feedback.
- Provide strong memory/context handling to keep conversations grounded and efficient at scale.
- Remain framework‑flexible: use LangGraph for control flow, reuse LangChain Tools and retrievers, plug in CrewAI or AutoGen agents where helpful.

---

## High‑Level Architecture

```mermaid
flowchart TD
  User[User / Client] -->|chat/query| Gateway
  subgraph Core Agent Runtime (MCP Host)
    Gateway --> Planner
    Planner -->|Plan| Orchestrator
    Orchestrator -->|Select Tool| ToolRouter
    ToolRouter --> MCPServers
    MCPServers -->|Tool Result| Orchestrator
    Orchestrator --> Verifier
    Verifier -->|Critique/Approve| Orchestrator
    Orchestrator -->|Action/Final| Gateway
  end
  subgraph Memory & Context
    Episodic[(Vector Store)]
    SemanticCache[(Semantic Cache)]
    Profiles[(User Profiles)]
    Summaries[(Conversation Summaries)]
  end
  Gateway <-->|retrieve/store| Memory & Context
  Orchestrator <-->|retrieve/store| Memory & Context
  Verifier <-->|evidence| Memory & Context
```

- MCP Host: Runs the model and routes MCP tool calls. Examples: `modelcontextprotocol` servers, local adapters, or IDE‑embedded tools.
- Planner (LLM‑driven): Builds a structured plan (steps, tools, expected evidence, stop criteria).
- Orchestrator (LangGraph): Executes plan, manages retries/branching, handles memory I/O.
- Verifier (LLM‑driven + rules): Scores outputs vs. plan/evidence; can request refinements or re‑planning.
- Memory: Short‑term scratchpad, episodic vector memory, semantic cache, user profile/constraints, rolling conversation summaries.

---

## Tool Orchestration (via MCP + adapters)

- Primary interface: MCP tools (search, RAG retrieval, file I/O, HTTP, code, DB). Tools are exposed as MCP servers; the agent calls them uniformly.
- Framework adapters:
  - LangChain Tools/Retrievers are wrapped as MCP tools so any LangChain asset is callable through MCP.
  - CrewAI or AutoGen agents are wrapped as higher‑level MCP tools when you want sub‑agents to solve subtasks.
  - Non‑LLM utilities (e.g., `arxiv`, `crossref`, `semantic scholar`, `postgres/pgvector`, `s3`, `fs`) are implemented as first‑class MCP tools.
- Routing Policy:
  - Static capability map (name → MCP server/tool signature).
  - Optional embedding‑based router to pick tools based on user intent.
  - Safety rules: deny‑list, rate limits, and argument validation per tool.

---

## Planner / Verifier Loops (reliable agenting)

- Planner produces a plan with: goals, steps, tools per step, evidence required, stop conditions.
- Orchestrator executes each step, gathers results/evidence, and updates the scratchpad.
- Verifier evaluates each step output for correctness, grounding, and policy compliance; may:
  - request a retry with adjusted parameters
  - call additional tools for evidence
  - escalate back to Planner for re‑planning
- Termination: Verifier approves final answer; Orchestrator composes citations and rationale from evidence.

Minimal LangGraph sketch for the loop (illustrative):

```python
from langgraph.graph import StateGraph, END

class AgentState(dict):
    ...  # fields: plan, step_idx, scratchpad, evidence, messages

graph = StateGraph(AgentState)

def planner_node(state):
    if not state.get("plan"):
        state["plan"] = llm_plan(state["messages"])  # returns structured plan
    return state

def exec_node(state):
    step = state["plan"].steps[state["step_idx"]]
    result = call_mcp_tool(step.tool, step.args)
    state["scratchpad"].append(result)
    state["evidence"].extend(extract_evidence(result))
    return state

def verifier_node(state):
    verdict = llm_verify(state)
    if verdict.action == "retry":
        state["plan"].steps[state["step_idx"]] = verdict.adjusted_step
        return state  # go back to exec
    if verdict.action == "replan":
        state["plan"] = verdict.new_plan
        state["step_idx"] = 0
        return state
    state["step_idx"] += 1
    if state["step_idx"] >= len(state["plan"].steps):
        return END
    return state

# wire nodes
graph.add_node("plan", planner_node)
graph.add_node("exec", exec_node)
graph.add_node("verify", verifier_node)

graph.set_entry_point("plan")
graph.add_edge("plan", "exec")
graph.add_edge("exec", "verify")
graph.add_conditional_edges("verify", lambda s: "exec" if s.get("retry") else (END if s.get("done") else "exec"))
app = graph.compile()
```

---

## Memory and Context Handling

Layered approach:

- Short‑term scratchpad: chain‑of‑thought artifacts kept private; distilled into concise working notes for subsequent steps.
- Episodic memory (vector store): chunks of prior interactions, retrieved by similarity (pgvector/FAISS/Chroma). Used for grounding and continuity.
- Semantic cache: memoize expensive tool+prompt pairs; cache hits bypass LLM/tool calls and reduce latency/cost.
- Conversation summaries: rolling summaries to fit within context window; periodically regenerate higher‑level summaries.
- User profile/context: preferences, roles, constraints, allowed tools; checked at plan time and by Verifier.

Recommended stores (choose one per environment):

- Vector: pgvector (Postgres), Chroma, FAISS.
- Cache: Redis, SQLite, or `langchain-community` in‑mem for dev.
- Metadata: SQLite/Postgres for plans, runs, artifacts, and audit.

---

## Framework Interop

- LangChain: RAG retrievers, document loaders, tools; memories (ConversationBuffer, VectorStoreRetrieverMemory) plugged into the Memory layer.
- LangGraph: execution backbone (graph control flow, retries, branches, check‑pointing).
- CrewAI: sub‑agents for specialized tasks (e.g., LiteratureSurveyCrew) wrapped as MCP tools for orchestrated calls.
- AutoGen: multi‑agent dialogues used as a single MCP tool when a debate/critique is beneficial; the Verifier can act as a judge.

All framework calls occur behind MCP where possible. If a framework lacks MCP‑native bindings, we expose its capability as an MCP tool via a thin adapter server.

---

## Example MCP Tools in this project

- `rag.retrieve`: semantic retrieval over your corpus (embeddings + vector DB), returns chunks + citations.
- `papers.search`: internet discovery (arXiv, CrossRef, Semantic Scholar) returning metadata/links.
- `papers.fetch`: fetch and parse PDFs; extract text and metadata.
- `notes.write` / `notes.read`: persistent notes for iterative research.
- `db.query`: SQL over Postgres/pgvector for advanced filters.

Each tool declares: name, description, input schema, output schema, rate limits, safety policy, and test vectors.

---

## Configuration

All via environment variables (12‑factor):

- `LLM_PROVIDER` and credentials (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).
- `EMBEDDINGS_MODEL` and `LLM_MODEL` identifiers.
- `VECTOR_STORE` (`pgvector|chroma|faiss`) and connection details.
- `CACHE_URL` for Redis/SQLite path.
- `MCP_SERVERS` list (URLs or local sockets) to auto‑register.
- `POLICY_MODE` (`strict|permissive`) for tool gating.

---

## Getting Started (local dev)

```bash
# Python env
python3.12 -m venv venv && source venv/bin/activate
pip install -U pip
pip install modelcontextprotocol langchain langgraph crewai pyautogen chromadb faiss-cpu psycopg[binary] pydantic fastapi uvicorn python-dotenv

# (Optional) Postgres + pgvector
# docker run --name pgvector -e POSTGRES_PASSWORD=dev -p 5432:5432 ankane/pgvector

# Run the MCP host + API gateway (example FastAPI)
uvicorn app.main:app --reload
```

Notes:
- This repo is now cloud‑agnostic; you can deploy anywhere (local, VM, Kubernetes). Infra as code previously in this repo was removed.
- Bring your own models/providers; default config targets widely available APIs.

---

## Repository Layout (proposed)

| Path | Description |
|------|-------------|
| `/app` | API gateway (FastAPI) and MCP host bootstrap |
| `/agents` | Planner, Orchestrator (LangGraph), Verifier nodes |
| `/tools/mcp_servers` | MCP tool servers (RAG, papers, notes, db) |
| `/adapters` | Wrappers for LangChain, CrewAI, AutoGen as MCP tools |
| `/memory` | Vector store, cache, summaries, profile store |
| `/configs` | Tool manifests, safety policies, routing configs |
| `/tests` | Unit/integration tests and tool test vectors |

This layout is aspirational; components will be introduced incrementally.

---

## Security & Safety

- Tool allow‑list and schema validation at the router.
- Verifier enforces grounding: answers must cite retrieved evidence or state uncertainty.
- Rate‑limit and budget guardrails per tool and per user.
- Red‑team prompts and test vectors for critical tools.

---

## Migration Notes

- Removed legacy AWS‑specific directories: `academic-agent-infra/` and `lambda/`.
- Internet discovery now lives behind `papers.search` and `papers.fetch` MCP tools rather than a Lambda.
- RAG is provider‑agnostic: use pgvector/FAISS/Chroma; swap embeddings/models via config.

---

## Roadmap

- [ ] Implement baseline MCP servers: `rag.retrieve`, `papers.search`, `notes.write`.
- [ ] Add LangGraph execution with retries/check‑pointing.
- [ ] Implement Verifier with rule‑based + LLM hybrid scoring.
- [ ] Add semantic cache and conversation summarizer.
- [ ] Provide examples for CrewAI and AutoGen sub‑agent adapters.

---

## License

MIT

---

## 设计完整性与可行性评估

本节从架构覆盖面、关键非功能性需求、风险与缓解、以及落地路径四方面评估当前设计。

### 覆盖面（已具备）
- MCP 统一工具面：通过 MCP 将检索、抓取、DB、文件、HTTP 等能力标准化，便于多框架复用。
- Orchestration：使用 LangGraph 进行计划/执行/验证的图式编排，支持重试与分支。
- Planner/Verifier 循环：以 LLM+规则混合的 Verifier 形成闭环，提高可靠性与可解释性。
- Memory/Context：短期 scratchpad、向量化 episodic memory、语义缓存、profile 与会话摘要分层。
- 框架互操作：LangChain 工具与检索器、CrewAI/AutoGen 子智能体均可经由 MCP 适配。
- 安全与治理：工具白名单、参数校验、速率/预算限制、证据引用约束。

### 关键待完成项（可行且建议尽快落地）
- MCP Host 与工具注册自发现：实现 `MCP_SERVERS` 自动注册与心跳；提供健康检查端点。
- 基线工具实现与契约测试：`rag.retrieve`、`papers.search`/`papers.fetch`、`notes.*`、`db.query` 的输入/输出模式与示例测试向量。
- Orchestrator Checkpointing：为 LangGraph 增加运行态持久化（SQLite/Postgres），支持断点续跑与审计。
- 观测与追踪：统一 run_id/trace_id，接入 OpenTelemetry；为每个工具记录延迟、成功率与 token 成本。
- 配置与密钥管理：`.env` 本地、环境变量注入与云密钥管理占位（可选）。
- E2E 验收流：从用户 query → 工具路由 → 结果验证 → 引用/证据输出的端到端测试。

### 可行性结论
- 依赖均为成熟生态（LangGraph、LangChain、CrewAI、AutoGen、pgvector/FAISS/Chroma、FastAPI、Redis/SQLite）。
- MCP Python 实现（`modelcontextprotocol`）活跃且持续演进；通过适配可平滑接入现有工具与服务。
- 计算/存储成本可控：语义缓存与 evidence‑based 验证可显著降低重复调用；向量库可按规模平滑扩展。

### 风险与缓解
- 工具误用/越权：严格的工具 schema 校验与 allow‑list，增加离线契约测试。
- 事实性错误：Verifier 强制“证据对齐”，无证据时要求不确定性回答；必要时二次检索。
- 复杂度提升：以最小可用集合启动（3–4 个工具 + 基线图），逐步引入子智能体与高级路由。
- 供应商变化：保持 MCP 抽象与可替换实现，避免绑定到单一 LLM/向量库。

---

## 开发步骤与细节（分阶段落地）

> 建议里程碑：M0 基线可对话；M1 E2E 验收与观测；M2 高级路由与子智能体；M3 安全与规模化。

### 阶段 M0：最小可用系统
1) 初始化与依赖
```bash
python3.12 -m venv venv && source venv/bin/activate
pip install -U pip
pip install modelcontextprotocol langchain langgraph crewai pyautogen chromadb faiss-cpu psycopg[binary] pydantic fastapi uvicorn python-dotenv opentelemetry-api opentelemetry-sdk
```
2) 目录搭建（见“Repository Layout (proposed)”）：创建 `/app` `/agents` `/tools/mcp_servers` `/memory` `/configs`。
3) 实现 MCP 基线工具（最小形态）
- `tools/mcp_servers/rag_server.py`：基于 Chroma/FAISS 的本地向量检索，返回 `[text, source, score]`。
- `tools/mcp_servers/papers_server.py`：封装 arXiv/CrossRef/Semantic Scholar 的搜索与 PDF 链接解析。
- `tools/mcp_servers/notes_server.py`：基于本地 SQLite/文件的简单读写。
- 为每个工具提供 JSON schema 与 3–5 个测试向量（输入/输出样例）。
4) MCP Host 引导与注册
- `/app/main.py`：FastAPI 暴露 `/chat`，在启动时按 `MCP_SERVERS` 列表注册工具（支持本地进程/子进程/HTTP）。
5) LangGraph 编排骨架
- `/agents/graph.py`：实现 planner → exec → verifier 的基本节点，支持单步重试与最终汇总。
6) 本地运行
```bash
uvicorn app.main:app --reload
```

### 阶段 M1：E2E、观测与持久化
1) Checkpointing：为 Orchestrator 增加 SQLite/Postgres 持久化（运行状态、证据、最终答案）。
2) OpenTelemetry：追踪 `run_id`、工具调用 span、LLM 调用指标；输出到控制台或 OTLP 收集器。
3) 语义缓存：为“LLM 提示+工具参数”对作键，命中直接返回并标注缓存来源。
4) E2E 测试：pytest + httpx 调用 `/chat`，断言包含证据引用与稳定延迟区间。

### 阶段 M2：高级路由与子智能体
1) 工具路由策略：意图分类 + 嵌入相似度二阶段；回退静态映射。
2) 子智能体（可选）：将 CrewAI/AutoGen 工作流封装为 MCP 工具（如 `survey.solve`），由 Orchestrator 按需调用。
3) 计划质量提升：Planner 输出“期望证据”模板，Verifier 严格对齐校验。

### 阶段 M3：安全、治理与规模化
1) 策略中心：`/configs/policy.yml` 定义角色、工具配额、输入长度上限、PII 处理策略。
2) 成本与配额：按用户/会话限流；大文档检索走批/流式；向量库分层（热/冷）。
3) 部署：容器化（uvicorn/gunicorn），可接入 K8s 或无服务器平台；外置 Redis/pgvector。

---

## 测试策略
- 单元测试：工具契约（输入/输出/错误分支）、Planner/Verifier 提示与解析。
- 集成测试：编排路径（重试/回退/缓存命中）、多工具序列。
- E2E：用户到答案，校验证据与安全策略；对关键查询建立基准用例与阈值。

## 版本与发布
- 语义化版本（SemVer）；在 `CHANGELOG.md` 记录功能与破坏性变更。
- 预发布分支 `release/*`，通过一套最小 e2e 用例门禁。

