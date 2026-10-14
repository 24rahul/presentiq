# Contributing

## Change protocol

1. Describe the observed problem and expected behavior. Identify whether the change belongs in the Python app, the hosted ARGOS implementation, or both.
2. Inspect local changes before editing. Keep unrelated work intact.
3. Put provider requests, storage, report generation and UI behavior in their existing modules. Introduce an abstraction only when it owns a real responsibility or removes repeated logic.
4. Add a regression test for changed behavior that could otherwise silently fail. Use fictional inputs and mock provider and storage calls by default.
5. Run the checks below. Update the operational documentation whenever configuration, deployment or data handling changes.
6. Describe what changed, how it was verified, and any remaining limitation in the pull request.

```sh
pip install -r requirements-dev.txt
ruff check .
ruff format --check .
python test_system.py
git diff --check
```

CI runs these checks on pull requests and pushes. Live provider checks are separate, explicit smoke tests using fictional input; never send student or patient records from a fixture.

## Code conventions

- Prefer named responsibilities and explicit state transitions over generic helpers or speculative plugin frameworks.
- Keep comments for intent, constraints and non-obvious behavior. Do not narrate straightforward statements or add decorative section banners.
- Validate data at provider and HTTP boundaries. Catch exceptions where there is a recovery action or a safe user-facing error.
- Never fabricate scores, treat failure as success, or retry a write with a new submission ID.
- Use shared output schemas and configuration constants. Do not duplicate model or input contracts in entry points.
- Keep secrets and runtime data out of Git, test output, error messages and browser bundles.

Internal Python imports use `presentiq.*`. The public entry points remain `streamlit run app.py`, `uvicorn api_server:app` and `python test_system.py`.
