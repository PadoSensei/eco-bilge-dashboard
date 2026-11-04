import unittest
from unittest.mock import MagicMock
import json
import os
import prisma_screener
from prisma_screener import PrismaScreener, load_screening_rules, build_system_prompt, screen_record


class TestPrismaScreener(unittest.TestCase):
    def test_load_default_screening_rules(self):
        rules = load_screening_rules()
        self.assertIn("include_rules", rules)
        self.assertIn("exclude_rules", rules)
        self.assertIn("vessels under 400 GT", rules["include_rules"])
        self.assertIn("tankers", rules["exclude_rules"])

    def test_build_system_prompt_parameterization(self):
        inc = "Test inclusion criteria"
        exc = "Test exclusion criteria"
        prompt = build_system_prompt(inc, exc)
        self.assertIn("Test inclusion criteria", prompt)
        self.assertIn("Test exclusion criteria", prompt)
        self.assertIn('"Keep"', prompt)
        self.assertIn('"Reason"', prompt)

    def test_mock_fallback_structure_and_types(self):
        screener = PrismaScreener(api_key=None)
        self.assertIsNone(screener.client)

        result = screener.screen_text("Study on bilge water from small motorboats")
        self.assertIsInstance(result, dict)
        self.assertIn("Keep", result)
        self.assertIn("Reason", result)
        self.assertIsInstance(result["Keep"], bool)
        self.assertIsInstance(result["Reason"], str)
        self.assertTrue(len(result["Reason"]) > 0)

    def test_empty_text_handling(self):
        screener = PrismaScreener(api_key=None)
        result = screener.screen_text("   ")
        self.assertFalse(result["Keep"])
        self.assertIn("empty", result["Reason"].lower())

    def test_custom_rule_overrides(self):
        screener = PrismaScreener(api_key=None)
        # Verify passing custom rules runs without error in mock and function signatures
        result = screener.screen_text(
            text="Patent for small vessel separator",
            include_rules="Custom inclusion rule",
            exclude_rules="Custom exclusion rule",
        )
        self.assertIn("Keep", result)
        self.assertIn("Reason", result)

    def test_convenience_function(self):
        result = screen_record("Abstract about oil bilge separator")
        self.assertIn("Keep", result)
        self.assertIn("Reason", result)

    def test_live_client_mocking(self):
        # Test simulated Gemini API response with strict JSON
        screener = PrismaScreener(api_key="fake-key-for-test")
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "Keep": True,
            "Reason": "The paper focuses specifically on recreational craft bilge water oil content."
        })
        mock_client.models.generate_content.return_value = mock_response
        screener.client = mock_client

        result = screener.screen_text("Recreational craft bilge water oil content evaluation")
        self.assertTrue(result["Keep"])
        self.assertEqual(result["Reason"], "The paper focuses specifically on recreational craft bilge water oil content.")


if __name__ == "__main__":
    unittest.main()
