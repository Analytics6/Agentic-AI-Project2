"""Final report generation — shared by LangGraph and CLI."""

from __future__ import annotations

from models.schemas import JobSearchState
from services.llm_service import LLMService


def generate_final_report(state: JobSearchState, llm: LLMService | None = None) -> str:
    profile = state.user_profile
    lines = [
        "=" * 60,
        "AGENTIC AI JOB SEARCH — FINAL REPORT",
        "=" * 60,
        "",
        f"Candidate: {profile.name or 'N/A'}",
        f"Target roles: {', '.join(profile.target_roles) or 'N/A'}",
        f"Skills: {', '.join(profile.skills[:8])}{'...' if len(profile.skills) > 8 else ''}",
        f"Experience: {profile.experience_years} years",
        "",
        f"Jobs discovered: {len(state.job_listings)}",
        f"Applications tracked: {len(state.applications)}",
        f"Shortlisted: {len(state.shortlisted_job_ids)}",
        "",
        "-" * 60,
        "TOP MATCHES",
        "-" * 60,
    ]

    for app in state.applications[:5]:
        lines.append(
            f"  [{app.match_score:.0f}%] {app.job_title} @ {app.company} - {app.status.value}"
        )
        if app.notes:
            lines.append(f"         > {app.notes}")

    if state.salary_analyses:
        lines.extend(["", "-" * 60, "SALARY INSIGHTS", "-" * 60])
        for sa in state.salary_analyses[:3]:
            job = next((j for j in state.job_listings if j.id == sa.job_id), None)
            title = job.title if job else sa.job_id
            lines.append(f"  {title}: {sa.listed_range} | {sa.verdict}")

    if state.company_profiles:
        lines.extend(["", "-" * 60, "COMPANY RESEARCH", "-" * 60])
        for cp in state.company_profiles[:3]:
            summary = cp.culture_summary[:80]
            lines.append(f"  {cp.company}: {summary}...")

    if state.cover_letters:
        lines.extend(["", "-" * 60, "COVER LETTERS GENERATED", "-" * 60])
        for cl in state.cover_letters:
            job = next((j for j in state.job_listings if j.id == cl.job_id), None)
            title = job.title if job else cl.job_id
            preview = cl.content[:120].replace("\n", " ")
            lines.append(f"  {title}: {preview}...")

    if state.interview_preps:
        lines.extend(["", "-" * 60, "INTERVIEW PREP", "-" * 60])
        for ip in state.interview_preps:
            job = next((j for j in state.job_listings if j.id == ip.job_id), None)
            title = job.title if job else ip.job_id
            lines.append(f"  {title}: {len(ip.likely_questions)} questions prepared")

    lines.extend([
        "",
        "-" * 60,
        "AGENT ACTIVITY LOG",
        "-" * 60,
    ])
    for msg in state.agent_messages[-12:]:
        lines.append(f"  [{msg.agent_name}] {msg.content[:100]}")

    lines.extend(["", "=" * 60, "END OF REPORT", "=" * 60])
    report = "\n".join(lines)

    if llm and llm.is_configured:
        try:
            summary = llm.chat(
                "You are a job search advisor. Summarize in 3 actionable bullet points.",
                f"Summarize this job search report:\n\n{report}",
                temperature=0.3,
            )
            report += f"\n\nEXECUTIVE SUMMARY (AI):\n{summary}"
        except Exception:
            pass

    return report
