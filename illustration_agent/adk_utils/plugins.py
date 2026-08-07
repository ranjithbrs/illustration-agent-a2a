import os
from google.adk.plugins import BasePlugin
from google.adk.models import LlmResponse
from google.adk.models.llm_request import LlmRequest
from google.genai import types
from google.adk.agents.callback_context import CallbackContext
from .cached_responses import cached_responses

class LabExUtils(BasePlugin):
    """Intercepts local failures to Vertex AI and handles them globally via ADK hooks."""
    
    def __init__(self):
        super().__init__(name="lab_ex_utils")

    async def on_model_error_callback(self, *, callback_context: CallbackContext, llm_request: LlmRequest, error: Exception) -> LlmResponse | None:
        """Global hook catch-all for errors emitted by any agent attached to this App."""
        if getattr(error, 'code', None) == 429:
            fallback_text = self._find_best_fallback(str(llm_request))
            
            return LlmResponse(
                content=types.Content(
                    role="model", 
                    parts=[types.Part.from_text(text=fallback_text)]
                )
            )
        raise error

    def _find_best_fallback(self, prompt: str) -> str:
        """Scan the prompt for keywords using reverse-find to match the latest context."""
        prompt_lower = prompt.lower()
        best_keyword, best_index = None, -1

        for keyword in cached_responses:
            if keyword == "default":
                continue
            idx = prompt_lower.rfind(keyword.lower())
            if idx > best_index:
                best_index, best_keyword = idx, keyword

        # Return the matched response, or tip over to our fallback default
        return cached_responses.get(best_keyword or "default", "We’re experiencing high demand right now. To stay on track, please skip this step for now and continue with the next part of the lab. You can try this prompt again in a few minutes.")