"""Agent 5: Company Researcher — gathers company intelligence."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agents.base import BaseAgent
from models.schemas import CompanyProfile, JobSearchState
from services.job_sources import get_job_by_id


class _CompanyPayload(BaseModel):
    industry: str = ""
    size: str = ""
    culture_summary: str = ""
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    interview_process: str = ""
    glassdoor_rating: str = ""


class CompanyResearcherAgent(BaseAgent):
    name = "CompanyResearcher"
    role = "Company Intelligence Analyst"
    description = "Research company culture, interview process, and employer reputation."

    def run(self, state: JobSearchState) -> JobSearchState:
        profiles: list[CompanyProfile] = []
        seen_companies: set[str] = set()
        top_matches = sorted(state.skill_matches, key=lambda m: m.match_score, reverse=True)[:5]

        for match in top_matches:
            job = get_job_by_id(match.job_id, state.job_listings)
            if not job or job.company in seen_companies:
                continue
            seen_companies.add(job.company)
            profiles.append(self._research_company(job))

        state.company_profiles = profiles
        self.log(state, f"Researched {len(profiles)} companies.")
        return state

    def _research_company(self, job) -> CompanyProfile:
        if self.llm.is_configured:
            try:
                payload = self.llm.chat_json(
                    self.system_prompt() + (
                        "\nProvide realistic employer research based on public knowledge "
                        "patterns for tech companies. Mark uncertain details clearly."
                    ),
                    f"Research company: {job.company}\nRole context: {job.title}",
                    _CompanyPayload,
                )
                return CompanyProfile(
                    company=job.company,
                    industry=payload.industry,
                    size=payload.size,
                    culture_summary=payload.culture_summary,
                    pros=payload.pros,
                    cons=payload.cons,
                    interview_process=payload.interview_process,
                    glassdoor_rating=payload.glassdoor_rating,
                )
            except Exception:
                pass

        return CompanyProfile(
            company=job.company,
            industry="Technology / AI",
            size="Mid-size (estimated)",
            culture_summary=f"{job.company} appears to be a technology company hiring for {job.title}.",
            pros=["Active hiring in AI/tech", "Remote/hybrid options may be available"],
            cons=["Verify benefits and work-life balance via employee reviews"],
            interview_process="Typical: recruiter screen → technical → team fit",
            glassdoor_rating="Check Glassdoor for latest ratings",
        )
