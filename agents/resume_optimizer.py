"""Agent 8: Resume Optimizer — tailors resume for target jobs."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agents.base import BaseAgent
from models.schemas import JobSearchState, ResumeOptimization
from services.job_sources import get_job_by_id


class _ResumePayload(BaseModel):
    optimized_summary: str = ""
    optimized_resume_text: str = ""
    keyword_additions: list[str] = Field(default_factory=list)
    bullet_rewrites: list[dict[str, str]] = Field(default_factory=list)
    ats_score: float = Field(default=0, ge=0, le=100)


class ResumeOptimizerAgent(BaseAgent):
    name = "ResumeOptimizer"
    role = "Resume & ATS Optimization Specialist"
    description = "Optimize resume content for ATS and specific job descriptions."

    def run(self, state: JobSearchState) -> JobSearchState:
        optimizations: list[ResumeOptimization] = []
        shortlisted = state.shortlisted_job_ids or [
            m.job_id
            for m in sorted(state.skill_matches, key=lambda x: x.match_score, reverse=True)[:3]
        ]
        cid = state.user_profile.candidate_id

        for job_id in shortlisted[:3]:
            job = get_job_by_id(job_id, state.job_listings)
            if not job:
                continue
            opt = self._optimize(state, job, cid)
            optimizations.append(opt)

        state.resume_optimizations = optimizations
        self.log(state, f"Created {len(optimizations)} tailored resume variants.")
        return state

    def _build_resume_text(self, profile, job, summary: str, keywords: list[str]) -> str:
        lines = [
            profile.name,
            " | ".join(filter(None, [profile.email, profile.phone, profile.location])),
            "",
            "PROFESSIONAL SUMMARY",
            summary,
            "",
            "TECHNICAL SKILLS",
            ", ".join(list(dict.fromkeys(profile.skills + keywords))[:18]),
            "",
            "PROFESSIONAL EXPERIENCE",
        ]
        for wh in profile.work_history:
            title = wh.get("title", "")
            company = wh.get("company", "")
            dates = wh.get("dates", "")
            lines.append(f"{title} | {company} | {dates}")
            for bullet in wh.get("bullets", []):
                lines.append(f"- {bullet}")
            lines.append("")

        if not profile.work_history and profile.raw_resume:
            exp_section = profile.raw_resume.upper().split("PROFESSIONAL EXPERIENCE")
            if len(exp_section) > 1:
                rest = exp_section[1].split("EDUCATION")[0].strip()
                lines.append(rest[:800])

        lines.extend(["EDUCATION", *profile.education, "", f"TARGET ROLE: {job.title} at {job.company}"])
        return "\n".join(lines)

    def _optimize(self, state: JobSearchState, job, candidate_id: str) -> ResumeOptimization:
        profile = state.user_profile

        if self.llm.is_configured:
            try:
                payload = self.llm.chat_json(
                    self.system_prompt() + (
                        "\nAlso return optimized_resume_text: a complete tailored resume "
                        "as plain text ready to submit."
                    ),
                    (
                        f"Resume:\n{profile.raw_resume[:2000]}\n\n"
                        f"Target job: {job.title} at {job.company}\n"
                        f"Requirements: {job.requirements}\n"
                        f"Description: {job.description}"
                    ),
                    _ResumePayload,
                )
                resume_text = payload.optimized_resume_text or self._build_resume_text(
                    profile, job, payload.optimized_summary, payload.keyword_additions
                )
                return ResumeOptimization(
                    job_id=job.id,
                    candidate_id=candidate_id,
                    optimized_summary=payload.optimized_summary,
                    optimized_resume_text=resume_text,
                    keyword_additions=payload.keyword_additions,
                    bullet_rewrites=payload.bullet_rewrites,
                    ats_score=payload.ats_score,
                )
            except Exception:
                pass

        missing = [r for r in job.requirements if r.lower() not in {s.lower() for s in profile.skills}]
        keywords = missing[:5] if missing else job.requirements[:5]
        summary = (
            f"{profile.summary} Targeting {job.title} at {job.company} "
            f"with expertise in {', '.join(profile.skills[:5])}."
        )
        match = next((m for m in state.skill_matches if m.job_id == job.id), None)
        ats = match.match_score if match else 75.0

        return ResumeOptimization(
            job_id=job.id,
            candidate_id=candidate_id,
            optimized_summary=summary,
            optimized_resume_text=self._build_resume_text(profile, job, summary, keywords),
            keyword_additions=keywords,
            bullet_rewrites=[
                {
                    "original": "General experience bullet",
                    "rewritten": f"Delivered results aligned with {job.title} requirements at scale",
                }
            ],
            ats_score=round(ats, 1),
        )
