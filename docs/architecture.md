# Architecture

## Boundaries

`app.py` owns Streamlit interaction; `api_server.py` owns HTTP authentication, request parsing and streaming. Both call `presentiq.ai.pipeline.FeedbackPipeline`. Neither entry point implements scoring rules.

`presentiq.ai.backend` creates an isolated provider client. Credentials are passed explicitly or read from server configuration; a session never changes process environment variables. Agents share that client for one evaluation, and it closes when the evaluation finishes.

`presentiq.ai.agents.schemas` defines output contracts. Model output must validate before another stage consumes it. Exceptions propagate to the entry point, which returns a sanitized error. No fallback score or successful-looking assessment is generated.

## Evaluation flow

1. Clean transcription artifacts while preserving clinical meaning.
2. Review clinical content and reasoning.
3. Evaluate structure, communication, learning points and optional attending commentary in parallel.
4. Produce contrasting evaluations and targeted rewrites in parallel.
5. Synthesize the findings.
6. Review the synthesis and, when needed, validate one revision.

Presentation format and medical service context are supplied to the reviewers. A brief handoff is evaluated against its expected content, rather than a full history and physical.

## Submission lifecycle

An audio fingerprint identifies the current recording. New audio invalidates the transcript and evaluation. Transcript edits and evaluation setting changes invalidate feedback. A completed evaluation receives a UUID that is reused for exports and save retries.

Recordings and ZIP archives remain in memory. `presentiq.web.state` owns reset rules; `presentiq.reports` owns serialization and has no Streamlit dependency. Google Sheets is an optional integration with a visible failure and retry path.

## Production counterpart

The ARGOS website is a separate TypeScript implementation with its own deployment. Its current workflow has six specialized reviewers and a synthesis stage, while this Python implementation includes transcription QA, clinical content, communication and a synthesis critic as distinct agents. Do not assume the two scoring pipelines are equivalent.

Keep case links, signup instructions, model choice, validation guarantees and operational documentation aligned. Cross-repository changes need checks in both repositories; Python tests cannot validate the hosted UI.
