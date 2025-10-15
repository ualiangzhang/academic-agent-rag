# Configuration Layering and Precedence

This document defines configuration sources, layering, and precedence for the project.

## Sources

- Base defaults: Checked-in defaults for local development.
- Environment variables: Primary override mechanism across environments.
- Secrets: Injected via secret manager or CI secret store, never committed.
- Runtime flags: Feature gates and budgets toggled at startup.

## Layering (highest precedence last)

1. Base defaults
2. Environment-specific overrides (e.g., staging/prod files or env)
3. Secrets from secret manager/CI vault
4. Runtime flags

## Environment Variables Overview

- LLM/Embeddings: provider, model IDs, API keys
- Vector store: backend selector and connection string
- Cache: backend URL and policy (TTL, size)
- MCP registry: list of tool servers and health configuration
- Policy: strict/permissive tool gating and budgets

See `configs/ENV_VARS.md` and `.env.example` for concrete names and examples.

## Validation

- Validate presence, type, and format at process start.
- Fail fast with actionable error messages.
- Log effective configuration with secrets redacted.

## Example Precedence Rules

- `LLM_MODEL` from env overrides base default; secret keys must come exclusively from secret manager in non-local environments.
- `VECTOR_DB_URL` must be present for pgvector; optional for FAISS/Chroma.
- `MCP_SERVERS` must resolve to healthy servers at startup or host should degrade gracefully with warnings.

## Change Management

- All configuration changes require code review.
- Document material changes in CHANGELOG and link to PR.
- Provide migration guidance for breaking configuration updates.
