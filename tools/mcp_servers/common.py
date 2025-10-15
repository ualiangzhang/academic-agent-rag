import os
import json
import asyncio
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import HTTPException
from jsonschema import Draft202012Validator

CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "configs" / "contracts"


@lru_cache(maxsize=64)
def load_schema(schema_filename: str) -> Dict[str, Any]:
    schema_path = CONTRACTS_DIR / schema_filename
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_validator(schema_filename: str) -> Draft202012Validator:
    schema = load_schema(schema_filename)
    return Draft202012Validator(schema)


class ConcurrencyGate:
    def __init__(self, env_var: str = "MAX_CONCURRENCY", default: int = 8) -> None:
        max_concurrency = int(os.getenv(env_var, default))
        self._sem = asyncio.Semaphore(max_concurrency)

    async def __aenter__(self):
        await self._sem.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self._sem.release()


def maybe_inject_error(inject: Optional[str]) -> None:
    if not inject:
        return
    if inject.lower() == "timeout":
        raise HTTPException(status_code=504, detail="Injected timeout")
    if inject == "404":
        raise HTTPException(status_code=404, detail="Injected not found")
    if inject == "429":
        raise HTTPException(status_code=429, detail="Injected rate limit")
    if inject == "503":
        raise HTTPException(status_code=503, detail="Injected backend unavailable")


def redact(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if len(value) <= 6:
        return "***"
    return value[:3] + "***" + value[-3:]
