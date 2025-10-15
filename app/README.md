# MCP Host & Gateway

Responsibilities:
- Read registry (`MCP_REGISTRY_JSON`), register tool servers, and perform periodic heartbeats.
- Expose `/tools` for health/metadata and `/chat` to bridge requests to tools.
- Provide isolation with circuit breaking on upstream failures/timeouts.

Environment:
- `HEARTBEAT_INTERVAL` seconds (default 10)
- `CIRCUIT_OPEN_SECS` seconds (default 30)
- `REQUEST_TIMEOUT` seconds (default 15)
- `MCP_REGISTRY_JSON` mapping tool→base URL

Run locally:
- Start tool servers on 7001–7004.
- Launch host: `uvicorn app.main:app --reload`
- Check `/tools` returns health and `/chat` can call a tool.
