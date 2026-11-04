"""
PRISMA LLM Screener Wrapper Module

Acts as middleware between OpenAlex/patent data and the final 16-column database.
Evaluates research text (titles, abstracts, summaries) against parameterized
inclusion and exclusion criteria using Gemini, with an offline mock fallback.
"""

import json
import os
import random
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

DEFAULT_RULES_FILE = os.path.join(os.path.dirname(__file__), "prisma_rules.json")


def load_screening_rules(rules_path: Optional[str] = None) -> Dict[str, str]:
    """
    Loads inclusion and exclusion rules from a JSON config file.
    Falls back to safe default baseline rules if the file is missing or invalid.
    """
    path_to_use = rules_path or DEFAULT_RULES_FILE
    if os.path.exists(path_to_use):
        try:
            with open(path_to_use, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "include_rules": data.get("include_rules", ""),
                    "exclude_rules": data.get("exclude_rules", ""),
                }
        except Exception:
            pass

    return {
        "include_rules": "vessels under 400 GT, recreational boats, marinas, inland waterways, coastal pollution from small craft.",
        "exclude_rules": "Industrial shipping, oil rigs, tankers, cargo ships over 400 GT, deep-sea oceanic pollution unrelated to coastal harbours.",
    }


def build_system_prompt(include_rules: str, exclude_rules: str) -> str:
    """
    Builds the parameterized PRISMA systematic screening system prompt.
    """
    return f"""You are an expert scientific literature screener applying PRISMA 2020 methodology for marine environmental research (EcoBilge).
Analyze the provided study text (academic abstract or patent summary) against the following inclusion and exclusion rules:

INCLUSION RULES:
{include_rules}

EXCLUSION RULES:
{exclude_rules}

CONSTRAINTS:
1. You must evaluate whether the study meets the inclusion criteria and is NOT disqualified by exclusion criteria.
2. Return ONLY a valid JSON object with EXACTLY two keys:
   - "Keep": boolean (true if the text satisfies the criteria, false otherwise)
   - "Reason": a single 1-sentence string explaining the decision based strictly on the rules.

JSON format:
{{"Keep": true, "Reason": "The study directly investigates bilge oil pollution from vessels under 400 GT in coastal marinas."}}
"""


class PrismaScreener:
    """
    PRISMA Systematic Review Screener.
    Supports Gemini 2.0 Flash via google-genai when GEMINI_API_KEY is present,
    with an offline mock fallback when the key is absent.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.0-flash",
        rules_path: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
        self.model_name = model_name
        self.default_rules = load_screening_rules(rules_path)
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[PrismaScreener] Warning: Failed to initialize live Gemini client ({e}). Defaulting to mock.")
                self.client = None

    def _mock_screen(self, text: str, include_rules: str, exclude_rules: str) -> Dict[str, Any]:
        """
        Mock fallback for offline testing in Hour 7 without requiring an API key.
        Produces a randomized Keep boolean and a clear 1-sentence reason.
        """
        keep = random.choice([True, False])
        if keep:
            reason = "Mock decision: Document matches inclusion criteria for small craft bilge discharge."
        else:
            reason = "Mock decision: Document excluded as it pertains to large commercial tankers or off-target operations."
        return {
            "Keep": keep,
            "Reason": reason,
        }

    def screen_text(
        self,
        text: str,
        include_rules: Optional[str] = None,
        exclude_rules: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Screens an academic abstract or patent summary.

        Args:
            text: Text to evaluate.
            include_rules: Optional override for inclusion rules.
            exclude_rules: Optional override for exclusion rules.

        Returns:
            dict: {"Keep": bool, "Reason": str}
        """
        if not text or not text.strip():
            return {
                "Keep": False,
                "Reason": "Excluded due to empty or missing text.",
            }

        effective_include = (
            include_rules
            if include_rules is not None
            else self.default_rules.get("include_rules", "")
        )
        effective_exclude = (
            exclude_rules
            if exclude_rules is not None
            else self.default_rules.get("exclude_rules", "")
        )

        # Offline fallback if API client is not configured
        if not self.client:
            return self._mock_screen(text, effective_include, effective_exclude)

        prompt = build_system_prompt(effective_include, effective_exclude)
        contents = f"{prompt}\n\nSTUDY TEXT TO SCREEN:\n{text}"

        try:
            from google.genai import types

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0,
                ),
            )

            raw_text = response.text.strip()
            parsed = json.loads(raw_text)

            # Ensure strict JSON schema with keys "Keep" and "Reason"
            keep_val = bool(parsed.get("Keep", False))
            reason_val = str(parsed.get("Reason", "No reason provided."))

            return {
                "Keep": keep_val,
                "Reason": reason_val,
            }
        except Exception as e:
            # Fall back gracefully to mock if live request fails
            print(f"[PrismaScreener] Live screening error: {e}. Falling back to mock response.")
            return self._mock_screen(text, effective_include, effective_exclude)


def screen_record(
    text: str,
    include_rules: Optional[str] = None,
    exclude_rules: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience functional interface for screening a single text string.
    """
    screener = PrismaScreener(api_key=api_key)
    return screener.screen_text(
        text=text,
        include_rules=include_rules,
        exclude_rules=exclude_rules,
    )
