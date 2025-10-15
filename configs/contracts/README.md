# MCP Contracts – Summary and Acceptance

This folder contains baseline contracts for MCP tools and their test vectors.

## Tools
- rag.retrieve
- papers.search
- papers.fetch
- notes.read
- notes.write
- db.query

## Contract Elements
- Input/Output JSON Schema per tool
- Error model: codes, retryability, timeouts
- Rate limits and idempotency
- Audit fields: `trace_id` and `run_id`

## Test Vectors
- Each tool has ≥3 JSONL inputs under `../test_vectors/` to validate parsing and behavior.

## Acceptance
- Contracts reviewed and approved → version frozen as v1 (tracked in CHANGELOG)
- Changes follow configuration change control with migration guidance
