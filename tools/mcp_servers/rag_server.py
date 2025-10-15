import os
from typing import Any, Dict
from fastapi import FastAPI, Request
from pydantic import BaseModel
from .common import get_validator, ConcurrencyGate, maybe_inject_error

app = FastAPI(title="MCP - rag.retrieve")
validator = get_validator("rag.retrieve.schema.json")
concurrency = ConcurrencyGate()


class InvokeBody(BaseModel):
    tool: str
    input: Dict[str, Any]
    inject_error: str | None = None


@app.on_event("startup")
async def on_startup():
    app.state.ready = True


@app.on_event("shutdown")
async def on_shutdown():
    app.state.ready = False


@app.get("/health")
async def health():
    return {"ok": True, "stage": os.getenv("APP_STAGE", "local")}


@app.post("/invoke")
async def invoke(body: InvokeBody, request: Request):
    if body.tool != "rag.retrieve":
        return {"error": "unknown_tool"}
    maybe_inject_error(body.inject_error)
    errors = sorted(validator.iter_errors(body.input), key=lambda e: e.path)
    if errors:
        return {"error": "invalid_input", "details": [e.message for e in errors]}
    # Stub output adhering to x-output schema
    matches = [
        {"text": "stub chunk", "source": "stub://source", "score": 0.9, "doc_id": "doc_stub"}
    ]
    return {"matches": matches, "trace_id": body.input.get("trace_id"), "run_id": body.input.get("run_id")}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 7001)))
