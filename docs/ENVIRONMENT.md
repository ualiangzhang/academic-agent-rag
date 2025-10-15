# Environment Matrix

This document defines consistent environments and configuration layering.

## Environments

| Env | Purpose | Python | Dependencies | Env Var Injection | Secrets | Vector Store | Cache | Telemetry |
|-----|---------|--------|--------------|-------------------|---------|--------------|-------|-----------|
| Local | Dev on laptop | 3.12.x | venv + pinned reqs | .env file + shell | .env only (non-prod keys) | FAISS/Chroma | SQLite/Redis | Console + OTLP optional |
| CI | Build/test | 3.12.x | ephemeral venv | CI secrets store | CI secrets | FAISS (ephemeral) | SQLite | OTLP exporter (test) |
| Staging | Pre-prod | 3.12.x | container image | env vars via orchestrator | Secret manager | pgvector | Redis | OTLP + dashboards |
| Production | Live | 3.12.x | container image | env vars via orchestrator | Secret manager | pgvector (HA) | Redis (HA) | OTLP + SLO alerts |

## Configuration Layering

1. Base defaults (checked in)
2. Environment overrides (staging/prod)
3. Secrets (never committed)
4. Runtime flags (feature gates, budgets)

## Health & Readiness

- All services expose health/readiness endpoints.
- MCP servers must provide registration, health, and graceful shutdown hooks.
