"""Base agent class for the job search system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from models.schemas import AgentMessage, JobSearchState
from services.llm_service import LLMService, get_llm

if TYPE_CHECKING:
    pass


class BaseAgent(ABC):
    """Abstract base for all job search agents."""

    name: str = "BaseAgent"
    role: str = "Generic agent"
    description: str = ""

    def __init__(self, llm: LLMService | None = None) -> None:
        self.llm = llm or get_llm()

    @abstractmethod
    def run(self, state: JobSearchState) -> JobSearchState:
        """Execute agent logic and return updated state."""

    def log(self, state: JobSearchState, content: str, **metadata) -> None:
        state.agent_messages.append(
            AgentMessage(
                agent_name=self.name,
                role=self.role,
                content=content,
                metadata=metadata,
            )
        )

    def system_prompt(self) -> str:
        return (
            f"You are {self.name}, a specialized AI agent in a job search system. "
            f"Role: {self.role}. {self.description}"
        )
