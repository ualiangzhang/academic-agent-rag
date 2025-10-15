# Orchestrator Integration Tests (Plan→Exec→Verify)

Scenarios:
1) Success path: registry has rag.retrieve server; planner creates one step; exec returns data; verifier approves; state completes.
2) Retry then rollback→skip: server returns error on first call; second attempt fails; state rolls back to checkpoint and skips the step; run persists intermediate state; completes or ends with remaining steps.
3) Resume: run fails mid-way; `resume_run_id` rehydrates state and continues.

Acceptance:
- State persisted in `orchestrator.sqlite`; steps and evidence recorded.
- Success and error scenarios documented with expected transitions.
