"""Azure OpenAI tool wrapper for CivicNav.

Provides async methods for chat completion and embeddings using
Azure OpenAI with DefaultAzureCredential for authentication.
"""

import logging
from typing import Any

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)


class OpenAITool:
    """Wrapper for Azure OpenAI operations.

    Uses DefaultAzureCredential for authentication, supporting both
    local development (Azure CLI) and production (managed identity).
    """

    def __init__(self) -> None:
        """Initialize the OpenAI tool with Azure credentials."""
        self.settings = get_settings()
        self._client: AsyncAzureOpenAI | None = None

    @property
    def client(self) -> AsyncAzureOpenAI:
        """Get or create the AsyncAzureOpenAI client."""
        if self._client is None:
            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(
                credential, "https://cognitiveservices.azure.com/.default"
            )
            self._client = AsyncAzureOpenAI(
                azure_endpoint=self.settings.azure_openai_endpoint,
                azure_ad_token_provider=token_provider,
                api_version=self.settings.azure_openai_api_version,
            )
        return self._client

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Generate a chat completion using Azure OpenAI.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            response_format: Optional response format specification

        Returns:
            The assistant's response text
        """
        logger.debug(f"Chat completion with {len(messages)} messages")

        kwargs: dict[str, Any] = {
            "model": self.settings.azure_openai_chat_deployment,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            kwargs["response_format"] = response_format

        response = await self.client.chat.completions.create(**kwargs)

        content = response.choices[0].message.content or ""
        logger.debug(f"Chat completion response: {len(content)} chars")
        return content

    async def create_embedding(self, text: str) -> list[float]:
        """Create an embedding vector for the given text.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector
        """
        logger.debug(f"Creating embedding for text: {len(text)} chars")

        response = await self.client.embeddings.create(
            model=self.settings.azure_openai_embedding_deployment,
            input=text,
        )

        embedding = response.data[0].embedding
        logger.debug(f"Created embedding with {len(embedding)} dimensions")
        return embedding

    async def check_connection(self) -> bool:
        """Check if the OpenAI service is accessible.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Simple test with minimal tokens
            await self.chat_completion(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
            )
            return True
        except Exception as e:
            logger.warning(f"OpenAI connection check failed: {e}")
            return False


# Global instance for convenience
_openai_tool: OpenAITool | None = None


def get_openai_tool() -> OpenAITool:
    """Get the global OpenAI tool instance."""
    global _openai_tool
    if _openai_tool is None:
        _openai_tool = OpenAITool()
    return _openai_tool
