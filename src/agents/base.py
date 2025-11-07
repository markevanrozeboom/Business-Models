"""Base agent class for all specialized agents."""

import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Tuple

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

    def _retry_with_backoff(
        self,
        func: Callable,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,),
    ):
        """
        Retry a function with exponential backoff.
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            backoff_factor: Multiplier for delay between retries
            exceptions: Tuple of exceptions to catch and retry on
            
        Returns:
            Result of function call
        """
        delay = initial_delay
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func()
            except exceptions as e:
                last_exception = e
                if attempt < max_retries:
                    self.logger.warning(
                        "retry_attempt",
                        agent_type=self.agent_type.value,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        error=str(e),
                        delay=delay,
                    )
                    time.sleep(delay)
                    delay *= backoff_factor
                else:
                    self.logger.error(
                        "retry_exhausted",
                        agent_type=self.agent_type.value,
                        max_retries=max_retries,
                        error=str(e),
                    )
        
        raise last_exception

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
        retry: bool = True,
    ) -> Message:
        """
        Create a message using the Anthropic API with retry logic.

        Args:
            messages: List of message dictionaries
            system: System prompt (uses default if not provided)
            max_tokens: Max tokens (uses default if not provided)
            temperature: Temperature (uses default if not provided)
            retry: Whether to retry on failure

        Returns:
            Anthropic Message response
        """
        def _make_request():
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

        if retry:
            return self._retry_with_backoff(
                _make_request,
                max_retries=3,
                initial_delay=1.0,
                exceptions=(Exception,),
            )
        else:
            return _make_request()

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

    def _extract_json_from_response(
        self, 
        text: str, 
        max_attempts: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from Claude's response using multiple strategies.

        Args:
            text: Response text that may contain JSON
            max_attempts: Maximum number of extraction attempts

        Returns:
            Parsed JSON dict or None if not found
        """
        strategies = [
            # Strategy 1: JSON in markdown code block with ```json
            lambda t: self._extract_from_markdown_block(t, "```json"),
            # Strategy 2: JSON in markdown code block with ```
            lambda t: self._extract_from_markdown_block(t, "```"),
            # Strategy 3: JSON object at start of text
            lambda t: self._extract_from_start(t),
            # Strategy 4: Find first { ... } block
            lambda t: self._extract_first_json_block(t),
            # Strategy 5: Find JSON between specific markers
            lambda t: self._extract_between_markers(t),
        ]

        for i, strategy in enumerate(strategies[:max_attempts], 1):
            try:
                result = strategy(text)
                if result is not None:
                    self.logger.debug(
                        "json_extraction_succeeded",
                        agent_type=self.agent_type.value,
                        strategy=i,
                    )
                    return result
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.debug(
                    "json_extraction_strategy_failed",
                    agent_type=self.agent_type.value,
                    strategy=i,
                    error=str(e),
                )
                continue

        self.logger.warning(
            "json_extraction_all_strategies_failed",
            agent_type=self.agent_type.value,
            text_preview=text[:200],
        )
        return None

    def _extract_from_markdown_block(self, text: str, marker: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from markdown code block."""
        if marker not in text:
            return None
        start = text.find(marker) + len(marker)
        end = text.find("```", start)
        if end == -1:
            return None
        json_str = text[start:end].strip()
        # Remove language identifier if present
        if json_str.startswith("json"):
            json_str = json_str[4:].strip()
        return json.loads(json_str)

    def _extract_from_start(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON if text starts with {."""
        text = text.strip()
        if text.startswith("{"):
            return json.loads(text)
        return None

    def _extract_first_json_block(self, text: str) -> Optional[Dict[str, Any]]:
        """Find and extract first complete JSON object."""
        # Find first {
        start_idx = text.find("{")
        if start_idx == -1:
            return None
        
        # Find matching closing }
        depth = 0
        in_string = False
        escape_next = False
        
        for i in range(start_idx, len(text)):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
                
            if char == "\\":
                escape_next = True
                continue
                
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
                
            if not in_string:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        json_str = text[start_idx:i+1]
                        return json.loads(json_str)
        
        return None

    def _extract_between_markers(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON between common markers."""
        markers = [
            ("{", "}"),
            ("```", "```"),
            ("<json>", "</json>"),
        ]
        
        for start_marker, end_marker in markers:
            start = text.find(start_marker)
            if start == -1:
                continue
            start += len(start_marker)
            end = text.find(end_marker, start)
            if end == -1:
                continue
            json_str = text[start:end].strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue
        
        return None

    def _validate_output_completeness(
        self,
        data: Dict[str, Any],
        required_fields: List[str],
        min_required: Optional[int] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Validate that output has required fields populated.
        
        Args:
            data: Output data to validate
            required_fields: List of field paths (e.g., ["market_overview", "comparable_companies"])
            min_required: Minimum number of required fields that must be populated (None = all)
            
        Returns:
            Tuple of (is_valid, missing_fields)
        """
        missing = []
        
        for field in required_fields:
            # Handle nested fields with dot notation
            parts = field.split(".")
            value = data
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break
            
            # Check if field is empty
            is_empty = (
                value is None or
                value == "" or
                (isinstance(value, list) and len(value) == 0) or
                (isinstance(value, dict) and len(value) == 0)
            )
            
            if is_empty:
                missing.append(field)
        
        if min_required is None:
            is_valid = len(missing) == 0
        else:
            is_valid = len(missing) <= (len(required_fields) - min_required)
        
        return is_valid, missing

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
