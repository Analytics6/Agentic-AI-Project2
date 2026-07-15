"""Agent 9: Application Tracker — manages job application pipeline."""

from __future__ import annotations

from datetime import datetime

from agents.base import BaseAgent
from models.schemas import ApplicationStatus, JobApplication, JobSearchState
from services.job_sources import get_job_by_id


class ApplicationTrackerAgent(BaseAgent):
    name = "ApplicationTracker"
    role = "Application Pipeline Manager"
    description = "Track applications, statuses, and next actions."

    SHORTLIST_THRESHOLD = 55.0

    def run(self, state: JobSearchState) -> JobSearchState:
        applications: list[JobApplication] = []
        shortlisted_ids: list[str] = []

        for match in state.skill_matches:
            job = get_job_by_id(match.job_id, state.job_listings)
            if not job:
                continue

            if match.match_score >= self.SHORTLIST_THRESHOLD:
                status = ApplicationStatus.SHORTLISTED
                shortlisted_ids.append(job.id)
            elif match.match_score >= 50:
                status = ApplicationStatus.MATCHED
            else:
                status = ApplicationStatus.DISCOVERED

            notes = self._build_notes(state, job, match)
            applications.append(
                JobApplication(
                    job_id=job.id,
                    job_title=job.title,
                    company=job.company,
                    status=status,
                    match_score=match.match_score,
                    notes=notes,
                    updated_at=datetime.now(),
                )
            )

        applications.sort(key=lambda a: a.match_score, reverse=True)
        state.applications = applications
        state.shortlisted_job_ids = shortlisted_ids

        self.log(
            state,
            f"Tracking {len(applications)} applications. "
            f"{len(shortlisted_ids)} shortlisted (score >= {self.SHORTLIST_THRESHOLD}).",
            shortlisted=shortlisted_ids,
        )
        return state

    def _build_notes(self, state: JobSearchState, job, match) -> str:
        salary = next((s for s in state.salary_analyses if s.job_id == job.id), None)
        parts = [match.recommendation]
        if salary:
            parts.append(salary.verdict)
        if match.missing_skills:
            parts.append(f"Gap: {', '.join(match.missing_skills[:3])}")
        return " | ".join(parts)
