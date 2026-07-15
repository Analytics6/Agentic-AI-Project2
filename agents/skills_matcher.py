"""Agent 3: Skills Matcher — scores job-candidate skill alignment."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from agents.base import BaseAgent
from models.schemas import JobSearchState, SkillMatchResult

REQUIREMENT_ALIASES: dict[str, list[str]] = {
    "python": ["python"],
    "machine learning": ["machine learning", "ml", "deep learning"],
    "pytorch": ["pytorch", "tensorflow"],
    "tensorflow": ["pytorch", "tensorflow"],
    "fastapi": ["fastapi", "flask", "rest apis"],
    "sql": ["sql", "postgresql", "mysql"],
    "docker": ["docker", "kubernetes"],
    "kubernetes": ["kubernetes", "docker", "k8s"],
    "aws": ["aws", "cloud", "gcp", "azure"],
    "mlops": ["mlops", "ci/cd", "docker"],
    "langchain": ["langchain", "langgraph", "agent frameworks"],
    "langgraph": ["langgraph", "langchain", "agent frameworks"],
    "openai": ["openai", "anthropic", "llm"],
    "rag": ["rag", "vector databases", "prompt engineering"],
    "nlp": ["nlp", "transformers", "natural language"],
    "transformers": ["transformers", "pytorch", "hugging face", "nlp"],
    "statistics": ["statistics", "scikit-learn", "a/b testing"],
    "scikit-learn": ["scikit-learn", "machine learning", "statistics"],
    "microservices": ["microservices", "rest apis", "distributed systems"],
    "terraform": ["terraform", "infrastructure", "aws"],
    "ci/cd": ["ci/cd", "mlops", "devops"],
    "publications": ["publications", "research", "phd"],
    "phd": ["phd", "publications", "research"],
}


class _MatchPayload(BaseModel):
    match_score: float = Field(ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    gap_analysis: str = ""
    recommendation: str = ""


class SkillsMatcherAgent(BaseAgent):
    name = "SkillsMatcher"
    role = "Skills Alignment Analyst"
    description = "Match candidate skills against job requirements and score fit."

    MATCH_THRESHOLD = 60.0

    def run(self, state: JobSearchState) -> JobSearchState:
        matches: list[SkillMatchResult] = []
        profile = state.user_profile
        user_skills = {s.lower() for s in profile.skills}
        user_text = " ".join(profile.skills + [profile.summary] + profile.target_roles).lower()

        for job in state.job_listings:
            result = self._match_job(profile, job, user_skills, user_text)
            matches.append(result)

        matches.sort(key=lambda m: m.match_score, reverse=True)
        state.skill_matches = matches

        top = matches[0] if matches else None
        self.log(
            state,
            f"Matched {len(matches)} jobs. Top match: {top.match_score if top else 0:.1f}%.",
            top_job_id=top.job_id if top else None,
        )
        return state

    def _requirement_matches(
        self, req: str, user_skills: set[str], user_text: str, experience_years: float
    ) -> bool:
        req_lower = req.lower()

        years_match = re.search(r"(\d+)\+?\s*years?", req_lower)
        if years_match and ("experience" in req_lower or "year" in req_lower):
            required = float(years_match.group(1))
            if experience_years >= required:
                return True

        if req_lower in user_skills:
            return True

        for skill in user_skills:
            if skill in req_lower or req_lower in skill:
                return True

        for alias_key, aliases in REQUIREMENT_ALIASES.items():
            if alias_key in req_lower:
                if any(a in user_skills or a in user_text for a in aliases):
                    return True

        req_tokens = set(re.findall(r"[a-z0-9/+]+", req_lower))
        req_tokens -= {"or", "and", "years", "experience", "preferred", "required"}
        for token in req_tokens:
            if len(token) > 2 and (token in user_text or any(token in s for s in user_skills)):
                return True

        return False

    def _match_job(self, profile, job, user_skills: set[str], user_text: str) -> SkillMatchResult:
        req_skills = [r.strip() for r in job.requirements if r.strip()]

        matched = [
            r for r in req_skills
            if self._requirement_matches(r, user_skills, user_text, profile.experience_years)
        ]
        missing = [r for r in req_skills if r not in matched]

        title_bonus = 0.0
        for role in profile.target_roles:
            if role.lower() in job.title.lower() or job.title.lower() in role.lower():
                title_bonus = 10.0
                break

        if req_skills:
            heuristic_score = (len(matched) / len(req_skills)) * 90 + title_bonus
        else:
            heuristic_score = 50.0 + title_bonus

        heuristic_score = min(heuristic_score, 100.0)

        if self.llm.is_configured:
            try:
                payload = self.llm.chat_json(
                    self.system_prompt(),
                    (
                        f"Candidate: {profile.name}\n"
                        f"Skills: {profile.skills}\n"
                        f"Experience: {profile.experience_years} years\n"
                        f"Target roles: {profile.target_roles}\n"
                        f"Job: {job.title} at {job.company}\n"
                        f"Requirements: {job.requirements}\n"
                        f"Heuristic score: {heuristic_score:.1f}"
                    ),
                    _MatchPayload,
                )
                return SkillMatchResult(
                    job_id=job.id,
                    match_score=payload.match_score,
                    matched_skills=payload.matched_skills or matched,
                    missing_skills=payload.missing_skills or missing,
                    gap_analysis=payload.gap_analysis,
                    recommendation=payload.recommendation,
                )
            except Exception:
                pass

        return SkillMatchResult(
            job_id=job.id,
            match_score=round(heuristic_score, 1),
            matched_skills=matched,
            missing_skills=missing,
            gap_analysis=f"Matched {len(matched)}/{len(req_skills)} requirements.",
            recommendation=(
                "Strong match — prioritize application."
                if heuristic_score >= self.MATCH_THRESHOLD
                else "Good potential — tailor resume and apply."
                if heuristic_score >= 45
                else "Stretch role — upskill on gaps first."
            ),
        )
