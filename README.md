# PresentIQ

PresentIQ gives medical students structured feedback on recorded case presentations. This repository contains the Python evaluation pipeline, a Streamlit study portal, and a FastAPI interface.

The live study runs at [argosresearch.org/presentiq](https://argosresearch.org/presentiq). Its Next.js implementation lives in the separate [ARGOS website repository](https://github.com/ARGOS-Research-Group/argos-website/tree/main/app/presentiq). Updating this repository alone does not update that website.

## Local setup

Python 3.10 or newer is required.

```sh
python -m venv venv
source venv/bin/activate
python scripts/setup_env.py
streamlit run app.py
```

The setup script installs dependencies, creates a private `.env` only if one does not exist, and runs the offline tests. Existing configuration is preserved. Manual setup is `pip install -r requirements.txt` followed by copying `.env.example` to `.env`.

Configure `OPENAI_API_KEY` for transcription and evaluation. GPT-5.5 is the default evaluation model. The student portal does not require an access code. `PRESENTIQ_ACCESS_TOKEN` is private and used only for researcher Advanced Mode and REST API access. Advanced Mode can also use a researcher's own provider key.

The hosted ARGOS app asks for study ID and Johns Hopkins email before clerkship selection, then restores saved survey and presentation progress using that identity. The Python prototype starts with clerkship selection and links to source cases. Neurology shows 19 clinical cases and the PresentIQ presentation guide from the [ScholarRx Neurology Clinical Bricks Library](https://exchange.scholarrx.com/lists/vprnjrjq65m6). Bricks open on their individual ScholarRx pages; students return to PresentIQ to record. The hosted reader is retained behind a configuration toggle. Other clerkships use [Research Teaching](https://www.researchteaching.com/signup/), with `learningrocks` entered in **Sign-Up Code**. Teachable instructions appear only for those clerkships.

## Repository layout

```text
app.py                    Streamlit entry point
api_server.py             FastAPI entry point
presentiq/
  ai/                     Provider clients, pipeline, legacy evaluator, agents
  integrations/           Google Sheets logging
  reports/                Text, HTML, and ZIP exports
  web/                    Portal, feedback views, browser recording, session state
  access.py               Study access and usage limits
  services.py             Specialty evaluation context
  validation.py           Input validation
  paths.py                Configuration paths
configs/                  Clerkship cases, surveys, presentation formats
scripts/setup_env.py      Environment setup
tests/                   Offline regression tests
docs/                    Architecture, contribution guide, operations
```

## Run and verify

```sh
# REST API; protected requests need Authorization: Bearer <study token>.
uvicorn api_server:app --host 127.0.0.1 --port 8000

# Development checks; provider and storage requests are mocked.
pip install -r requirements-dev.txt
ruff check .
ruff format --check .
python test_system.py
```

`/health` is public. `POST /analyze` returns multi-agent feedback; `/analyze/stream` streams progress; `/analyze/legacy` provides single-prompt feedback. See [operations](docs/operations.md) for payloads, configuration and deployment boundaries.

## Behavior and data handling

- Each completed evaluation has validated output and a submission ID. Failed, refused, truncated, or malformed responses return an error and no score.
- GPT-5.5 uses the Responses API with low reasoning effort and structured outputs. Legacy GPT and Grok selections retain their existing Chat Completions path.
- Study-funded access allows 120 operations per minute and 20 concurrent operations per process. A transcription and an evaluation count separately.
- Audio is captured in the browser and held in memory. Replacing audio clears its transcript and feedback; changing evaluation settings clears feedback.
- OpenAI receives audio for transcription and transcript content for feedback. Python study logging, when configured, retains transcripts, feedback and study metadata in Google Sheets. The hosted ARGOS implementation also retains recordings and reports in Google Drive after study consent. Closing the browser does not delete submitted study records.
- Google Sheets saves have an explicit retry path and reuse the submission ID. Checks within one process prevent duplicates after an uncertain append; multiple processes need shared coordination.

Use fictional study cases and do not submit identifying patient information. Browser recording requires HTTPS on a hosted installation; localhost also works.

Further reading: [quick start](QUICKSTART.md), [architecture](docs/architecture.md), [contributing](docs/contributing.md), [operations](docs/operations.md).
