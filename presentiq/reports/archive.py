"""Build portable, in-memory submission archives."""

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from presentiq.reports.html import generate_html_report
from presentiq.reports.text import generate_report


def create_data_package(
    audio_data,
    audio_name,
    transcript,
    edited_transcript,
    feedback,
    case,
    clerkship_data,
    ai_provider,
    model,
    submission_id=None,
):
    """Create a ZIP with all submission data. Returns (bytes, filename)."""
    clerkship_name = clerkship_data.get("display_name", "unknown")
    case_id = case.get("id", "case")
    ts = datetime.now(timezone.utc)
    ts_str = ts.strftime("%Y%m%d_%H%M%S")
    safe_clerkship = clerkship_name.lower().replace(" ", "_").replace("/", "")
    filename = f"presentiq_{safe_clerkship}_{case_id}_{ts_str}.zip"

    transcript_text = edited_transcript if edited_transcript is not None else (transcript or "")
    service = case.get("service", "")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Audio recording
        if audio_data:
            ext = Path(audio_name).suffix.lower() or ".wav"
            zf.writestr(f"recording{ext}", audio_data)

        # Transcript
        zf.writestr("transcript.txt", transcript_text)
        if edited_transcript and transcript and edited_transcript != transcript:
            zf.writestr("transcript_original.txt", transcript)

        # Plain-text report
        report_txt = generate_report(feedback, ai_provider, model, service, transcript_text)
        zf.writestr("feedback_report.txt", report_txt)

        # HTML report
        html = generate_html_report(
            feedback, transcript_text, clerkship_name, case, ai_provider, model
        )
        zf.writestr("feedback_report.html", html)

        # Complete feedback JSON
        zf.writestr(
            "feedback_complete.json",
            json.dumps(feedback, indent=2, default=str),
        )

        # Individual agent outputs
        agent_results = feedback.get("_agent_results", {})
        for agent_name, agent_data in agent_results.items():
            zf.writestr(
                f"agents/{agent_name}.json",
                json.dumps(agent_data, indent=2, default=str),
            )

        # Metadata
        metadata = {
            "submission_id": submission_id,
            "clerkship": clerkship_name,
            "case_id": case.get("id"),
            "case_title": case.get("title"),
            "service": service,
            "presentation_format": case.get("presentation_format"),
            "ai_provider": ai_provider,
            "model": model,
            "timestamp": ts.isoformat(),
            "overall_score": feedback.get("overall_score"),
        }
        zf.writestr("metadata.json", json.dumps(metadata, indent=2))

    buf.seek(0)
    return buf.getvalue(), filename
