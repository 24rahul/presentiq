# Quick start

1. Create and activate a Python 3.10+ virtual environment.
2. Run `python scripts/setup_env.py` from the repository root.
3. Set `OPENAI_API_KEY` in `.env`. Configure `PRESENTIQ_ACCESS_TOKEN` only for researcher Advanced Mode or the REST API. The setup script creates that private token for new files; existing files are preserved.
4. Run `streamlit run app.py` and open the displayed local URL.

For manual setup, install `requirements.txt`, copy `.env.example` to `.env`, and fill in the configuration. Generate a private researcher/API token with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

## Student workflow

1. Open PresentIQ and select your clerkship on the first screen.
2. For Neurology, choose a ScholarRx clinical brick. The hosted ARGOS app displays 18 openly licensed bricks in its reader; three open on ScholarRx. The Python prototype links to the source library.
3. For the other clerkships, create an account at [Research Teaching](https://www.researchteaching.com/signup/), choose and confirm your password, and enter `learningrocks` in **Sign-Up Code**. Return to the case dashboard after signing up.
4. Complete the pre-study survey, review a case, and record a presentation or upload audio up to 25 MB. The hosted app requests study ID and email before the first recording.
5. Review the transcript, generate feedback, and download your report. If the study save fails, use **Retry saving to study**.
6. Complete the post-study survey after the required presentations. Neurology requires a minimum of one clinical case. Reading a guide or answering practice questions does not create a PresentIQ submission or update ScholarRx course credit.

The student portal does not ask for a PresentIQ access code. GPT-5.5 is the default model. Study access allows 120 operations per minute and 20 simultaneous operations per process. Adjust the two usage settings in `.env` and restart to change them.

## Troubleshooting

- **Researcher or API access unavailable:** configure `PRESENTIQ_ACCESS_TOKEN` on the server and restart. Students do not need this token.
- **Microphone unavailable:** allow microphone access and use HTTPS or localhost.
- **Provider or evaluation error:** check the provider account and selected model; retry. An error does not generate a score.
- **Study save failed:** check the sheet ID, service-account credentials and sharing, then retry with the same submission.

See [operations](docs/operations.md) for complete configuration and [contributing](docs/contributing.md) for checks before sharing a change.
