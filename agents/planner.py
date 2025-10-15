from __future__ import annotations
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List
import yaml

POLICY_PATH = os.path.join(os.path.dirname(__file__), "..", "configs", "policy", "PLANNER_POLICY.yaml")


@dataclass
class PlanStep:
    tool: str
    params: Dict[str, Any]
    expected_evidence: List[str] = field(default_factory=list)


@dataclass
class Plan:
    goal: str
    steps: List[PlanStep]
    stop_conditions: List[str]
    risks: Dict[str, str]
    budgets: Dict[str, int]
    role: str
    rubric: Dict[str, Any]


def load_policy() -> Dict[str, Any]:
    with open(POLICY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def clamp_to_policy(plan: Plan, policy: Dict[str, Any]) -> Plan:
    role_caps = policy["roles"].get(plan.role, policy["roles"]["user"])
    # Filter tools by allow-list
    allowed = set(role_caps["allowed_tools"])
    filtered_steps = [s for s in plan.steps if s.tool in allowed]
    # Enforce max steps
    if len(filtered_steps) > role_caps["max_steps"]:
        filtered_steps = filtered_steps[: role_caps["max_steps"]]
    plan.steps = filtered_steps
    # Budgets
    plan.budgets = {
        "max_steps": role_caps["max_steps"],
        "max_budget_tokens": role_caps["max_budget_tokens"],
        "max_wallclock_seconds": role_caps["max_wallclock_seconds"],
    }
    return plan


def build_plan(messages: List[Dict[str, str]], role: str = "user") -> Plan:
    # Minimal heuristic planner
    user_msg = next((m for m in reversed(messages) if m["role"] == "user"), {"content": ""})
    goal = user_msg["content"]
    steps = [
        PlanStep(tool="rag.retrieve", params={"query": goal, "top_k": 5}, expected_evidence=["matches>=3"]),
    ]
    policy = load_policy()
    plan = Plan(
        goal=goal,
        steps=steps,
        stop_conditions=["evidence_sufficient", "budget_exhausted", "no_more_actions"],
        risks=policy.get("risk_matrix", {}),
        budgets={},
        role=role,
        rubric={
            "consistency": {"score": 4, "reason": "Matches query and allowed tools"},
            "grounding": {"score": 4, "reason": "Requests citations via rag"},
            "efficiency": {"score": 4, "reason": "Single-step baseline"},
        },
    )
    plan = clamp_to_policy(plan, policy)
    return plan


def plan_to_dict(plan: Plan) -> Dict[str, Any]:
    return {
        "goal": plan.goal,
        "steps": [
            {"tool": s.tool, "params": s.params, "expected_evidence": s.expected_evidence} for s in plan.steps
        ],
        "stop_conditions": plan.stop_conditions,
        "risks": plan.risks,
        "budgets": plan.budgets,
        "role": plan.role,
        "rubric": plan.rubric,
    }
