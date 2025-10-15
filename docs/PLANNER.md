# Planner Design

## Plan Structure
- goal: user intent and success criteria
- steps: ordered list of steps with `tool` and `params`
- expected_evidence: per-step evidence requirements
- stop_conditions: conditions to stop early (evidence, budget, no actions)
- risks: known risks and fallback (retry, rollback→skip, replan)
- budgets: token/time/steps caps

## Constraints
- Roles and policies limit allowed tools and caps (see `configs/policy/PLANNER_POLICY.yaml`)
- Enforce budgets and wallclock guardrails during planning

## Rubric
- Consistency, Grounding, Efficiency (1–5). Planner outputs self-assessment and rationale.

## Acceptance
- Template exists and is referenced by orchestrator
- Plans conform to schema and satisfy policy caps; rationale is present
