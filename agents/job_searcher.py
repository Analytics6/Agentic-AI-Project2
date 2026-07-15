"""Agent 2: Job Searcher — discovers relevant job listings."""

from __future__ import annotations

from agents.base import BaseAgent
from models.schemas import JobSearchState
from services.job_sources import search_jobs


class JobSearcherAgent(BaseAgent):
    name = "JobSearcher"
    role = "Job Discovery Specialist"
    description = "Find and rank job listings matching the candidate profile."

    def run(self, state: JobSearchState) -> JobSearchState:
        query = state.search_query
        if not query:
            roles = state.user_profile.target_roles
            skills = state.user_profile.skills[:5]
            query = " ".join(roles + skills)

        listings = search_jobs(state.user_profile, query=query, limit=15)

        if self.llm.is_configured and listings:
            listings = self._rerank_with_llm(state, listings)

        state.job_listings = listings
        self.log(
            state,
            f"Discovered {len(listings)} job listings for query: '{query}'.",
            job_ids=[j.id for j in listings],
        )
        return state

    def _rerank_with_llm(self, state: JobSearchState, listings: list) -> list:
        profile_json = state.user_profile.model_dump_json()
        jobs_summary = [
            {"id": j.id, "title": j.title, "company": j.company, "requirements": j.requirements}
            for j in listings
        ]
        system = self.system_prompt() + (
            "\nGiven a candidate profile and job list, return JSON: "
            '{"ranked_ids": ["id1", "id2", ...]} ordered best to worst fit.'
        )
        try:
            raw = self.llm.chat(
                system,
                f"Profile:\n{profile_json}\n\nJobs:\n{jobs_summary}",
            )
            data = self.llm._extract_json(raw)
            ranked_ids = data.get("ranked_ids", [])
            id_map = {j.id: j for j in listings}
            reranked = [id_map[jid] for jid in ranked_ids if jid in id_map]
            seen = {j.id for j in reranked}
            reranked.extend(j for j in listings if j.id not in seen)
            return reranked
        except Exception:
            return listings
