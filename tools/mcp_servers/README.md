# MCP Servers (FastAPI)

Each server is an independent process exposing:
- `GET /health` ready check
- `POST /invoke` schema-validated tool invocation with optional error injection (`inject_error=timeout|404|429|503`)
- startup/shutdown hooks

Servers:
- rag_server.py (port 7001)
- papers_server.py (port 7002)
- notes_server.py (port 7003)
- db_server.py (port 7004)
 - ingest_server.py (port 7005)

Concurrency and limits:
- Gate concurrency via `MAX_CONCURRENCY` env var (default 8)
- Respect per-tool timeouts/rate limits defined in contracts

Run locally:
- Use `python tools/mcp_servers/<server>.py` or run under `uvicorn`.
- Verify `/health` returns `{ ok: true }`.
