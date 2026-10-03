"""External LLM provider supporting OpenAI, Gemini, Anthropic, or local OpenAI-compatible endpoints."""
import os
import json
from typing import Optional, Type, TypeVar, Dict, Any
from pydantic import BaseModel

from .base import LLMProvider
from .local_synthesizer import LocalAerospaceSynthesizer

T = TypeVar("T", bound=BaseModel)


class ExternalLLMProvider(LLMProvider):
    """Integrates with external LLMs (OpenAI, Gemini, vLLM, Ollama) with fallback to LocalSynthesizer."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        provider_type: str = "openai"
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("LLM_MODEL_NAME") or "gpt-4o-mini"
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.provider_type = provider_type.lower()
        self.fallback = LocalAerospaceSynthesizer()

    @property
    def provider_name(self) -> str:
        return f"External LLM Provider ({self.model_name})"

    def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> T:
        """Attempt API call; if unavailable or unconfigured, gracefully fallback to local synthesizer."""
        if not self.api_key and not self.base_url:
            return self.fallback.generate_structured(prompt, response_model, system_prompt, context)

        try:
            import httpx
            # Standard OpenAI-compatible chat completion payload
            headers = {"Authorization": f"Bearer {self.api_key or 'local'}"}
            url = f"{self.base_url.rstrip('/') if self.base_url else 'https://api.openai.com/v1'}/chat/completions"

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }

            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    content_str = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content_str)
                    return response_model.model_validate(parsed)
        except Exception:
            pass

        # Fallback to offline domain synthesizer
        return self.fallback.generate_structured(prompt, response_model, system_prompt, context)

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        if not self.api_key and not self.base_url:
            return self.fallback.generate_text(prompt, system_prompt, context)

        try:
            import httpx
            headers = {"Authorization": f"Bearer {self.api_key or 'local'}"}
            url = f"{self.base_url.rstrip('/') if self.base_url else 'https://api.openai.com/v1'}/chat/completions"
            messages = [{"role": "user", "content": prompt}]
            if system_prompt:
                messages.insert(0, {"role": "system", "content": system_prompt})

            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json={"model": self.model_name, "messages": messages}, headers=headers)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
        except Exception:
            pass

        return self.fallback.generate_text(prompt, system_prompt, context)
