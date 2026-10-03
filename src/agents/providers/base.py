"""Base interface for pluggable LLM / synthesizer providers in FMEA-GPT."""
from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar, Dict, Any
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract base class for FMEA reasoning providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the inference provider."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> T:
        """Generate a structured response adhering to a Pydantic schema."""
        pass

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate unstructured reasoning text."""
        pass
