from __future__ import annotations

import os
from typing import Optional


class GeminiClient:
    """
    Client interface for Google Generative AI (Gemini).
    Provides stubs and safe fallbacks when real Gemini is not configured.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel("gemini-1.5-flash")
            except Exception:
                self._client = None

    @property
    def is_available(self) -> bool:
        """Returns True if the real Gemini client is ready and configured."""
        return self._client is not None

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Generates content using Gemini if available, or returns a structured mock response.
        """
        if self.is_available and self._client:
            try:
                response = self._client.generate_content(prompt)
                return response.text
            except Exception as e:
                return f"[Gemini Error: {e} - Falling back to mock]"

        # Default mock response when real Gemini is not active
        return (
            "[Mock Gemini Response] This is a placeholder response for the prompt. "
            "Real Gemini calls will be activated once an API key is configured."
        )


# Global LLM instance
llm_client = GeminiClient()
