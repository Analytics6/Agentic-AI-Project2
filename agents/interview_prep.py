"""Agent 8: Interview Prep — prepares interview questions and answers."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agents.base import BaseAgent
from models.schemas import InterviewPrep, JobSearchState
from services.job_sources import get_job_by_id


class _InterviewPayload(BaseModel):
    likely_questions: list[str] = Field(default_factory=list)
    suggested_answers: list[dict[str, str]] = Field(default_factory=list)
    questions_to_ask: list[str] = Field(default_factory=list)
    preparation_tips: list[str] = Field(default_factory=list)


class InterviewPrepAgent(BaseAgent):
    name = "InterviewPrep"
    role = "Interview Coach"
    description = "Generate role-specific interview questions, answers, and prep tips."

    def run(self, state: JobSearchState) -> JobSearchState:
        preps: list[InterviewPrep] = []
        shortlisted = state.shortlisted_job_ids or [
            m.job_id
            for m in sorted(state.skill_matches, key=lambda x: x.match_score, reverse=True)[:2]
        ]

        for job_id in shortlisted[:2]:
            job = get_job_by_id(job_id, state.job_listings)
            if not job:
                continue
            prep = self._prepare(state, job)
            preps.append(prep)

        state.interview_preps = preps
        self.log(state, f"Prepared interview guides for {len(preps)} jobs.")
        return state

    def _prepare(self, state: JobSearchState, job) -> InterviewPrep:
        profile = state.user_profile
        company = next(
            (c for c in state.company_profiles if c.company == job.company), None
        )

        if self.llm.is_configured:
            try:
                payload = self.llm.chat_json(
                    self.system_prompt(),
                    (
                        f"Candidate: {profile.name}, {profile.experience_years} yrs exp\n"
                        f"Skills: {profile.skills}\n"
                        f"Job: {job.title} at {job.company}\n"
                        f"Requirements: {job.requirements}\n"
                        f"Company info: {company.model_dump() if company else 'N/A'}"
                    ),
                    _InterviewPayload,
                )
                return InterviewPrep(
                    job_id=job.id,
                    likely_questions=payload.likely_questions,
                    suggested_answers=payload.suggested_answers,
                    questions_to_ask=payload.questions_to_ask,
                    preparation_tips=payload.preparation_tips,
                )
            except Exception:
                pass

        return InterviewPrep(
            job_id=job.id,
            likely_questions=[
                f"Why do you want to work at {job.company}?",
                f"Describe your experience with {job.requirements[0] if job.requirements else 'this stack'}.",
                "Tell me about a challenging project and how you solved it.",
                "How do you stay current with AI/ML trends?",
            ],
            suggested_answers=[
                {
                    "question": f"Why {job.company}?",
                    "answer": (
                        f"Research {job.company}'s products and connect your "
                        f"{profile.skills[0] if profile.skills else 'technical'} experience to their mission."
                    ),
                }
            ],
            questions_to_ask=[
                "What does success look like in the first 90 days?",
                "How is the team structured for this role?",
                "What are the biggest technical challenges right now?",
            ],
            preparation_tips=[
                "Review the job description and map each requirement to a story.",
                "Prepare 2-3 STAR-format behavioral examples.",
                "Practice explaining your ML/AI projects with metrics.",
            ],
        )
