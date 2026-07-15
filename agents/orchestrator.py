"""Agent 10: Orchestrator — delegates to LangGraph workflow."""

from __future__ import annotations

from agents.base import BaseAgent
from models.schemas import JobSearchState, UserProfile


class OrchestratorAgent(BaseAgent):
    name = "Orchestrator"
    role = "LangGraph Multi-Agent Coordinator"
    description = (
        "Coordinate the full job search pipeline via LangGraph StateGraph "
        "across 9 specialist agents plus report generation."
    )

    def run(self, state: JobSearchState) -> JobSearchState:
        from graph.workflow import run_pipeline

        return run_pipeline(
            profile=state.user_profile,
            search_query=state.search_query,
        )

    def run_pipeline(
        self,
        profile: UserProfile | None = None,
        search_query: str = "",
    ) -> JobSearchState:
        from graph.workflow import run_pipeline

        return run_pipeline(profile=profile, search_query=search_query)
