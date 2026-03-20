# Testing Notes

This folder contains behavior-focused tests for SmartTutor.

## What is covered

- `test_examples.py`
  - Basic accepted and rejected examples
  - Grade info and summary handling
- `test_fallback_rules.py`
  - Short keyword-based fallback rules
- `test_multiturn_followups.py`
  - Multi-turn follow-up cases
  - Clarification after rejection
  - Boundary and near-boundary prompts
- `test_ui.py`
  - UI delegation to the orchestrator

## How to run

From the `smarttutor` directory:

```powershell
pytest -q
```

Run only the tests in this folder:

```powershell
pytest -q tests
```

Run only the new multi-turn tests:

```powershell
pytest -q tests/test_multiturn_followups.py
```

## Notes

- Most tests are mock-first, so they do not spend API tokens.
- These tests mainly verify routing, guardrails, session flow, and response policy.
- If you want to inspect real model answers, use the app manually or run a separate smoke test script.
