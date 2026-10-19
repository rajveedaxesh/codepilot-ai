import logging
from backend.app.config import settings
from backend.app.ai.provider_base import LLMProvider
from backend.app.ai.mock_provider import MockAIProvider

logger = logging.getLogger(__name__)

def get_llm_provider() -> LLMProvider:
    """Factory to retrieve active LLM provider based on settings and available keys."""
    if settings.LLM_PROVIDER.lower() == "anthropic" and settings.ANTHROPIC_API_KEY:
        try:
            from backend.app.ai.anthropic_provider import AnthropicProvider
            return AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY, model=settings.ANTHROPIC_MODEL)
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic provider ({e}); falling back to mock provider.")
            return MockAIProvider()
    
    # Default offline mock provider
    return MockAIProvider()
