import os
import time
import json
import asyncio
from typing import Dict, Any, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", 10))
CIRCUIT_OPEN_SECS = int(os.getenv("CIRCUIT_OPEN_SECS", 30))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 15))

app = FastAPI(title="MCP Host & Gateway")


class ToolStatus(BaseModel):
    name: str
    url: str
    healthy: bool
    last_checked: float
    circuit_open_until: Optional[float] = None


class HostState:
    def __init__(self) -> None:
        self.tools: Dict[str, ToolStatus] = {}
        self.client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)

    def register(self, name: str, url: str) -> None:
        self.tools[name] = ToolStatus(name=name, url=url, healthy=False, last_checked=0.0)

    def set_unhealthy(self, name: str) -> None:
        status = self.tools[name]
        status.healthy = False
        status.circuit_open_until = time.time() + CIRCUIT_OPEN_SECS

    def can_call(self, name: str) -> bool:
        status = self.tools[name]
        if status.circuit_open_until and time.time() < status.circuit_open_until:
            return False
        return True

    async def heartbeat_once(self) -> None:
        for name, status in self.tools.items():
            try:
                r = await self.client.get(f"{status.url}/health")
                status.healthy = r.status_code == 200 and r.json().get("ok", False) is True
                status.last_checked = time.time()
            except Exception:
                status.healthy = False
                status.last_checked = time.time()


host = HostState()


class ChatRequest(BaseModel):
    message: str
    tool: Optional[str] = None
    inject_error: Optional[str] = None
    tool_input: Dict[str, Any] = {}


@app.on_event("startup")
async def on_startup():
    # Auto-register tools from MCP_SERVERS; map basic names to URLs.
    # Expect env like: MCP_REGISTRY_JSON='{"rag.retrieve":"http://localhost:7001","papers.search":"http://localhost:7002","papers.fetch":"http://localhost:7002","notes.read":"http://localhost:7003","notes.write":"http://localhost:7003","db.query":"http://localhost:7004"}'
    registry_json = os.getenv("MCP_REGISTRY_JSON")
    if registry_json:
        registry = json.loads(registry_json)
        for name, base in registry.items():
            host.register(name, base)
    # Heartbeat task
    async def _hb():
        while True:
            await host.heartbeat_once()
            await asyncio.sleep(HEARTBEAT_INTERVAL)
    app.state.hb = asyncio.create_task(_hb())


@app.on_event("shutdown")
async def on_shutdown():
    hb: asyncio.Task = app.state.hb
    hb.cancel()
    try:
        await hb
    except Exception:
        pass
    await host.client.aclose()


@app.get("/tools")
async def list_tools() -> List[ToolStatus]:
    return list(host.tools.values())


@app.post("/chat")
async def chat(req: ChatRequest):
    # Minimal orchestration: route to specified tool or choose a default (rag.retrieve)
    tool = req.tool or "rag.retrieve"
    if tool not in host.tools:
        raise HTTPException(status_code=400, detail=f"tool not registered: {tool}")
    status = host.tools[tool]
    if not status.healthy or not host.can_call(tool):
        raise HTTPException(status_code=503, detail=f"tool unavailable: {tool}")

    # Prepare invoke payload according to contracts
    payload = {
        "tool": tool,
        "input": req.tool_input or {"query": req.message},
        "inject_error": req.inject_error,
    }

    try:
        r = await host.client.post(f"{status.url}/invoke", json=payload)
        if r.status_code >= 500:
            host.set_unhealthy(tool)
            raise HTTPException(status_code=502, detail=f"upstream error {r.status_code}")
        data = r.json()
        if "error" in data:
            return {"ok": False, "tool": tool, "error": data["error"], "details": data.get("details")}
        return {"ok": True, "tool": tool, "data": data}
    except httpx.ConnectError:
        host.set_unhealthy(tool)
        raise HTTPException(status_code=502, detail="connect error")
    except httpx.ReadTimeout:
        host.set_unhealthy(tool)
        raise HTTPException(status_code=504, detail="timeout")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
