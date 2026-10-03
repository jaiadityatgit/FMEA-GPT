"""Factory for creating the appropriate FMEA LLM / reasoning provider."""
import os
from typing import Optional
from .base import LLMProvider
from .local_synthesizer import LocalAerospaceSynthesizer
from .external_llm import ExternalLLMProvider


def get_llm_provider(force_provider: Optional[str] = None) -> LLMProvider:
    """Return the configured reasoning provider. Defaults to LocalAerospaceSynthesizer."""
    provider_choice = (force_provider or os.getenv("FMEA_INFERENCE_PROVIDER", "local")).lower()

    if provider_choice in ["openai", "external", "remote", "gemini"]:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        if api_key or base_url:
            return ExternalLLMProvider(api_key=api_key, base_url=base_url)

    # Default to 100% offline local synthesizer
    return LocalAerospaceSynthesizer()
