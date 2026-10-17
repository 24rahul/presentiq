import io
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from presentiq.access import UsageLimits
from presentiq.ai.agents.base import BaseAgent
from presentiq.paths import ROOT
from presentiq.web.portal import load_clerkship_config
from tests.fixtures import model_response


class UITests(unittest.TestCase):
    def setUp(self):
        patches = [
            patch("dotenv.load_dotenv", return_value=False),
            patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "server-secret",
                    "XAI_API_KEY": "server-xai-secret",
                    "PRESENTIQ_ACCESS_TOKEN": "study-test-token",
                    "AI_MODEL": "server-model",
                    "GOOGLE_CREDENTIALS_PATH": "",
                    "GOOGLE_CREDENTIALS_JSON": "{}",
                    "GOOGLE_SHEET_ID": "test-sheet",
                },
            ),
            patch.object(BaseAgent, "_call_llm", new=model_response),
            patch("presentiq.access.study_usage", UsageLimits(1000, 10)),
        ]
        for mock in patches:
            mock.start()
            self.addCleanup(mock.stop)
        self.audio = io.BytesIO(b"synthetic-audio-A")
        self.audio.name = "a.wav"
        uploader = patch("streamlit.file_uploader", return_value=self.audio)
        self.uploader = uploader.start()
        self.addCleanup(uploader.stop)
        transcriber = patch(
            "openai.resources.audio.transcriptions.Transcriptions.create",
            return_value=SimpleNamespace(text="Transcript A"),
        )
        self.transcriber = transcriber.start()
        self.addCleanup(transcriber.stop)
        logger = patch("presentiq.integrations.sheets.log_submission", return_value=(True, "Saved"))
        self.logger = logger.start()
        self.addCleanup(logger.stop)

    def button(self, app, label):
        return next(button for button in app.button if button.label == label)

    def advanced(self):
        app = AppTest.from_file(str(ROOT / "app.py")).run()
        self.button(app, "Open Advanced Mode").click().run()
        self.assertFalse(app.exception)
        return app

    def uploaded(self, portal=False):
        app = AppTest.from_file(str(ROOT / "app.py"))
        if portal:
            clerkship = load_clerkship_config()["clerkships"]["surgery"]
            app.session_state["page"] = "presentiq"
            app.session_state["active_case"] = clerkship["cases"][0]
            app.session_state["clerkship_data"] = clerkship
        else:
            app.session_state["page"] = "advanced"
            app.session_state["user_openai_key"] = "student-own-key"
        app.run()
        next(r for r in app.radio if r.label == "Audio source").set_value("Upload File").run()
        self.assertFalse(app.exception)
        return app

    def analyzed(self, portal=False):
        app = self.uploaded(portal)
        self.button(app, "Transcribe Audio").click().run()
        self.assertFalse(app.exception)
        self.button(app, "Generate Multi-Agent Feedback").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["feedback"]["overall_score"], 8)
        return app

    def test_clerkship_selection_precedes_provider_instructions(self):
        app = AppTest.from_file(str(ROOT / "app.py")).run()
        content = "\n".join(m.value for m in app.markdown)
        self.assertNotIn("learningrocks", content)
        app.selectbox[0].set_value("surgery").run()
        self.button(app, "Continue").click().run()
        content = "\n".join(m.value for m in app.markdown)
        self.assertIn("learningrocks", content)
        self.assertIn("Sign-Up Code", content)
        self.assertIn(
            "https://www.researchteaching.com/signup/",
            [link.proto.url for link in app.get("link_button")],
        )
        self.assertFalse(app.exception)

    def test_neurology_shows_bricks_without_teachable(self):
        app = AppTest.from_file(str(ROOT / "app.py")).run()
        app.selectbox[0].set_value("neurology").run()
        self.button(app, "Continue").click().run()
        content = "\n".join(m.value for m in app.markdown)
        self.assertNotIn("learningrocks", content)
        self.assertNotIn("Create your Teachable account", content)
        links = [link.proto.url for link in app.get("link_button")]
        self.assertEqual(
            sum(url.startswith("https://exchange.scholarrx.com/brick/") for url in links), 21
        )
        self.assertEqual(len(app.session_state["clerkship_data"]["cases"]), 19)
        self.assertFalse(app.exception)

    def test_server_secrets_are_never_populated_or_changed(self):
        before = dict(os.environ)
        first = self.advanced()
        self.assertEqual(next(w for w in first.text_input if w.label == "OpenAI API Key").value, "")
        next(w for w in first.text_input if w.label == "OpenAI API Key").set_value(
            "student-A-key"
        ).run()
        self.assertFalse(first.exception)
        second = self.advanced()
        self.assertEqual(
            next(w for w in second.text_input if w.label == "OpenAI API Key").value, ""
        )
        self.assertEqual(dict(os.environ), before)

    def test_bring_your_own_key_works_without_server_credentials(self):
        with patch.dict(
            os.environ, {"OPENAI_API_KEY": "", "XAI_API_KEY": "", "PRESENTIQ_ACCESS_TOKEN": ""}
        ):
            app = self.advanced()
            next(w for w in app.text_input if w.label == "OpenAI API Key").set_value(
                "own-key"
            ).run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.get("audio_input")), 1)

    def test_student_portal_does_not_require_token(self):
        with patch.dict(os.environ, {"PRESENTIQ_ACCESS_TOKEN": ""}):
            app = self.uploaded(portal=True)
            self.assertFalse(app.exception)
            self.assertTrue(self.button(app, "Transcribe Audio"))
            self.assertFalse(any("token" in field.label.lower() for field in app.text_input))

    def test_researcher_server_access_requires_token(self):
        app = self.advanced()
        self.assertFalse(app.get("audio_input"))
        token = next(w for w in app.text_input if w.label == "Researcher access token")
        token.set_value("wrong-token").run()
        self.assertFalse(app.get("audio_input"))
        token = next(w for w in app.text_input if w.label == "Researcher access token")
        token.set_value("study-test-token").run()
        self.assertEqual(len(app.get("audio_input")), 1)

    def test_new_upload_cannot_export_old_analysis(self):
        with patch("tempfile.NamedTemporaryFile", side_effect=AssertionError("No disk audio")):
            app = self.analyzed()
            new_audio = io.BytesIO(b"synthetic-audio-B")
            new_audio.name = "b.wav"
            self.uploader.return_value = new_audio
            app.run()
            self.assertFalse(app.exception)
            self.assertIsNone(app.session_state["feedback"])
            self.assertIsNone(app.session_state["transcription"])
            self.assertEqual(app.session_state["audio_data"], b"synthetic-audio-B")
            self.assertTrue(self.button(app, "Transcribe Audio"))
            self.assertFalse(app.get("download_button"))

    def test_blank_edit_disables_analysis_instead_of_reusing_original(self):
        app = self.analyzed()
        app.text_area[0].set_value("").run()
        self.assertIsNone(app.session_state["feedback"])
        self.assertEqual(app.session_state["edited_transcription"], "")
        self.assertTrue(self.button(app, "Generate Multi-Agent Feedback").disabled)

    def test_changed_model_invalidates_feedback(self):
        app = self.analyzed()
        next(s for s in app.selectbox if s.label == "Model").set_value("gpt-4").run()
        self.assertIsNone(app.session_state["feedback"])
        self.assertEqual(app.session_state["transcription"], "Transcript A")

    def test_failed_sheet_save_stays_unsaved_and_can_be_retried(self):
        self.logger.return_value = (False, "Mock outage")
        app = self.analyzed(portal=True)
        submission_id = app.session_state["submission_id"]
        self.assertFalse(app.session_state["data_logged"])
        self.assertTrue(app.warning)
        app.run()
        self.assertEqual(self.logger.call_count, 1)
        self.logger.return_value = (True, "Saved")
        self.button(app, "Retry saving to study").click().run()
        self.assertTrue(app.session_state["data_logged"])
        self.assertEqual(self.logger.call_count, 2)
        self.assertTrue(
            all(
                call.kwargs["submission_id"] == submission_id for call in self.logger.call_args_list
            )
        )

    def test_navigation_discards_case_audio_and_analysis(self):
        app = self.analyzed(portal=True)
        epoch = app.session_state["audio_epoch"]
        self.button(app, "Back to Dashboard").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["page"], "dashboard")
        self.assertIsNone(app.session_state["audio_data"])
        self.assertIsNone(app.session_state["feedback"])
        self.assertGreater(app.session_state["audio_epoch"], epoch)

    def test_model_failure_remains_retryable_and_is_not_logged(self):
        app = self.uploaded(portal=True)
        self.button(app, "Transcribe Audio").click().run()
        with patch.object(
            BaseAgent, "_call_llm", side_effect=RuntimeError("private provider error")
        ):
            self.button(app, "Generate Multi-Agent Feedback").click().run()
        self.assertFalse(app.exception)
        self.assertIsNone(app.session_state["feedback"])
        self.assertTrue(app.error)
        self.assertNotIn("private provider error", "\n".join(e.value for e in app.error))
        self.logger.assert_not_called()
        self.assertFalse(self.button(app, "Generate Multi-Agent Feedback").disabled)
