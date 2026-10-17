# Operations

## Configuration

Copy `.env.example` for the full set of settings. The server loads `.env`; changing environment-backed settings requires a restart.

| Setting | Purpose | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | OpenAI transcription and feedback | Required |
| `PRESENTIQ_ACCESS_TOKEN` | Private researcher Advanced Mode and REST API access; not required by students | Researcher/API access disabled until set |
| `AI_MODEL` | OpenAI API model | `gpt-5.5` |
| `XAI_API_KEY` | Optional Grok feedback | Unset |
| `GROK_MODEL` | Grok backend default | `grok-3` |
| `PRESENTIQ_REQUESTS_PER_MINUTE` | Study operations per process | `120` |
| `PRESENTIQ_MAX_CONCURRENT_ANALYSES` | Active study operations per process | `20` |
| `GOOGLE_SHEET_ID` | Optional study spreadsheet | Unset |
| `GOOGLE_CREDENTIALS_PATH` or `GOOGLE_CREDENTIALS_JSON` | Service account for Sheets | Unset |

The Streamlit portal model is configured in `configs/clerkships.yaml`; Advanced Mode exposes a model selector. `FEEDBACK_TEMPERATURE` applies to the legacy Chat Completions path, not GPT-5.5 reasoning requests. GPT-5.5 uses low reasoning effort with `store=False`; this does not by itself promise zero provider retention.

Each transcription and each complete analysis counts as one operation, regardless of the number of internal agent requests. Limits are per process; provider account limits apply separately. Multi-worker deployments need a shared limiter or gateway for aggregate limits.

## API contract

Start `uvicorn api_server:app --host 127.0.0.1 --port 8000`. A reverse proxy should supply HTTPS and body limits for remote use.

Send `Authorization: Bearer <PRESENTIQ_ACCESS_TOKEN>` to protected routes with a JSON body:

```json
{
  "transcript": "Fictional student presentation text",
  "service": "internal_medicine_hospitalist",
  "presentation_format": "sbar"
}
```

The transcript must be non-empty and no longer than 12,000 characters. Services come from `presentiq/services.py`; formats come from `configs/presentation_formats.yaml`. The historical `im_hospitalist` API alias is accepted.

`/analyze` returns validated feedback. `/analyze/legacy` uses one evaluator. `/analyze/stream` emits progress followed by a terminal `result` or `error` event; clients must inspect the event because a stream can fail after HTTP 200 has begun. `/health` is public.

## Study storage

Give the configured Google service account edit access to the spreadsheet. Logging is enabled only when both credentials and a sheet ID are configured. The app does not report a submission saved until the write succeeds.

Retries reuse the submission ID and check the sheet before appending. A process-level lock serializes checks and writes, but this is not cross-process exactly-once delivery. Large feedback JSON is split into continuation columns; join those columns in order to reconstruct it. Unexpected headers cause a visible error instead of overwriting the sheet structure.

## Deployment and rollback

This repository runs independently from the ARGOS website. Deploying the live study requires the ARGOS Cloudflare workflow documented under its `lib/presentiq/README.md`. Do not publish the Python app as a substitute for updating the existing site.

Before a Python deployment, run the offline suite and perform a fictional end-to-end smoke test. Verify authentication, microphone capture over HTTPS, model access and the intended storage destination. Keep credentials in host secrets. Retain the previous application revision and settings for rollback.

The production case links and survey URLs are mirrored into `configs/clerkships.yaml` from ARGOS's `lib/presentiq/clerkship-config.ts`. Update both when study assignments change. Do not invent missing study URLs.


## Case resources

Clerkship selection is the first student screen. Neurology uses the ScholarRx Neurology library, with 19 clinical cases and two guides. Other clerkships retain Teachable cases and signup instructions. The hosted ARGOS implementation has an attributed reader for 18 CC BY-SA bricks; the Python prototype opens source links. Three Standard-license bricks remain external. Reader practice responses do not update ScholarRx completion.

New Neurology IDs use `brick_<publisher slug>`. Retired Teachable IDs remain in historical submissions and are not relabeled as brick completions. The hosted post-study survey unlocks after presentations on three different Neurology clinical bricks. Previously saved current brick presentations count toward that total; repeat attempts on a brick count once. The two guides are educational resources, not recordable cases. This three-brick requirement supersedes the original publisher guide's one-case minimum; the hosted reader displays that clarification above the original guide. The other clerkships retain their three-case requirement.
