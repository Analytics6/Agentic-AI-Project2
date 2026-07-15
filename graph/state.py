"""LangGraph state definition and conversion helpers."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from models.schemas import JobSearchState, UserProfile


class GraphState(TypedDict, total=False):
    """LangGraph shared state — mirrors JobSearchState as plain dicts."""

    user_profile: dict[str, Any]
    search_query: str
    job_listings: list[dict[str, Any]]
    skill_matches: list[dict[str, Any]]
    salary_analyses: list[dict[str, Any]]
    company_profiles: list[dict[str, Any]]
    cover_letters: list[dict[str, Any]]
    resume_optimizations: list[dict[str, Any]]
    interview_preps: list[dict[str, Any]]
    applications: list[dict[str, Any]]
    agent_messages: Annotated[list[dict[str, Any]], operator.add]
    shortlisted_job_ids: list[str]
    final_report: str
    current_agent: str
    pipeline_status: str


def to_job_search_state(state: GraphState | dict[str, Any]) -> JobSearchState:
    """Convert graph state dict to Pydantic JobSearchState."""
    clean = {k: v for k, v in state.items() if k not in ("current_agent", "pipeline_status")}
    return JobSearchState.model_validate(clean)


def from_job_search_state(js: JobSearchState, **extra: Any) -> GraphState:
    """Convert JobSearchState to graph state dict."""
    data: GraphState = js.model_dump(mode="json")  # type: ignore[assignment]
    data.update(extra)
    return data


def partial_from_agent(
    js: JobSearchState,
    fields: list[str],
    new_messages: list[dict[str, Any]],
    agent_key: str,
    include_status: bool = True,
) -> GraphState:
    """Build a partial state update for LangGraph (supports parallel nodes)."""
    full = js.model_dump(mode="json")
    update: GraphState = {field: full[field] for field in fields}
    update["agent_messages"] = new_messages
    if include_status:
        update["current_agent"] = agent_key
        update["pipeline_status"] = "running"
    return update


def initial_state(
    profile: UserProfile | None = None,
    search_query: str = "",
) -> GraphState:
    js = JobSearchState(
        user_profile=profile or UserProfile(),
        search_query=search_query,
    )
    return from_job_search_state(
        js,
        current_agent="",
        pipeline_status="pending",
    )
