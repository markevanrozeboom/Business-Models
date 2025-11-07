"""Base agent class for all specialized agents."""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from anthropic import Anthropic, AsyncAnthropic
from anthropic.types import Message

from ..models.schemas import AgentType, AgentResponse
from ..utils.config import settings
from ..utils.logger import get_logger


class BaseAgent(ABC):
    """Base class for all agents in the system."""

    def __init__(
        self,
        agent_type: AgentType,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ):
        """
        Initialize the base agent.

        Args:
            agent_type: Type of agent
            model: Claude model to use (defaults to settings)
            max_tokens: Maximum tokens for response (defaults to settings)
            temperature: Temperature for response generation (defaults to settings)
        """
        self.agent_type = agent_type
        self.model = model or settings.default_model
        self.max_tokens = max_tokens or settings.default_max_tokens
        self.temperature = temperature or settings.default_temperature

        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.async_client = AsyncAnthropic(api_key=settings.anthropic_api_key)

        self.logger = get_logger(f"agent.{agent_type.value}")

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.

        Returns:
            System prompt string
        """
        pass

    @abstractmethod
    def process(self, input_data: Any) -> AgentResponse:
        """
        Process input and return response.

        Args:
            input_data: Input data for processing

        Returns:
            AgentResponse with results
        """
        pass

    def _create_message(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Message:
        """
        Create a message using the Anthropic API.

        Args:
            messages: List of message dictionaries
            system: System prompt (uses default if not provided)
            max_tokens: Max tokens (uses default if not provided)
            temperature: Temperature (uses default if not provided)

        Returns:
            Anthropic Message response
        """
        try:
            self.logger.info(
                "creating_message",
                agent_type=self.agent_type.value,
                model=self.model,
                num_messages=len(messages),
            )

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                system=system or self.get_system_prompt(),
                messages=messages,
            )

            self.logger.info(
                "message_created",
                agent_type=self.agent_type.value,
                stop_reason=response.stop_reason,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

            return response

        except Exception as e:
            self.logger.error(
                "message_creation_failed",
                agent_type=self.agent_type.value,
                error=str(e),
            )
            raise

    async def _create_message_async(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Message:
        """
        Create a message asynchronously using the Anthropic API.

        Args:
            messages: List of message dictionaries
            system: System prompt (uses default if not provided)
            max_tokens: Max tokens (uses default if not provided)
            temperature: Temperature (uses default if not provided)

        Returns:
            Anthropic Message response
        """
        try:
            self.logger.info(
                "creating_message_async",
                agent_type=self.agent_type.value,
                model=self.model,
                num_messages=len(messages),
            )

            response = await self.async_client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                system=system or self.get_system_prompt(),
                messages=messages,
            )

            self.logger.info(
                "message_created_async",
                agent_type=self.agent_type.value,
                stop_reason=response.stop_reason,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

            return response

        except Exception as e:
            self.logger.error(
                "message_creation_failed_async",
                agent_type=self.agent_type.value,
                error=str(e),
            )
            raise

    def _extract_json_from_response(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from Claude's response.

        Args:
            text: Response text that may contain JSON

        Returns:
            Parsed JSON dict or None if not found
        """
        try:
            # Try to find JSON in markdown code blocks
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                json_str = text[start:end].strip()
                return json.loads(json_str)

            # Try to find JSON object directly
            if text.strip().startswith("{"):
                return json.loads(text.strip())

            return None

        except json.JSONDecodeError as e:
            self.logger.warning(
                "json_extraction_failed",
                agent_type=self.agent_type.value,
                error=str(e),
            )
            return None

    def create_response(
        self,
        success: bool,
        message: str,
        data: Optional[Any] = None,
        confidence_score: Optional[float] = None,
        requires_human_review: bool = False,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        **kwargs,
    ) -> AgentResponse:
        """
        Create a standardized agent response.

        Args:
            success: Whether the operation was successful
            message: Response message
            data: Response data
            confidence_score: Confidence score (0-100)
            requires_human_review: Whether human review is needed
            errors: List of errors
            warnings: List of warnings
            **kwargs: Additional metadata

        Returns:
            AgentResponse object
        """
        return AgentResponse(
            agent_type=self.agent_type,
            success=success,
            message=message,
            data=data,
            confidence_score=confidence_score,
            requires_human_review=requires_human_review,
            errors=errors or [],
            warnings=warnings or [],
            metadata=kwargs,
        )
