import contextlib
import importlib
import io
import unittest
from unittest.mock import patch

import test_system
from presentiq.ai.pipeline import PRESENTATION_FORMATS
from presentiq.services import SERVICE_CONTEXTS
from presentiq.web.portal import load_clerkship_config


class SystemChecks(unittest.TestCase):
    def test_required_packages_import(self):
        for package in [
            "streamlit",
            "openai",
            "fastapi",
            "uvicorn",
            "pydantic",
            "yaml",
            "dotenv",
            "gspread",
            "google.auth",
            "httpx",
        ]:
            with self.subTest(package=package):
                importlib.import_module(package)

    def test_case_references_are_valid(self):
        for clerkship in load_clerkship_config()["clerkships"].values():
            for case in clerkship["cases"]:
                self.assertIn(case["service"], SERVICE_CONTEXTS)
                self.assertIn(case["presentation_format"], PRESENTATION_FORMATS)

    def test_runner_fails_when_a_test_fails(self):
        class DeliberateFailure(unittest.TestCase):
            def runTest(self):
                self.fail("Synthetic failure")

        with (
            patch(
                "unittest.defaultTestLoader.discover",
                return_value=unittest.TestSuite([DeliberateFailure()]),
            ),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(test_system.main(), 1)

    def test_runner_fails_when_no_tests_were_discovered(self):
        with (
            patch("unittest.defaultTestLoader.discover", return_value=unittest.TestSuite()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(test_system.main(), 1)
