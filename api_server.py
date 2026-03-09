#!/usr/bin/env python3
"""FastAPI server for PresentIQ pipeline.

This server exposes the multi-agent feedback pipeline as a REST API
that can be called from the Next.js frontend.

Run with: uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import json
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from pipeline import FeedbackPipeline
from feedback_generator import FeedbackGenerator

load_dotenv()

app = FastAPI(
    title="PresentIQ API",
    description="Multi-agent feedback pipeline for medical presentations",
    version="1.0.0",
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://argosresearch.org"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    transcript: str
    service: str = "im_hospitalist"
    presentation_format: str = "full_hp"
    enable_anticipatory: bool = True


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


async def generate_analysis_stream(request: AnalyzeRequest) -> AsyncGenerator[str, None]:
    """Stream analysis progress and results."""
    try:
        # Validate API key is present
        if not os.getenv("OPENAI_API_KEY"):
            yield f"data: {json.dumps({'type': 'error', 'message': 'OPENAI_API_KEY not configured'})}\n\n"
            return

        yield f"data: {json.dumps({'type': 'progress', 'step': 'Initializing pipeline...', 'progress': 5})}\n\n"

        # Initialize the feedback generator to get service contexts
        feedback_generator = FeedbackGenerator(provider="OpenAI")

        # Initialize the pipeline
        pipeline = FeedbackPipeline(provider="OpenAI")

        yield f"data: {json.dumps({'type': 'progress', 'step': 'Pipeline ready', 'progress': 10})}\n\n"

        # Define progress callback
        steps = [
            ("Cleaning transcript...", 15),
            ("Analyzing clinical content...", 25),
            ("Evaluating clinical reasoning...", 40),
            ("Assessing structure & delivery...", 50),
            ("Analyzing communication...", 55),
            ("Running literature analysis...", 60),
            ("Running anticipatory reasoning...", 70),
            ("Debate: Generous vs Strict evaluator...", 80),
            ("Generating contrastive feedback...", 85),
            ("Synthesizing final feedback...", 90),
            ("Running synthesis critic...", 95),
        ]
        step_index = [0]

        def progress_callback(step_name: str):
            if step_index[0] < len(steps):
                step_index[0] += 1

        # Run the multi-agent analysis with progress updates
        # Since we can't easily inject streaming into the existing pipeline,
        # we'll run it and report completion
        yield f"data: {json.dumps({'type': 'progress', 'step': 'Running multi-agent analysis...', 'progress': 20})}\n\n"

        feedback = pipeline.run(
            transcript=request.transcript,
            service=request.service,
            service_contexts=feedback_generator.service_contexts,
            presentation_format=request.presentation_format,
            enable_anticipatory=request.enable_anticipatory,
            progress_callback=progress_callback,
        )

        yield f"data: {json.dumps({'type': 'progress', 'step': 'Analysis complete!', 'progress': 100})}\n\n"
        yield f"data: {json.dumps({'type': 'result', 'data': feedback})}\n\n"

    except Exception as e:
        print(f"Analysis error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@app.post("/analyze/stream")
async def analyze_presentation_stream(request: AnalyzeRequest):
    """Analyze with streaming progress updates."""
    return StreamingResponse(
        generate_analysis_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/analyze")
async def analyze_presentation(request: AnalyzeRequest):
    """Analyze a medical presentation using the multi-agent pipeline.

    Args:
        request: AnalyzeRequest containing transcript and configuration

    Returns:
        Comprehensive feedback from the multi-agent pipeline
    """
    try:
        # Validate API key is present
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY not configured"
            )

        # Initialize the feedback generator to get service contexts
        feedback_generator = FeedbackGenerator(provider="OpenAI")

        # Initialize the pipeline
        pipeline = FeedbackPipeline(provider="OpenAI")

        # Run the multi-agent analysis
        feedback = pipeline.run(
            transcript=request.transcript,
            service=request.service,
            service_contexts=feedback_generator.service_contexts,
            presentation_format=request.presentation_format,
            enable_anticipatory=request.enable_anticipatory,
        )

        return feedback

    except Exception as e:
        print(f"Analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@app.post("/analyze/legacy")
async def analyze_presentation_legacy(request: AnalyzeRequest):
    """Analyze using the legacy single-prompt generator.

    For comparison or fallback purposes.
    """
    try:
        generator = FeedbackGenerator(provider="OpenAI")
        feedback = generator.generate_feedback(
            request.transcript,
            medical_service=request.service,
        )
        return feedback

    except Exception as e:
        print(f"Legacy analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
