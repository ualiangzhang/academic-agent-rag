import os
from typing import Any, Dict
from fastapi import FastAPI
from pydantic import BaseModel
from .common import get_validator, maybe_inject_error

app = FastAPI(title="MCP - papers.*")
search_validator = get_validator("papers.search.schema.json")
fetch_validator = get_validator("papers.fetch.schema.json")


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
async def invoke(body: InvokeBody):
    maybe_inject_error(body.inject_error)
    if body.tool == "papers.search":
        errors = sorted(search_validator.iter_errors(body.input), key=lambda e: e.path)
        if errors:
            return {"error": "invalid_input", "details": [e.message for e in errors]}
        items = [{"title": "stub", "url": "https://example.com", "source": "arxiv"}]
        return {"items": items, "trace_id": body.input.get("trace_id"), "run_id": body.input.get("run_id")}
    if body.tool == "papers.fetch":
        errors = sorted(fetch_validator.iter_errors(body.input), key=lambda e: e.path)
        if errors:
            return {"error": "invalid_input", "details": [e.message for e in errors]}
        return {"text": "stub text", "metadata": {"pages": 1}, "doc_id": body.input.get("doc_id")}
    return {"error": "unknown_tool"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 7002)))
