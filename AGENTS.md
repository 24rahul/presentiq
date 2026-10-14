# Working in PresentIQ

This repository is the Python implementation. The hosted study is maintained separately in ARGOS; see `docs/architecture.md` and `docs/operations.md` before changing deployment behavior.

- Preserve local changes and keep changes scoped to the requested behavior.
- Put domain code under `presentiq/`, tests under `tests/`, and operational documentation under `docs/`.
- Use shared schemas, service definitions and presentation formats. Do not duplicate scoring or provider logic in entry points.
- Validate provider responses. Failures must never become default scores or successful-looking feedback.
- Keep credentials, recordings, transcripts and study records out of Git and logs. Tests use fictional inputs and mocked external services.
- Run `ruff check .`, `ruff format --check .`, and `python test_system.py` after code changes.
- Update configuration examples and operational docs when changing an environment variable, entry point, data flow or deployment requirement.
- Prefer direct functions and explicit state transitions. Avoid speculative frameworks, decorative comments and broad exception catches without a recovery or boundary-level error response.
