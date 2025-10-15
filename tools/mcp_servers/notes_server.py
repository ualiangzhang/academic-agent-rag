import os
from typing import Any, Dict
from fastapi import FastAPI
from pydantic import BaseModel
from .common import get_validator, maybe_inject_error

app = FastAPI(title="MCP - notes.*")
read_validator = get_validator("notes.read.schema.json")
write_validator = get_validator("notes.write.schema.json")


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
    if body.tool == "notes.read":
        errors = sorted(read_validator.iter_errors(body.input), key=lambda e: e.path)
        if errors:
            return {"error": "invalid_input", "details": [e.message for e in errors]}
        return {"items": [{"key": body.input.get("key", "q"), "text": "stub note"}]}
    if body.tool == "notes.write":
        errors = sorted(write_validator.iter_errors(body.input), key=lambda e: e.path)
        if errors:
            return {"error": "invalid_input", "details": [e.message for e in errors]}
        return {"ok": True, "version": "v1"}
    return {"error": "unknown_tool"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 7003)))
