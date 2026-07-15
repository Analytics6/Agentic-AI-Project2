"""Agent 1: Profile Analyzer — extracts and structures user profile from resume."""

from __future__ import annotations

from agents.base import BaseAgent
from models.schemas import JobSearchState
from services.resume_parser import parse_resume_text


class ProfileAnalyzerAgent(BaseAgent):
    name = "ProfileAnalyzer"
    role = "Resume & Profile Analyst"
    description = "Parse resumes and build structured candidate profiles."

    def run(self, state: JobSearchState) -> JobSearchState:
        profile = state.user_profile
        raw = profile.raw_resume or ""
        if not raw.strip():
            from services.resume_loader import load_all_resumes
            resumes = load_all_resumes()
            raw = resumes[0].raw_resume if resumes else ""

        cid = profile.candidate_id or profile.resume_file or "candidate"
        resume_file = profile.resume_file or "inline.txt"

        system = self.system_prompt() + (
            "\nExtract a structured profile from the resume text. "
            "Return JSON with: name, email, phone, location, skills (list), "
            "experience_years (number), summary, target_roles (list), "
            "education (list), work_history (list of objects with title, company, dates, bullets), "
            "salary_expectation, target_locations (list)."
        )

        if self.llm.is_configured:
            try:
                raw_response = self.llm.chat(system, f"Resume:\n\n{raw}")
                data = self.llm._extract_json(raw_response)
                parsed = parse_resume_text(raw, resume_file=resume_file, candidate_id=cid)
                state.user_profile = parsed.model_copy(update={
                    "name": data.get("name") or parsed.name,
                    "email": data.get("email") or parsed.email,
                    "phone": data.get("phone") or parsed.phone,
                    "location": data.get("location") or parsed.location,
                    "skills": data.get("skills") or parsed.skills,
                    "experience_years": float(data.get("experience_years", parsed.experience_years)),
                    "summary": data.get("summary") or parsed.summary,
                    "target_roles": data.get("target_roles") or parsed.target_roles,
                    "education": data.get("education") or parsed.education,
                    "work_history": data.get("work_history") or parsed.work_history,
                    "salary_expectation": data.get("salary_expectation") or parsed.salary_expectation,
                    "target_locations": data.get("target_locations") or parsed.target_locations,
                    "raw_resume": raw,
                })
            except Exception as exc:
                state.user_profile = parse_resume_text(raw, resume_file=resume_file, candidate_id=cid)
                self.log(state, f"Profile parsed with rule-based parser (LLM fallback): {exc}")
        else:
            state.user_profile = parse_resume_text(raw, resume_file=resume_file, candidate_id=cid)

        self.log(
            state,
            f"Analyzed profile for {state.user_profile.name or 'candidate'}: "
            f"{len(state.user_profile.skills)} skills, "
            f"{state.user_profile.experience_years} years experience, "
            f"roles: {', '.join(state.user_profile.target_roles[:3])}.",
            candidate_id=state.user_profile.candidate_id,
        )
        return state
