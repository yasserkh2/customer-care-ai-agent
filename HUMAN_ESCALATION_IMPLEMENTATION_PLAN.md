# Phase 1: Route Mid-Conversation Escalation To `human_escalation`

## Summary
- First implement the conversation-level routing behavior: whenever escalation is detected during any turn, the graph should move to the `human_escalation` node immediately.
- This phase is about control flow and state, not the final LLM classifier yet.
- It should work whether escalation is triggered from classification, KB failure handling, or action-flow failure handling.

## Key Changes
- Extend `app/graph/state.py` with:
  - `handoff_pending: bool`
  - `turn_outcome: "resolved" | "needs_input" | "unresolved"`
  - `turn_failure_reason: str | None`
- Add a dedicated escalation-evaluation node, `evaluate_escalation`, placed after `kb_answer` and `action_request` and before `response`.
- Update graph flow in `app/graph/builder.py` to:
  - `ingest_query -> classify_intent -> kb_answer/action_request/human_escalation`
  - `kb_answer -> evaluate_escalation`
  - `action_request -> evaluate_escalation`
  - `evaluate_escalation -> human_escalation or response`
  - `human_escalation -> response`
- Update routing in `app/graph/router.py`:
  - if `handoff_pending=True`, always route directly to `human_escalation`
  - this check should happen before active action routing
- Define the escalation rule for this phase:
  - if `intent == "human_escalation"` after classification, route there immediately
  - if a service returns `turn_outcome="unresolved"` and `failure_count + 1 >= 3`, set `handoff_pending=True` and route to `human_escalation`
  - if a service explicitly sets `frustration_flag=True` or `escalation_reason`, set `handoff_pending=True` and route to `human_escalation`
- When handoff starts:
  - preserve `history`
  - preserve `escalation_reason`
  - clear `active_action`
  - clear appointment-confirmation flags so the bot does not continue automation after handoff

## Service Contract Adjustments
- KB and action paths must return enough metadata for escalation routing:
  - `turn_outcome`
  - optional `turn_failure_reason`
  - optional `escalation_reason`
- `HumanEscalationAgent` stays responsible for building the user-facing handoff message once the graph reaches that node.

## Test Plan
- Graph test: explicit escalation intent routes directly to `human_escalation`
- Graph test: `handoff_pending=True` forces routing to `human_escalation` on the next turn
- KB test: third consecutive unresolved KB turn routes to `human_escalation`
- Action test: unresolved action failure with escalation reason routes to `human_escalation`
- State test: once handoff begins, `active_action` is cleared and the bot no longer continues appointment flow

## Assumptions
- Repeated-failure threshold remains `3`
- This phase can use temporary deterministic escalation flags until the LLM classifier is added
- The LLM-based classifier will be added in the next phase, but the routing contract introduced here should not need to change
