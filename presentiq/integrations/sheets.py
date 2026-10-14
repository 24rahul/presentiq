"""Google Sheets persistence with retry-safe submission IDs."""

import json
import os
import threading
from datetime import datetime, timezone

_HEADERS = [
    "Timestamp",
    "Clerkship",
    "Case ID",
    "Case Title",
    "Service",
    "Presentation Format",
    "Overall Score",
    "Transcript",
    "Overall Assessment",
    "Clinical Content",
    "Clinical Reasoning",
    "Structure & Delivery",
    "Communication & Professionalism",
    "Plan Coherence",
    "Information Efficiency",
    "Debate Summary",
    "Contrastive Feedback",
    "Teaching Points",
    "AI Provider",
    "AI Model",
    "Full Feedback JSON",
    "Submission ID",
]
_write_lock = threading.Lock()


def is_logging_configured():
    return bool(
        os.getenv("GOOGLE_SHEET_ID")
        and (os.getenv("GOOGLE_CREDENTIALS_PATH") or os.getenv("GOOGLE_CREDENTIALS_JSON"))
    )


def log_submission(
    clerkship, case, transcript, feedback, score, ai_provider, model, *, submission_id
):
    if not is_logging_configured():
        return False, "Study storage is not configured. Contact the study administrator."
    if not submission_id or feedback.get("status") != "complete":
        return False, "Only a completed evaluation can be saved to the study."

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
        if credentials_json:
            creds = Credentials.from_service_account_info(
                json.loads(credentials_json), scopes=scopes
            )
        else:
            creds = Credentials.from_service_account_file(
                os.getenv("GOOGLE_CREDENTIALS_PATH"), scopes=scopes
            )
        gc = gspread.authorize(creds)
        gc.set_timeout(20)
        spreadsheet = gc.open_by_key(os.environ["GOOGLE_SHEET_ID"])
        worksheet = spreadsheet.sheet1

        agents = feedback.get("_agent_results", {})
        debate = "\n".join(
            f"{p['dimension']}: {p['resolution']}"
            for p in agents.get("debate", {}).get("contested_points", [])
        )
        rewrites = "\n".join(
            f"{r['area']}: {r['why_better']}"
            for r in agents.get("contrastive_feedback", {}).get("rewrites", [])
        )
        teaching = "\n".join(
            f"{p['topic']}: {p['point']}"
            for p in agents.get("literature_learning", {}).get("teaching_points", [])
        )
        payload = json.dumps(feedback, ensure_ascii=False)
        # Preserve complete JSON without exceeding a single Sheets cell's size.
        chunks = [payload[i : i + 45000] for i in range(0, len(payload), 45000)]
        row = [
            datetime.now(timezone.utc).isoformat(),
            clerkship.get("display_name", ""),
            case.get("id", ""),
            case.get("title", ""),
            case.get("service", ""),
            case.get("presentation_format", ""),
            str(score),
            transcript,
            feedback.get("overall_assessment", ""),
            feedback.get("clinical_content", ""),
            feedback.get("clinical_reasoning", ""),
            feedback.get("presentation_structure", ""),
            feedback.get("communication_professionalism", ""),
            feedback.get("plan_coherence_summary", ""),
            feedback.get("semantic_density_summary", ""),
            debate,
            rewrites,
            teaching,
            ai_provider,
            model,
            chunks[0],
            submission_id,
            *chunks[1:],
        ]
        if any(len(str(value)) > 45000 for value in row):
            return (
                False,
                "A feedback section is too large for study storage. Download your data and contact the study administrator.",
            )

        with _write_lock:
            existing = worksheet.row_values(1)
            count = max(len(existing), len(row), len(_HEADERS))
            headers = _HEADERS + [
                f"Full Feedback JSON (part {i})" for i in range(2, count - len(_HEADERS) + 2)
            ]
            if existing and existing != headers[: len(existing)]:
                return (
                    False,
                    "The study sheet has unexpected columns. Contact the study administrator.",
                )
            if worksheet.col_count < count:
                worksheet.add_cols(count - worksheet.col_count)
            if existing != headers:
                worksheet.update(range_name="A1", values=[headers], value_input_option="RAW")
            # If an append succeeded but its response was lost, retry acknowledges
            # that row instead of appending another copy (serialized per process).
            if submission_id in worksheet.col_values(22)[1:]:
                return True, "Submission already saved."
            worksheet.append_row(row, value_input_option="RAW")
        return True, "Submission saved."
    except ImportError:
        return False, "Study storage dependencies are missing. Contact the study administrator."
    except Exception:
        # Remote exceptions may include the transcript, sheet ID or credential details.
        return (
            False,
            "Study storage is temporarily unavailable. Retry saving or download your data.",
        )
