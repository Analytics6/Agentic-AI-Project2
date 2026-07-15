"""Agent 4: Salary Analyst — evaluates compensation competitiveness."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agents.base import BaseAgent
from models.schemas import JobSearchState, SalaryAnalysis
from services.job_sources import get_job_by_id


class _SalaryPayload(BaseModel):
    market_estimate: str = ""
    competitiveness: str = ""
    negotiation_tips: list[str] = Field(default_factory=list)
    verdict: str = ""


class SalaryAnalystAgent(BaseAgent):
    name = "SalaryAnalyst"
    role = "Compensation Analyst"
    description = "Analyze salary ranges and provide negotiation guidance."

    def run(self, state: JobSearchState) -> JobSearchState:
        analyses: list[SalaryAnalysis] = []
        top_matches = sorted(state.skill_matches, key=lambda m: m.match_score, reverse=True)[:5]

        for match in top_matches:
            job = get_job_by_id(match.job_id, state.job_listings)
            if not job:
                continue
            analysis = self._analyze_job(state, job)
            analyses.append(analysis)

        state.salary_analyses = analyses
        self.log(state, f"Completed salary analysis for {len(analyses)} top jobs.")
        return state

    def _analyze_job(self, state: JobSearchState, job) -> SalaryAnalysis:
        expectation = state.user_profile.salary_expectation or "Not specified"

        if self.llm.is_configured:
            try:
                payload = self.llm.chat_json(
                    self.system_prompt(),
                    (
                        f"Job: {job.title} at {job.company}\n"
                        f"Location: {job.location}\n"
                        f"Listed salary: {job.salary_range}\n"
                        f"Candidate expectation: {expectation}\n"
                        f"Experience: {state.user_profile.experience_years} years"
                    ),
                    _SalaryPayload,
                )
                return SalaryAnalysis(
                    job_id=job.id,
                    listed_range=job.salary_range,
                    market_estimate=payload.market_estimate,
                    competitiveness=payload.competitiveness,
                    negotiation_tips=payload.negotiation_tips,
                    verdict=payload.verdict,
                )
            except Exception:
                pass

        return SalaryAnalysis(
            job_id=job.id,
            listed_range=job.salary_range,
            market_estimate=job.salary_range or "Market data unavailable",
            competitiveness="Review against Levels.fyi and Glassdoor for your level.",
            negotiation_tips=[
                "Anchor on total compensation, not base alone.",
                "Prepare 2-3 quantified impact stories.",
                "Ask about equity, bonus, and remote stipends.",
            ],
            verdict=f"Listed range {job.salary_range} — compare to your expectation: {expectation}.",
        )
