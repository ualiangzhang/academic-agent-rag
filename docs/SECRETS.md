# Secrets Management and Rotation

This document describes how secrets are sourced, injected, rotated, and audited.

## Secret Types

- LLM API keys (e.g., OpenAI, Anthropic)
- Vector DB credentials (e.g., Postgres)
- Cache credentials (e.g., Redis)
- Third‑party API keys (e.g., arXiv/Crossref/Semantic Scholar if applicable)

## Sourcing and Storage

- Local/CI: use CI secret store or .env for local only (non‑prod values)
- Staging/Prod: use a cloud secret manager; never store secrets in repo

## Injection

- Local: `.env` loaded by process startup
- CI: per‑job secret variables injected into environment
- Staging/Prod: container orchestrator pulls from secret manager and injects as env vars

## Rotation

- Keys must be rotatable without code changes
- Maintain a runbook for rotation, including rollback steps
- Set maximum secret age and rotate on schedule or upon incident

## Audit & Monitoring

- Log secret usage metadata (service, scope), never values
- Alert on missing/invalid secrets
- Restrict access based on least privilege; audit access logs periodically

## Developer Guidance

- Do not print secrets in logs
- Do not commit `.env`
- Use placeholder values in examples
