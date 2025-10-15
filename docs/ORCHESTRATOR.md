# Orchestrator (plan → exec → verify)

This document describes the orchestrator graph, transitions, and persistence model.

## Graph and Transitions
- plan: create `Plan` from messages
- exec: invoke current step tool and collect scratchpad + evidence
- verify: approve, retry once, or skip; on approval, advance step
- terminal: when `step_idx == len(steps)`, mark `completed`

## Error Handling
- On exec error: persist state with `status=running` and `error`; allow resume
- Retry policy: single retry then skip

## Persistence
- SQLite file `orchestrator.sqlite`
- Table `runs(run_id, status, state_json, error)`
- Saved after each step or error

## Resume
- `resume_run_id` loads persisted state and continues; if not found, start fresh

## Integration
- Registry maps tool name → base URL; host provides client and timeouts
- Minimal planner chooses `rag.retrieve` on the last user message

## Acceptance
- Integration tests cover success, retry/skip, and resume
- Evidence collected per step; final state is `completed` or resumable
