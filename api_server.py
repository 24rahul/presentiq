"""Authenticated REST and SSE interfaces for the PresentIQ pipeline."""

import asyncio
import json
import os
import threading

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, model_validator

load_dotenv()

from presentiq.access import CapacityError, access_token_valid, study_usage
from presentiq.ai.backend import AnalysisError
from presentiq.ai.legacy import FeedbackGenerator
from presentiq.ai.pipeline import FeedbackPipeline
from presentiq.services import SERVICE_CONTEXTS
from presentiq.validation import MAX_TRANSCRIPT_CHARS, validate_analysis_input

app = FastAPI(title="PresentIQ API", version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://argosresearch.org"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
bearer = HTTPBearer(auto_error=False)
_workers = set()


def require_access(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if not os.getenv("PRESENTIQ_ACCESS_TOKEN"):
        raise HTTPException(503, "Study API access is not configured.")
    if credentials is None or not access_token_valid(credentials.credentials):
        raise HTTPException(
            401, "A valid study access token is required.", headers={"WWW-Authenticate": "Bearer"}
        )
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(503, "Analysis provider access is not configured.")


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    transcript: str = Field(min_length=1, max_length=MAX_TRANSCRIPT_CHARS)
    service: str = "internal_medicine_hospitalist"
    presentation_format: str = "full_hp"
    enable_anticipatory: bool = True

    @model_validator(mode="after")
    def validate_selection(self):
        # Preserve the original API's default service alias for existing clients.
        if self.service == "im_hospitalist":
            self.service = "internal_medicine_hospitalist"
        self.transcript = validate_analysis_input(
            self.transcript, self.service, self.presentation_format
        )
        return self


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.1.0"}


def run_analysis(request, progress_callback=None):
    with study_usage.reserve(), FeedbackPipeline(provider="OpenAI") as pipeline:
        return pipeline.run(
            transcript=request.transcript,
            service=request.service,
            service_contexts=SERVICE_CONTEXTS,
            presentation_format=request.presentation_format,
            enable_anticipatory=request.enable_anticipatory,
            progress_callback=progress_callback,
        )


def public_error(exc):
    if isinstance(exc, CapacityError):
        return 429, str(exc)
    if isinstance(exc, AnalysisError):
        return 502, str(exc)
    return 500, "Analysis could not be completed. Please retry or contact the study administrator."


async def generate_analysis_stream(request):
    loop = asyncio.get_running_loop()
    events = asyncio.Queue()
    cancelled = threading.Event()

    def emit(event):
        if not cancelled.is_set():
            try:
                loop.call_soon_threadsafe(events.put_nowait, event)
            except RuntimeError:
                # The server may shut down while a provider call finishes.
                cancelled.set()

    def progress_callback(name, step, total):
        if cancelled.is_set():
            raise AnalysisError("Analysis cancelled.")
        emit({"type": "progress", "step": name, "progress": round((step - 1) / total * 100)})

    def work():
        try:
            feedback = run_analysis(request, progress_callback)
            emit({"type": "progress", "step": "Analysis complete!", "progress": 100})
            emit({"type": "result", "data": feedback})
        except Exception as exc:
            status, message = public_error(exc)
            emit({"type": "error", "status": status, "message": message})

    worker = asyncio.create_task(asyncio.to_thread(work))
    _workers.add(worker)
    worker.add_done_callback(_workers.discard)
    try:
        while True:
            try:
                event = await asyncio.wait_for(events.get(), timeout=15)
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"
                continue
            yield f"data: {json.dumps(event)}\n\n"
            if event["type"] in ("result", "error"):
                break
    finally:
        # Work already in flight keeps its usage slot until its thread exits.
        cancelled.set()


@app.post("/analyze/stream", dependencies=[Depends(require_access)])
async def analyze_presentation_stream(request: AnalyzeRequest):
    return StreamingResponse(
        generate_analysis_stream(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/analyze", dependencies=[Depends(require_access)])
def analyze_presentation(request: AnalyzeRequest):
    # FastAPI executes synchronous endpoints in its worker thread pool.
    try:
        return run_analysis(request)
    except Exception as exc:
        status, message = public_error(exc)
        raise HTTPException(status, message) from None


@app.post("/analyze/legacy", dependencies=[Depends(require_access)])
def analyze_presentation_legacy(request: AnalyzeRequest):
    try:
        with study_usage.reserve(), FeedbackGenerator(provider="OpenAI") as generator:
            return generator.generate_feedback(
                request.transcript,
                service=request.service,
                presentation_format=request.presentation_format,
            )
    except Exception as exc:
        status, message = public_error(exc)
        raise HTTPException(status, message) from None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
