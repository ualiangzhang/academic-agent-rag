from __future__ import annotations
import os
import uuid
from typing import Any, Dict, List

from dataclasses import dataclass, field
from fastapi import HTTPException
import httpx

from .persistence import save_run, load_run, RunRecord

# Placeholder for LangGraph-like node execution

@dataclass
class PlanStep:
    tool: str
    args: Dict[str, Any]


@dataclass
class Plan:
    steps: List[PlanStep]


@dataclass
class AgentState:
    run_id: str
    plan: Plan
    step_idx: int = 0
    scratchpad: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "running"  # running|completed|failed
    error: str | None = None


async def planner(messages: List[Dict[str, str]]) -> Plan:
    # Minimal planner: route to rag.retrieve with the last user message
    last_user = next((m for m in reversed(messages) if m["role"] == "user"), None)
    query = last_user["content"] if last_user else ""
    return Plan(steps=[PlanStep(tool="rag.retrieve", args={"query": query, "top_k": 3})])


async def exec_step(state: AgentState, client: httpx.AsyncClient, registry: Dict[str, str]) -> AgentState:
    step = state.plan.steps[state.step_idx]
    base = registry.get(step.tool)
    if not base:
        raise HTTPException(status_code=400, detail=f"tool not registered: {step.tool}")
    payload = {"tool": step.tool, "input": step.args}
    try:
        r = await client.post(f"{base}/invoke", json=payload)
        data = r.json()
        if "error" in data:
            state.error = data["error"]
            raise HTTPException(status_code=502, detail=data["error"])
        state.scratchpad.append(data)
        # naive evidence collection
        state.evidence.append({"tool": step.tool, "data": data})
        return state
    except Exception as e:
        state.error = str(e)
        raise


async def verifier(state: AgentState) -> Dict[str, Any]:
    # Minimal verifier: accept if we have at least one evidence item
    if not state.evidence:
        return {"action": "retry"}
    return {"action": "approve"}


async def run_orchestrator(messages: List[Dict[str, str]], registry: Dict[str, str], resume_run_id: str | None = None) -> AgentState:
    run_id = resume_run_id or uuid.uuid4().hex
    if resume_run_id:
        rec = load_run(resume_run_id)
        if rec:
            state_dict = rec.state
            # naive reconstruction
            plan = Plan(steps=[PlanStep(**s) for s in state_dict["plan"]["steps"]])
            state = AgentState(run_id=rec.run_id, plan=plan, step_idx=state_dict["step_idx"], scratchpad=state_dict["scratchpad"], evidence=state_dict["evidence"], status=rec.status, error=rec.error)
        else:
            # cannot resume; start fresh
            plan = await planner(messages)
            state = AgentState(run_id=run_id, plan=plan)
    else:
        plan = await planner(messages)
        state = AgentState(run_id=run_id, plan=plan)

    async with httpx.AsyncClient(timeout=int(os.getenv("REQUEST_TIMEOUT", 15))) as client:
        while state.step_idx < len(state.plan.steps):
            try:
                # checkpoint for rollback
                checkpoint = {
                    "step_idx": state.step_idx,
                    "scratchpad": list(state.scratchpad),
                    "evidence": list(state.evidence),
                }
                state = await exec_step(state, client, registry)
                v = await verifier(state)
                if v.get("action") == "retry":
                    # single retry then skip with rollback
                    try:
                        state = await exec_step(state, client, registry)
                    except Exception:
                        state.step_idx = checkpoint["step_idx"]
                        state.scratchpad = checkpoint["scratchpad"]
                        state.evidence = checkpoint["evidence"]
                        state.step_idx += 1
                        save_run(RunRecord(run_id=state.run_id, status=state.status, state=state.__dict__, error=state.error))
                        continue
                elif v.get("action") == "rollback":
                    state.step_idx = checkpoint["step_idx"]
                    state.scratchpad = checkpoint["scratchpad"]
                    state.evidence = checkpoint["evidence"]
                    state.step_idx += 1
                    save_run(RunRecord(run_id=state.run_id, status=state.status, state=state.__dict__, error=state.error))
                    continue
                # approve by default
                state.step_idx += 1
                save_run(RunRecord(run_id=state.run_id, status=state.status, state=state.__dict__, error=state.error))
            except Exception as e:
                # persist error and allow resume
                save_run(RunRecord(run_id=state.run_id, status="running", state=state.__dict__, error=str(e)))
                break
        if state.step_idx >= len(state.plan.steps):
            state.status = "completed"
            save_run(RunRecord(run_id=state.run_id, status=state.status, state=state.__dict__, error=None))
        return state
