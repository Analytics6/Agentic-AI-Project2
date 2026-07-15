"""Agent 6: Cover Letter Writer — generates tailored cover letters."""

from __future__ import annotations

from agents.base import BaseAgent
from models.schemas import CoverLetter, JobSearchState
from services.job_sources import get_job_by_id


class CoverLetterWriterAgent(BaseAgent):
    name = "CoverLetterWriter"
    role = "Cover Letter Specialist"
    description = "Write personalized cover letters for shortlisted jobs."

    def run(self, state: JobSearchState) -> JobSearchState:
        letters: list[CoverLetter] = []
        shortlisted = state.shortlisted_job_ids or self._auto_shortlist(state)

        for job_id in shortlisted[:3]:
            job = get_job_by_id(job_id, state.job_listings)
            if not job:
                continue
            match = next((m for m in state.skill_matches if m.job_id == job_id), None)
            letter = self._write_letter(state, job, match)
            letters.append(letter)

        state.cover_letters = letters
        self.log(state, f"Generated {len(letters)} cover letters.")
        return state

    def _auto_shortlist(self, state: JobSearchState) -> list[str]:
        return [
            m.job_id
            for m in sorted(state.skill_matches, key=lambda x: x.match_score, reverse=True)[:3]
        ]

    def _write_letter(self, state: JobSearchState, job, match) -> CoverLetter:
        profile = state.user_profile
        matched_skills = match.matched_skills if match else profile.skills[:4]

        system = self.system_prompt() + (
            "\nWrite a professional, concise cover letter (3-4 paragraphs). "
            "Be specific to the role. Do not use placeholder brackets."
        )
        prompt = (
            f"Candidate: {profile.name}\n"
            f"Summary: {profile.summary}\n"
            f"Key skills: {matched_skills}\n"
            f"Job: {job.title} at {job.company}\n"
            f"Description: {job.description}\n"
            f"Requirements: {job.requirements}"
        )

        content = self.llm.chat(system, prompt, temperature=0.5)
        highlights = [
            f"Highlighted skill: {s}" for s in matched_skills[:3]
        ]

        return CoverLetter(job_id=job.id, candidate_id=profile.candidate_id, content=content.strip(), highlights=highlights)
