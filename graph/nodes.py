"""LangGraph node functions — each wraps one specialist agent."""

from __future__ import annotations

from typing import Any, Callable

from agents.application_tracker import ApplicationTrackerAgent
from agents.company_researcher import CompanyResearcherAgent
from agents.cover_letter_writer import CoverLetterWriterAgent
from agents.interview_prep import InterviewPrepAgent
from agents.job_searcher import JobSearcherAgent
from agents.profile_analyzer import ProfileAnalyzerAgent
from agents.resume_optimizer import ResumeOptimizerAgent
from agents.salary_analyst import SalaryAnalystAgent
from agents.skills_matcher import SkillsMatcherAgent
from graph.report import generate_final_report
from graph.state import GraphState, partial_from_agent, to_job_search_state
from models.schemas import AgentMessage
from services.llm_service import get_llm


def _serialize_messages(messages: list) -> list[dict[str, Any]]:
    return [
        m.model_dump(mode="json") if hasattr(m, "model_dump") else m
        for m in messages
    ]


def _make_node(
    agent_cls: type,
    agent_key: str,
    output_fields: list[str],
    parallel: bool = False,
) -> Callable[[GraphState], GraphState]:
    """Factory: create a LangGraph node that returns partial state updates."""

    def node(state: GraphState) -> GraphState:
        llm = get_llm()
        agent = agent_cls(llm)
        js = to_job_search_state(state)
        before = len(js.agent_messages)
        js = agent.run(js)
        new_msgs = _serialize_messages(js.agent_messages[before:])
        return partial_from_agent(
            js,
            fields=output_fields,
            new_messages=new_msgs,
            agent_key=agent_key,
            include_status=not parallel,
        )

    node.__name__ = agent_key
    return node


profile_analyzer_node = _make_node(
    ProfileAnalyzerAgent, "profile_analyzer", ["user_profile"]
)
job_searcher_node = _make_node(
    JobSearcherAgent, "job_searcher", ["job_listings", "search_query"]
)
skills_matcher_node = _make_node(
    SkillsMatcherAgent, "skills_matcher", ["skill_matches"]
)
salary_analyst_node = _make_node(
    SalaryAnalystAgent, "salary_analyst", ["salary_analyses"], parallel=True
)
company_researcher_node = _make_node(
    CompanyResearcherAgent, "company_researcher", ["company_profiles"], parallel=True
)
application_tracker_node = _make_node(
    ApplicationTrackerAgent, "application_tracker", ["applications", "shortlisted_job_ids"]
)
cover_letter_writer_node = _make_node(
    CoverLetterWriterAgent, "cover_letter_writer", ["cover_letters"]
)
resume_optimizer_node = _make_node(
    ResumeOptimizerAgent, "resume_optimizer", ["resume_optimizations"]
)
interview_prep_node = _make_node(
    InterviewPrepAgent, "interview_prep", ["interview_preps"]
)


def report_generator_node(state: GraphState) -> GraphState:
    """Final node: synthesize the actionable report."""
    js = to_job_search_state(state)
    llm = get_llm()
    js.final_report = generate_final_report(js, llm)
    msg = AgentMessage(
        agent_name="ReportGenerator",
        role="Report Synthesizer",
        content="Final report generated.",
    )
    update = partial_from_agent(
        js,
        fields=["final_report"],
        new_messages=[msg.model_dump(mode="json")],
        agent_key="report_generator",
    )
    update["pipeline_status"] = "complete"
    return update


def orchestrator_start_node(state: GraphState) -> GraphState:
    """Entry node: log pipeline start."""
    js = to_job_search_state(state)
    msg = AgentMessage(
        agent_name="Orchestrator",
        role="LangGraph Coordinator",
        content="LangGraph pipeline started — 10 agents queued.",
    )
    return {
        "agent_messages": [msg.model_dump(mode="json")],
        "current_agent": "orchestrator",
        "pipeline_status": "running",
    }


NODE_REGISTRY: dict[str, dict[str, str]] = {
    "orchestrator": {
        "name": "Orchestrator",
        "role": "LangGraph Coordinator",
        "description": "Entry point that initializes the multi-agent pipeline.",
    },
    "profile_analyzer": {
        "name": "ProfileAnalyzer",
        "role": "Resume & Profile Analyst",
        "description": "Parse resume and build structured candidate profile.",
    },
    "job_searcher": {
        "name": "JobSearcher",
        "role": "Job Discovery Specialist",
        "description": "Discover and rank relevant job listings.",
    },
    "skills_matcher": {
        "name": "SkillsMatcher",
        "role": "Skills Alignment Analyst",
        "description": "Score skill alignment between candidate and jobs.",
    },
    "salary_analyst": {
        "name": "SalaryAnalyst",
        "role": "Compensation Analyst",
        "description": "Analyze salary ranges and negotiation strategy.",
    },
    "company_researcher": {
        "name": "CompanyResearcher",
        "role": "Company Intelligence Analyst",
        "description": "Research company culture and interview process.",
    },
    "application_tracker": {
        "name": "ApplicationTracker",
        "role": "Application Pipeline Manager",
        "description": "Track applications, statuses, and shortlisting.",
    },
    "cover_letter_writer": {
        "name": "CoverLetterWriter",
        "role": "Cover Letter Specialist",
        "description": "Generate tailored cover letters for top jobs.",
    },
    "resume_optimizer": {
        "name": "ResumeOptimizer",
        "role": "Resume & ATS Optimization Specialist",
        "description": "Optimize resume keywords and bullets for ATS.",
    },
    "interview_prep": {
        "name": "InterviewPrep",
        "role": "Interview Coach",
        "description": "Prepare role-specific interview Q&A.",
    },
    "report_generator": {
        "name": "ReportGenerator",
        "role": "Report Synthesizer",
        "description": "Produce the final actionable job search report.",
    },
}
