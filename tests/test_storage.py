import io
import json
import os
import unittest
import zipfile
from unittest.mock import MagicMock, patch

from presentiq.integrations import sheets as sheets_logger
from presentiq.reports.archive import create_data_package
from presentiq.web.state import reset_submission, set_audio, update_transcript
from tests.fixtures import SYNTHESIS


class SubmissionStateTests(unittest.TestCase):
    def test_replacing_audio_invalidates_transcript_feedback_and_logging(self):
        state = {}
        reset_submission(state)
        set_audio(state, b"audio-a", "a.wav", "upload")
        state.update(
            transcription="A",
            edited_transcription="A",
            transcription_editor="A",
            feedback=SYNTHESIS.copy(),
            data_logged=True,
        )
        set_audio(state, b"audio-b", "b.wav", "upload")
        self.assertEqual(state["audio_data"], b"audio-b")
        for key in ["transcription", "edited_transcription", "feedback", "submission_id"]:
            self.assertIsNone(state[key])
        self.assertFalse(state["data_logged"])
        self.assertNotIn("transcription_editor", state)

    def test_unchanged_audio_preserves_analysis_without_disk_writes(self):
        state = {}
        reset_submission(state)
        with patch("tempfile.NamedTemporaryFile", side_effect=AssertionError("No disk audio")):
            set_audio(state, b"audio-a", "a.wav", "upload")
            state["transcription"] = "A"
            set_audio(state, b"audio-a", "a.wav", "upload")
        self.assertEqual(state["transcription"], "A")

    def test_reset_discards_audio_and_changes_widget_generation(self):
        state = {}
        reset_submission(state)
        epoch = state["audio_epoch"]
        set_audio(state, b"audio", "a.wav", "record")
        reset_submission(state)
        self.assertIsNone(state["audio_data"])
        self.assertGreater(state["audio_epoch"], epoch)

    def test_empty_edited_transcript_is_preserved_and_invalidates_feedback(self):
        state = {"edited_transcription": "old", "feedback": SYNTHESIS.copy(), "data_logged": True}
        update_transcript(state, "")
        self.assertEqual(state["edited_transcription"], "")
        self.assertIsNone(state["feedback"])
        self.assertFalse(state["data_logged"])

    def test_audio_size_and_extension_limits(self):
        for data, name in [
            (b"", "a.wav"),
            (b"a" * (25 * 1024 * 1024 + 1), "a.wav"),
            (b"a", "a.exe"),
        ]:
            with self.subTest(name=name, size=len(data)), self.assertRaises(ValueError):
                set_audio({}, data, name, "upload")

    def test_archive_contains_in_memory_audio_and_matching_metadata(self):
        feedback = {**SYNTHESIS, "status": "complete"}
        data, filename = create_data_package(
            b"audio-B",
            "b.wav",
            "original B",
            "edited B",
            feedback,
            {
                "id": "case_1",
                "title": "Case",
                "service": "surgery_general",
                "presentation_format": "full_hp",
            },
            {"display_name": "Surgery"},
            "OpenAI",
            "test-model",
            submission_id="submission-1",
        )
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            self.assertEqual(archive.read("recording.wav"), b"audio-B")
            self.assertEqual(archive.read("transcript.txt"), b"edited B")
            self.assertEqual(archive.read("transcript_original.txt"), b"original B")
            self.assertEqual(
                json.loads(archive.read("metadata.json"))["submission_id"], "submission-1"
            )
            self.assertIn("feedback_report.html", archive.namelist())


class SheetsTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(
            os.environ, {"GOOGLE_CREDENTIALS_JSON": "{}", "GOOGLE_SHEET_ID": "synthetic-sheet"}
        )
        self.env.start()
        self.addCleanup(self.env.stop)
        self.credentials = patch(
            "google.oauth2.service_account.Credentials.from_service_account_info",
            return_value=MagicMock(),
        )
        self.credentials.start()
        self.addCleanup(self.credentials.stop)
        self.gc = MagicMock()
        self.auth = patch("gspread.authorize", return_value=self.gc)
        self.auth.start()
        self.addCleanup(self.auth.stop)
        self.sheet = self.gc.open_by_key.return_value.sheet1
        self.sheet.col_count = 26
        self.sheet.row_values.return_value = sheets_logger._HEADERS.copy()
        self.sheet.col_values.return_value = ["Submission ID"]
        self.feedback = {**SYNTHESIS, "status": "complete"}

    def save(self):
        return sheets_logger.log_submission(
            {},
            {},
            "Synthetic",
            self.feedback,
            8,
            "OpenAI",
            "test-model",
            submission_id="submission-1",
        )

    def test_retry_after_uncertain_append_does_not_duplicate(self):
        def append(*args, **kwargs):
            self.sheet.col_values.return_value = ["Submission ID", "submission-1"]
            raise TimeoutError("request succeeded but response was lost")

        self.sheet.append_row.side_effect = append
        self.assertFalse(self.save()[0])
        self.assertTrue(self.save()[0])
        self.assertEqual(self.sheet.append_row.call_count, 1)

    def test_legacy_headers_are_extended_without_reordering_data(self):
        self.sheet.row_values.return_value = sheets_logger._HEADERS[:-1]
        self.assertTrue(self.save()[0])
        self.assertEqual(self.sheet.update.call_args.kwargs["values"][0], sheets_logger._HEADERS)
        self.assertEqual(self.sheet.append_row.call_args.args[0][21], "submission-1")
        self.assertEqual(self.sheet.append_row.call_args.kwargs["value_input_option"], "RAW")

    def test_large_feedback_json_is_split_losslessly(self):
        self.feedback["extra_detail"] = "x" * 60000
        self.assertTrue(self.save()[0])
        row = self.sheet.append_row.call_args.args[0]
        payload = row[20] + "".join(row[22:])
        self.assertEqual(json.loads(payload), self.feedback)
        self.assertLessEqual(max(map(lambda v: len(str(v)), row)), 45000)

    def test_failed_or_mismatched_data_is_not_saved(self):
        self.feedback["status"] = "failed"
        self.assertFalse(self.save()[0])
        self.sheet.append_row.assert_not_called()
        self.feedback["status"] = "complete"
        self.sheet.row_values.return_value = ["Unrelated column"]
        self.assertFalse(self.save()[0])
        self.sheet.append_row.assert_not_called()

    def test_remote_error_details_are_not_shown_to_student(self):
        self.sheet.append_row.side_effect = RuntimeError("secret credential and patient transcript")
        ok, message = self.save()
        self.assertFalse(ok)
        self.assertNotIn("secret", message)
        self.assertNotIn("patient", message)
