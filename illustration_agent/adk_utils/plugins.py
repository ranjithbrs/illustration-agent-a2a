import os
import logging
from google.adk.plugins import BasePlugin
from google.adk.models import LlmResponse
from google.adk.models.llm_request import LlmRequest
from google.genai import types
from google.adk.agents.callback_context import CallbackContext
from .cached_responses import cached_responses

logger = logging.getLogger("LabExUtils")

class LabExUtils(BasePlugin):
    """Intercepts failures to Vertex AI and handles them globally via ADK hooks."""
    
    def __init__(self):
        super().__init__(name="lab_ex_utils")

    async def on_model_error_callback(self, *, callback_context: CallbackContext, llm_request: LlmRequest, error: Exception) -> LlmResponse | None:
        """Global hook catch-all for errors emitted by any agent attached to this App."""
        error_code = getattr(error, 'code', None)
        error_msg = str(error)

        if error_code == 429 or "RESOURCE_EXHAUSTED" in error_msg:
            logger.warning("[ADK PLUGIN] Intercepted 429 Quota Exhaustion from LLM. Serving cached fallback response.")
        else:
            logger.warning(f"[ADK PLUGIN] Intercepted model error ({error}). Serving structured fallback response.")

        fallback_text = self._find_best_fallback(str(llm_request))
        return LlmResponse(
            content=types.Content(
                role="model", 
                parts=[types.Part.from_text(text=fallback_text)]
            )
        )

    def _find_best_fallback(self, prompt: str) -> str:
        """Scan prompt for keywords using reverse-find to match the latest context."""
        prompt_lower = prompt.lower()
        best_keyword, best_index = None, -1

        for keyword in cached_responses:
            if keyword == "default":
                continue
            idx = prompt_lower.rfind(keyword.lower())
            if idx > best_index:
                best_index, best_keyword = idx, keyword

        # Return matched response or default stadium maintenance fallback
        return cached_responses.get(
            best_keyword or "default",
            cached_responses.get("supporting")
        )
