"""
LM Studio Integration

Provides integration with LM Studio for local AI model inference.
LM Studio runs OpenAI-compatible API locally.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LMStudioConfig(BaseModel):
    """Configuration for LM Studio connection."""

    host: str = Field(default="localhost")
    port: int = Field(default=1234)
    api_path: str = Field(default="/v1")

    # Model settings
    model: str = Field(default="local-model")  # LM Studio uses loaded model
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=2048)
    top_p: float = Field(default=0.95)

    # Timeout
    timeout: float = Field(default=120.0)

    @property
    def base_url(self) -> str:
        """Get the base URL for API calls."""
        return f"http://{self.host}:{self.port}{self.api_path}"


class LMStudioClient:
    """
    Client for LM Studio local AI inference.

    LM Studio provides an OpenAI-compatible API endpoint
    for running local LLMs with GPU acceleration.
    """

    def __init__(self, config: LMStudioConfig | None = None):
        self.config = config or LMStudioConfig()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "LMStudioClient":
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
        """Check if LM Studio is running and available."""
        try:
            if not self._client:
                self._client = httpx.AsyncClient(
                    base_url=self.config.base_url,
                    timeout=5.0,
                )

            response = await self._client.get("/models")
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"LM Studio not available: {e}")
            return False

    async def get_models(self) -> list[dict[str, Any]]:
        """Get list of available models."""
        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )

        try:
            response = await self._client.get("/models")
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return []

    async def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Send a chat completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt to prepend
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            The assistant's response text
        """
        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )

        all_messages = []

        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})

        all_messages.extend(messages)

        payload = {
            "model": self.config.model,
            "messages": all_messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "top_p": self.config.top_p,
            "stream": False,
        }

        try:
            response = await self._client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return ""

        except Exception as e:
            logger.error(f"Chat request failed: {e}")
            raise

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """
        Send a streaming chat completion request.

        Yields:
            Chunks of the assistant's response
        """
        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )

        all_messages = []

        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})

        all_messages.extend(messages)

        payload = {
            "model": self.config.model,
            "messages": all_messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "top_p": self.config.top_p,
            "stream": True,
        }

        try:
            async with self._client.stream(
                "POST",
                "/chat/completions",
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"Streaming chat failed: {e}")
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
            analysis_type: Type of analysis (review, security, performance, etc.)

        Returns:
            Analysis results
        """
        prompts = {
            "review": f"""Analyze this {language} code and identify:
1. Potential bugs or issues
2. Code quality concerns
3. Suggestions for improvement

Be specific and cite line numbers where applicable.

```{language}
{code}
```""",
            "security": f"""Perform a security analysis of this {language} code:
1. Identify potential vulnerabilities (SQL injection, XSS, etc.)
2. Check for insecure patterns
3. Suggest security improvements

```{language}
{code}
```""",
            "performance": f"""Analyze the performance of this {language} code:
1. Identify performance bottlenecks
2. Check for inefficient patterns
3. Suggest optimizations

```{language}
{code}
```""",
            "dead_code": f"""Analyze this {language} code for dead or unreachable code:
1. Identify unused variables
2. Find unreachable code paths
3. Detect unused functions or methods

```{language}
{code}
```""",
        }

        prompt = prompts.get(analysis_type, prompts["review"])

        response = await self.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are an expert code analyzer. Provide detailed, actionable feedback.",
        )

        return {
            "analysis_type": analysis_type,
            "language": language,
            "response": response,
            "model": self.config.model,
        }

    async def explain_finding(
        self,
        finding: dict[str, Any],
        context: str | None = None,
    ) -> str:
        """
        Get an explanation for an audit finding.

        Args:
            finding: The finding to explain
            context: Optional additional context

        Returns:
            Explanation of the finding
        """
        prompt = f"""Explain this code audit finding in simple terms:

**Type:** {finding.get('type', 'Unknown')}
**Severity:** {finding.get('severity', 'Unknown')}
**Message:** {finding.get('message', 'No message')}
**File:** {finding.get('file', 'Unknown')}
**Line:** {finding.get('line', 'Unknown')}

{f"Additional context: {context}" if context else ""}

Please explain:
1. What this issue means
2. Why it matters
3. How to fix it
"""

        return await self.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a helpful code review assistant. Explain issues clearly.",
        )

    async def suggest_fix(
        self,
        code: str,
        finding: dict[str, Any],
        language: str,
    ) -> str:
        """
        Suggest a fix for a finding.

        Args:
            code: The problematic code
            finding: The finding to fix
            language: Programming language

        Returns:
            Suggested fix
        """
        prompt = f"""Suggest a fix for this issue:

**Issue:** {finding.get('message', 'Unknown issue')}
**Severity:** {finding.get('severity', 'Unknown')}

Current code:
```{language}
{code}
```

Please provide:
1. The corrected code
2. Brief explanation of the changes
"""

        return await self.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are an expert programmer. Provide concise, correct fixes.",
        )
