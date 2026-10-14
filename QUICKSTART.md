# Quick start

1. Create and activate a Python 3.10+ virtual environment.
2. Run `python scripts/setup_env.py` from the repository root.
3. Set `OPENAI_API_KEY` in `.env`. Configure `PRESENTIQ_ACCESS_TOKEN` only for researcher Advanced Mode or the REST API. The setup script creates that private token for new files; existing files are preserved.
4. Run `streamlit run app.py` and open the displayed local URL.

For manual setup, install `requirements.txt`, copy `.env.example` to `.env`, and fill in the configuration. Generate a private researcher/API token with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

## Student workflow

1. Open [Research Teaching signup](https://www.researchteaching.com/signup/).
2. Choose a username and password; confirm the password.
3. Enter `learningrocks` in **Sign-Up Code**, then select **Sign Up**.
4. Return to PresentIQ, select your clerkship and complete the pre-study survey.
5. Review an assigned case, then record a presentation or upload audio up to 25 MB.
6. Review the transcript, generate feedback, and download your report. If the study save fails, use **Retry saving to study**.

The student portal does not ask for a PresentIQ access code. GPT-5.5 is the default model. Study access allows 120 operations per minute and 20 simultaneous operations per process. Adjust the two usage settings in `.env` and restart to change them.

## Troubleshooting

- **Researcher or API access unavailable:** configure `PRESENTIQ_ACCESS_TOKEN` on the server and restart. Students do not need this token.
- **Microphone unavailable:** allow microphone access and use HTTPS or localhost.
- **Provider or evaluation error:** check the provider account and selected model; retry. An error does not generate a score.
- **Study save failed:** check the sheet ID, service-account credentials and sharing, then retry with the same submission.

See [operations](docs/operations.md) for complete configuration and [contributing](docs/contributing.md) for checks before sharing a change.
