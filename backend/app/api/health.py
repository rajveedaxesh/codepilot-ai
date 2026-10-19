from fastapi import APIRouter
from backend.app.config import settings
from backend.app.ai.factory import get_llm_provider

router = APIRouter(tags=["Health & Diagnostics"])

@router.get("/health")
def health_check():
    provider = get_llm_provider()
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "env": settings.APP_ENV,
        "llm_provider": provider.provider_name,
        "anthropic_configured": bool(settings.ANTHROPIC_API_KEY),
        "sandboxing_enabled": settings.ENABLE_ISOLATED_VERIFICATION
    }

@router.get("/settings")
def get_current_settings():
    provider = get_llm_provider()
    return {
        "app_name": settings.APP_NAME,
        "llm_provider": settings.LLM_PROVIDER,
        "active_provider_name": provider.provider_name,
        "anthropic_model": settings.ANTHROPIC_MODEL,
        "anthropic_configured": bool(settings.ANTHROPIC_API_KEY),
        "max_tokens": settings.MAX_TOKENS,
        "execution_timeout_seconds": settings.EXECUTION_TIMEOUT_SECONDS,
        "allowed_commands": settings.ALLOWED_COMMAND_PREFIXES
    }
