"""
Unit and integration test suite for Illustration Agent A2A microservice.
Tests fallback resilience, schema adherence, and simulated failure modes.
"""

import os
import sys
import json
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

# Mock BasePlugin for clean local testing
class MockBasePlugin:
    def __init__(self, name=None):
        self.name = name

# Mock google cloud, adk, and a2a modules if running in an environment without them pre-installed
for mod in ["google.adk", "google.adk.agents", "google.adk.tools.tool_context", 
            "google.adk.models", "google.adk.apps.app",
            "google.adk.models.llm_request", "google.adk.agents.callback_context",
            "a2a.types", "google.genai", "google.genai.types",
            "google.cloud", "google.cloud.storage", "google.auth",
            "google.auth.impersonated_credentials"]:
    if mod not in sys.modules:
        mock_mod = MagicMock()
        sys.modules[mod] = mock_mod

mock_plugins_mod = MagicMock()
mock_plugins_mod.BasePlugin = MockBasePlugin
sys.modules["google.adk.plugins"] = mock_plugins_mod

import illustration_agent.agent as agent_module
from illustration_agent.agent import _get_fallback_image_url, generate_image, FALLBACK_TRAINING_URL, FALLBACK_STADIUM_URL
from illustration_agent.adk_utils.plugins import LabExUtils


class TestIllustrationAgentFallback(unittest.TestCase):

    def test_agent_json_specification(self):
        """Validates that agent.json adheres to the Agent-to-Agent (A2A) protocol specification."""
        agent_json_path = os.path.join(BASE_DIR, "illustration_agent", "agent.json")
        self.assertTrue(os.path.exists(agent_json_path), "agent.json must exist")
        
        with open(agent_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("name"), "illustration_agent")
        self.assertIn("text/plain", data.get("defaultInputModes", []))
        self.assertIn("application/json", data.get("defaultOutputModes", []))
        
        skills = data.get("skills", [])
        self.assertTrue(any(s.get("id") == "illustrate_text" for s in skills), "illustrate_text skill required")
        self.assertTrue(data.get("url", "").startswith("https://"), "Valid HTTPS endpoint URL required")
        
        # Verify deployment metadata
        capabilities = data.get("capabilities", {})
        self.assertEqual(capabilities.get("status"), "archived_training_reference")

    def test_fallback_image_url_selection(self):
        """Verifies keyword-based fallback image routing."""
        # Training / learning keywords
        self.assertEqual(_get_fallback_image_url("New mentor training program on field"), FALLBACK_TRAINING_URL)
        self.assertEqual(_get_fallback_image_url("Apprentice maintenance onboarding"), FALLBACK_TRAINING_URL)
        
        # General / stadium maintenance keywords
        self.assertEqual(_get_fallback_image_url("Stadium lights and turf maintenance"), FALLBACK_STADIUM_URL)
        self.assertEqual(_get_fallback_image_url("General announcement for fans"), FALLBACK_STADIUM_URL)

    def test_generate_image_fallback_contract(self):
        """
        Verifies that generate_image NEVER crashes on unauthenticated calls
        and ALWAYS returns the required dictionary contract {"image_url": str}.
        """
        res = generate_image("Test stadium lights prompt without credentials")
        self.assertIsInstance(res, dict)
        self.assertIn("image_url", res)
        self.assertTrue(res["image_url"].startswith("https://"))

    def test_simulate_network_timeout(self):
        """Simulates network timeout during Gemini content generation."""
        with patch.object(agent_module.client.models, 'generate_content', side_effect=TimeoutError("Connection timed out")):
            res = generate_image("Network timeout scenario")
            self.assertIsInstance(res, dict)
            self.assertEqual(res.get("image_url"), FALLBACK_STADIUM_URL)

    def test_simulate_429_quota_exhaustion(self):
        """Simulates 429 RESOURCE_EXHAUSTED error during image generation."""
        with patch.object(agent_module.client.models, 'generate_content', side_effect=Exception("429 RESOURCE_EXHAUSTED")):
            res = generate_image("Staff training session on turf")
            self.assertIsInstance(res, dict)
            self.assertEqual(res.get("image_url"), FALLBACK_TRAINING_URL)

    def test_simulate_auth_failure(self):
        """Simulates GCP credential resolution failure."""
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.content.parts = [MagicMock()]
        mock_candidate.content.parts[0].inline_data.data = b"fake_png_data"
        mock_response.candidates = [mock_candidate]

        with patch.object(agent_module.client.models, 'generate_content', return_value=mock_response):
            with patch('illustration_agent.agent.default', side_effect=Exception("DefaultCredentialsError: Missing GCP ADC credentials")):
                res = generate_image("Authentication failure scenario")
                self.assertIsInstance(res, dict)
                self.assertIn("image_url", res)
                self.assertTrue(res["image_url"].startswith("https://"))

    def test_simulate_gcs_upload_failure(self):
        """Simulates Google Cloud Storage 503 upload failure."""
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.content.parts = [MagicMock()]
        mock_candidate.content.parts[0].inline_data.data = b"fake_png_data"
        mock_response.candidates = [mock_candidate]

        mock_storage_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.upload_from_string.side_effect = Exception("503 Service Unavailable: Storage upload error")
        mock_bucket.blob.return_value = mock_blob
        mock_storage_client.bucket.return_value = mock_bucket

        with patch.object(agent_module.client.models, 'generate_content', return_value=mock_response):
            with patch('illustration_agent.agent.storage.Client', return_value=mock_storage_client):
                res = generate_image("GCS upload outage scenario")
                self.assertIsInstance(res, dict)
                self.assertIn("image_url", res)
                self.assertTrue(res["image_url"].startswith("https://"))

    def test_plugin_keyword_fallback(self):
        """Verifies that LabExUtils plugin returns structured fallback responses."""
        plugin = LabExUtils()
        fallback_resp = plugin._find_best_fallback("announcement for supporting each other in stadium")
        self.assertIn("Prompt Used:", fallback_resp)
        self.assertIn("Generated Illustration:", fallback_resp)


if __name__ == "__main__":
    unittest.main()
