import asyncio
import json
import os
import threading
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

with patch("dotenv.load_dotenv", return_value=False):
    import api_server
from presentiq.access import UsageLimits
from presentiq.ai.agents.base import BaseAgent
from tests.fixtures import model_response

TOKEN = "synthetic-study-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


class APITests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(
            os.environ,
            {
                "PRESENTIQ_ACCESS_TOKEN": TOKEN,
                "OPENAI_API_KEY": "test-key",
                "AI_MODEL": "test-model",
            },
        )
        self.env.start()
        self.addCleanup(self.env.stop)
        limiter = patch.object(api_server, "study_usage", UsageLimits(1000, 2))
        limiter.start()
        self.addCleanup(limiter.stop)
        model = patch.object(BaseAgent, "_call_llm", new=model_response)
        model.start()
        self.addCleanup(model.stop)
        self.client = TestClient(api_server.app)
        self.addCleanup(self.client.close)

    def test_missing_or_invalid_auth_never_starts_pipeline(self):
        with patch.object(api_server, "run_analysis") as run:
            for route in ["/analyze", "/analyze/legacy", "/analyze/stream"]:
                for headers in [{}, {"Authorization": "Bearer wrong"}]:
                    self.assertEqual(
                        self.client.post(
                            route, json={"transcript": "Synthetic"}, headers=headers
                        ).status_code,
                        401,
                    )
            run.assert_not_called()

    def test_unconfigured_access_fails_closed(self):
        with patch.dict(os.environ, {"PRESENTIQ_ACCESS_TOKEN": ""}):
            self.assertEqual(
                self.client.post(
                    "/analyze", json={"transcript": "Synthetic"}, headers=HEADERS
                ).status_code,
                503,
            )
        self.assertEqual(self.client.get("/health").status_code, 200)

    def test_invalid_inputs_rejected_before_model_calls(self):
        for body in [
            {"transcript": ""},
            {"transcript": "   "},
            {"transcript": "x" * 12001},
            {"transcript": "Synthetic", "service": "unknown"},
            {"transcript": "Synthetic", "presentation_format": "unknown"},
        ]:
            with (
                self.subTest(body_keys=list(body)),
                patch.object(api_server, "run_analysis") as run,
            ):
                self.assertEqual(
                    self.client.post("/analyze", json=body, headers=HEADERS).status_code, 422
                )
                run.assert_not_called()

    def test_standard_route_returns_validated_feedback(self):
        response = self.client.post(
            "/analyze",
            json={"transcript": "Synthetic", "service": "im_hospitalist"},
            headers=HEADERS,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "complete")
        self.assertEqual(response.json()["overall_score"], 8)

    def test_legacy_route_calls_correct_service_argument(self):
        response = self.client.post(
            "/analyze/legacy",
            json={"transcript": "Synthetic", "service": "surgery_general"},
            headers=HEADERS,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["specialty"], "Surgery")
        self.assertEqual(response.json()["overall_score"], 8)

    def test_stream_emits_seven_steps_and_result(self):
        response = self.client.post(
            "/analyze/stream", json={"transcript": "Synthetic"}, headers=HEADERS
        )
        events = [
            json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")
        ]
        self.assertEqual(response.status_code, 200)
        progress = [event for event in events if event["type"] == "progress"]
        self.assertEqual(len(progress), 8)
        self.assertEqual(progress[-1]["progress"], 100)
        self.assertEqual(events[-1]["type"], "result")
        self.assertEqual(events[-1]["data"]["overall_score"], 8)

    def test_provider_failure_returns_no_successful_score(self):
        with patch.object(BaseAgent, "_call_llm", side_effect=RuntimeError("private-secret")):
            response = self.client.post(
                "/analyze", json={"transcript": "Synthetic"}, headers=HEADERS
            )
            self.assertEqual(response.status_code, 502)
            self.assertNotIn("overall_score", response.json())
            self.assertNotIn("private-secret", response.text)
            response = self.client.post(
                "/analyze/stream", json={"transcript": "Synthetic"}, headers=HEADERS
            )
            self.assertNotIn('"type": "result"', response.text)
            self.assertNotIn("private-secret", response.text)
            self.assertIn('"type": "error"', response.text)

    def test_request_limit_and_capacity_limit(self):
        with patch.object(api_server, "study_usage", UsageLimits(1, 1)) as limiter:
            self.assertEqual(
                self.client.post(
                    "/analyze", json={"transcript": "Synthetic"}, headers=HEADERS
                ).status_code,
                200,
            )
            self.assertEqual(
                self.client.post(
                    "/analyze", json={"transcript": "Synthetic"}, headers=HEADERS
                ).status_code,
                429,
            )
        with patch.object(api_server, "study_usage", UsageLimits(10, 1)) as limiter:
            with limiter.reserve():
                self.assertEqual(
                    self.client.post(
                        "/analyze", json={"transcript": "Synthetic"}, headers=HEADERS
                    ).status_code,
                    429,
                )


class APIConcurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def test_stream_delivers_progress_before_completion_and_stops_on_disconnect(self):
        release = threading.Event()
        completed_steps = []

        def slow_pipeline(request, progress_callback):
            progress_callback("First stage", 1, 7)
            completed_steps.append(1)
            release.wait(timeout=2)
            progress_callback("Second stage", 2, 7)
            completed_steps.append(2)
            return {"overall_score": 8}

        with patch.object(api_server, "run_analysis", side_effect=slow_pipeline):
            stream = api_server.generate_analysis_stream(
                api_server.AnalyzeRequest(transcript="Synthetic")
            )
            try:
                first = await asyncio.wait_for(anext(stream), timeout=0.5)
                self.assertIn("First stage", first)
                self.assertFalse(release.is_set())
                await stream.aclose()
            finally:
                release.set()
                await asyncio.wait_for(asyncio.gather(*tuple(api_server._workers)), timeout=1)
            self.assertEqual(completed_steps, [1])

    async def test_health_remains_responsive_during_analysis(self):
        started, release = threading.Event(), threading.Event()

        def slow_pipeline(*args, **kwargs):
            started.set()
            release.wait(timeout=2)
            return {"status": "complete", "overall_score": 8}

        with (
            patch.dict(os.environ, {"PRESENTIQ_ACCESS_TOKEN": TOKEN, "OPENAI_API_KEY": "test-key"}),
            patch.object(api_server, "run_analysis", side_effect=slow_pipeline),
        ):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=api_server.app), base_url="http://test"
            ) as client:
                analysis = asyncio.create_task(
                    client.post("/analyze", json={"transcript": "Synthetic"}, headers=HEADERS)
                )
                try:
                    self.assertTrue(await asyncio.to_thread(started.wait, 1))
                    health = await asyncio.wait_for(client.get("/health"), timeout=0.5)
                    self.assertEqual(health.status_code, 200)
                    self.assertFalse(analysis.done())
                finally:
                    release.set()
                    await analysis
