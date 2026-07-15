"""LangGraph workflow — 10-agent job search pipeline."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from graph.nodes import (
    NODE_REGISTRY,
    application_tracker_node,
    company_researcher_node,
    cover_letter_writer_node,
    interview_prep_node,
    job_searcher_node,
    orchestrator_start_node,
    profile_analyzer_node,
    report_generator_node,
    resume_optimizer_node,
    salary_analyst_node,
    skills_matcher_node,
)
from graph.state import GraphState, from_job_search_state, initial_state, to_job_search_state
from models.schemas import JobSearchState, UserProfile


def build_job_search_graph():
    """
    Build and compile the LangGraph workflow.

    Flow:
        START -> orchestrator -> profile_analyzer -> job_searcher -> skills_matcher
              -> [salary_analyst, company_researcher] (parallel)
              -> application_tracker -> cover_letter_writer -> resume_optimizer
              -> interview_prep -> report_generator -> END
    """
    builder = StateGraph(GraphState)

    # Register all nodes
    builder.add_node("orchestrator", orchestrator_start_node)
    builder.add_node("profile_analyzer", profile_analyzer_node)
    builder.add_node("job_searcher", job_searcher_node)
    builder.add_node("skills_matcher", skills_matcher_node)
    builder.add_node("salary_analyst", salary_analyst_node)
    builder.add_node("company_researcher", company_researcher_node)
    builder.add_node("application_tracker", application_tracker_node)
    builder.add_node("cover_letter_writer", cover_letter_writer_node)
    builder.add_node("resume_optimizer", resume_optimizer_node)
    builder.add_node("interview_prep", interview_prep_node)
    builder.add_node("report_generator", report_generator_node)

    # Sequential edges
    builder.add_edge(START, "orchestrator")
    builder.add_edge("orchestrator", "profile_analyzer")
    builder.add_edge("profile_analyzer", "job_searcher")
    builder.add_edge("job_searcher", "skills_matcher")

    # Parallel fan-out after skills matching
    builder.add_edge("skills_matcher", "salary_analyst")
    builder.add_edge("skills_matcher", "company_researcher")

    # Fan-in: both must complete before application tracker
    builder.add_edge(["salary_analyst", "company_researcher"], "application_tracker")

    # Sequential application phase
    builder.add_edge("application_tracker", "cover_letter_writer")
    builder.add_edge("cover_letter_writer", "resume_optimizer")
    builder.add_edge("resume_optimizer", "interview_prep")
    builder.add_edge("interview_prep", "report_generator")
    builder.add_edge("report_generator", END)

    return builder.compile()


# Singleton compiled graph
_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_job_search_graph()
    return _compiled_graph


def run_pipeline(
    profile: UserProfile | None = None,
    search_query: str = "",
) -> JobSearchState:
    """Run the full LangGraph pipeline and return final JobSearchState."""
    graph = get_graph()
    init = initial_state(profile=profile, search_query=search_query)
    final = graph.invoke(init)
    return to_job_search_state(final)


def stream_pipeline(
    profile: UserProfile | None = None,
    search_query: str = "",
):
    """Stream LangGraph node updates for live UI."""
    graph = get_graph()
    init = initial_state(profile=profile, search_query=search_query)
    yield from graph.stream(init, stream_mode="updates")


def stream_pipeline_to_state(
    profile: UserProfile | None = None,
    search_query: str = "",
) -> JobSearchState:
    """Stream pipeline and return final merged state (single graph pass)."""
    graph = get_graph()
    init = initial_state(profile=profile, search_query=search_query)
    final: GraphState | None = None
    for chunk in graph.stream(init, stream_mode="values"):
        final = chunk
    if final is None:
        final = graph.invoke(init)
    return to_job_search_state(final)


def get_mermaid_diagram() -> str:
    """Return Mermaid diagram of the agent graph."""
    return """graph TD
    START([START]) --> orchestrator[Orchestrator]
    orchestrator --> profile_analyzer[Profile Analyzer]
    profile_analyzer --> job_searcher[Job Searcher]
    job_searcher --> skills_matcher[Skills Matcher]
    skills_matcher --> salary_analyst[Salary Analyst]
    skills_matcher --> company_researcher[Company Researcher]
    salary_analyst --> application_tracker[Application Tracker]
    company_researcher --> application_tracker
    application_tracker --> cover_letter_writer[Cover Letter Writer]
    cover_letter_writer --> resume_optimizer[Resume Optimizer]
    resume_optimizer --> interview_prep[Interview Prep]
    interview_prep --> report_generator[Report Generator]
    report_generator --> END_NODE([END])

    style orchestrator fill:#6366f1,color:#fff
    style profile_analyzer fill:#8b5cf6,color:#fff
    style job_searcher fill:#a855f7,color:#fff
    style skills_matcher fill:#d946ef,color:#fff
    style salary_analyst fill:#ec4899,color:#fff
    style company_researcher fill:#f43f5e,color:#fff
    style application_tracker fill:#f97316,color:#fff
    style cover_letter_writer fill:#eab308,color:#000
    style resume_optimizer fill:#22c55e,color:#fff
    style interview_prep fill:#14b8a6,color:#fff
    style report_generator fill:#3b82f6,color:#fff
"""


def list_agents() -> list[dict]:
    """Return agent metadata for UI."""
    order = [
        "orchestrator", "profile_analyzer", "job_searcher", "skills_matcher",
        "salary_analyst", "company_researcher", "application_tracker",
        "cover_letter_writer", "resume_optimizer", "interview_prep", "report_generator",
    ]
    return [
        {"id": aid, "index": i + 1, **NODE_REGISTRY[aid]}
        for i, aid in enumerate(order)
    ]
