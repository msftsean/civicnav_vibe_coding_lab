"""Abstract base class for CivicNav agents.

All agents in the pipeline inherit from BaseAgent and implement
the async run() method to process inputs and return AgentResult.
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from app.models.schemas import AgentResult

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Abstract base class for all CivicNav agents.

    Each agent in the pipeline (Query, Retrieve, Answer) inherits from this
    base class and implements the run() method to process inputs.

    Attributes:
        name: Human-readable name for the agent
        tools_used: List of tool names used during execution
    """

    def __init__(self, name: str) -> None:
        """Initialize the agent.

        Args:
            name: Human-readable name for the agent
        """
        self.name = name
        self.tools_used: list[str] = []

    @abstractmethod
    async def run(self, input_data: InputT) -> AgentResult:
        """Process input and return structured result.

        Args:
            input_data: The input to process (type varies by agent)

        Returns:
            AgentResult containing output, reasoning, tools used, and latency
        """
        pass

    async def execute(self, input_data: InputT) -> AgentResult:
        """Execute the agent with timing and error handling.

        This wrapper method handles timing, error capture, and result
        formatting for all agent implementations.

        Args:
            input_data: The input to process

        Returns:
            AgentResult with timing information
        """
        start_time = time.perf_counter()
        self.tools_used = []

        try:
            result = await self.run(input_data)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            result.latency_ms = elapsed_ms
            result.tools_used = self.tools_used
            return result
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return AgentResult(
                output=None,
                reasoning=f"Error in {self.name}: {str(e)}",
                tools_used=self.tools_used,
                latency_ms=elapsed_ms,
            )

    def use_tool(self, tool_name: str) -> None:
        """Record that a tool was used during execution.

        Args:
            tool_name: Name of the tool that was invoked
        """
        self.tools_used.append(tool_name)
