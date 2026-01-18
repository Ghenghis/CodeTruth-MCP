"""
Ollama Integration

Provides integration with Ollama for local LLM inference.
Supports various open-source models like Llama, Mistral, CodeLlama, etc.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class OllamaConfig(BaseModel):
    """Configuration for Ollama connection."""

    host: str = Field(default="localhost")
    port: int = Field(default=11434)

    # Model settings
    model: str = Field(default="codellama:7b")
    temperature: float = Field(default=0.7)
    num_predict: int = Field(default=2048)
    top_p: float = Field(default=0.95)

    # Timeout
    timeout: float = Field(default=300.0)

    @property
    def base_url(self) -> str:
        """Get the base URL for API calls."""
        return f"http://{self.host}:{self.port}"


class OllamaClient:
    """
    Client for Ollama local LLM inference.

    Ollama runs various open-source models locally.
    Recommended models for code analysis:
    - codellama:7b - General code tasks
    - codellama:13b - Better quality, slower
    - deepseek-coder:6.7b - Good for code
    - mistral:7b - General purpose
    - llama3:8b - Latest Llama model
    """

    def __init__(self, config: OllamaConfig | None = None):
        self.config = config or OllamaConfig()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "OllamaClient":
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def is_available(self) -> bool:
        """Check if Ollama is running and available."""
        try:
            if not self._client:
                self._client = httpx.AsyncClient(
                    base_url=self.config.base_url,
                    timeout=5.0,
                )

            response = await self._client.get("/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False

    async def get_models(self) -> list[dict[str, Any]]:
        """Get list of available models."""
        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )

        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return []

    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry."""
        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )

        try:
            response = await self._client.post(
                "/api/pull",
                json={"name": model_name},
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        num_predict: int | None = None,
    ) -> str:
        """
        Generate a completion.

        Args:
            prompt: The prompt to complete
            system: Optional system prompt
            temperature: Override default temperature
            num_predict: Override default max tokens

        Returns:
            Generated text
        """
        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
                "num_predict": num_predict or self.config.num_predict,
                "top_p": self.config.top_p,
            },
        }

        if system:
            payload["system"] = system

        try:
            response = await self._client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        num_predict: int | None = None,
    ) -> AsyncIterator[str]:
        """
        Generate a streaming completion.

        Yields:
            Chunks of generated text
        """
        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature or self.config.temperature,
                "num_predict": num_predict or self.config.num_predict,
                "top_p": self.config.top_p,
            },
        }

        if system:
            payload["system"] = system

        try:
            async with self._client.stream(
                "POST",
                "/api/generate",
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            chunk = data.get("response", "")
                            if chunk:
                                yield chunk

                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise

    async def chat(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
    ) -> str:
        """
        Send a chat request.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: Optional system prompt

        Returns:
            Assistant response
        """
        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )

        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.num_predict,
            },
        }

        if system:
            payload["messages"] = [{"role": "system", "content": system}] + messages

        try:
            response = await self._client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise

    async def analyze_code(
        self,
        code: str,
        language: str,
        analysis_type: str = "review",
    ) -> dict[str, Any]:
        """
        Analyze code using the local LLM.

        Args:
            code: Source code to analyze
            language: Programming language
            analysis_type: Type of analysis

        Returns:
            Analysis results
        """
        system = "You are an expert code analyzer. Be concise and specific."

        prompts = {
            "review": f"Review this {language} code for bugs, issues, and improvements:\n\n```{language}\n{code}\n```",
            "security": f"Security audit this {language} code:\n\n```{language}\n{code}\n```",
            "performance": f"Analyze performance of this {language} code:\n\n```{language}\n{code}\n```",
        }

        prompt = prompts.get(analysis_type, prompts["review"])

        response = await self.generate(prompt, system=system)

        return {
            "analysis_type": analysis_type,
            "language": language,
            "response": response,
            "model": self.config.model,
        }
