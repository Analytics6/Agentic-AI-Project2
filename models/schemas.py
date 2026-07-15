"""Shared data models for the job search multi-agent system."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ApplicationStatus(str, Enum):
    DISCOVERED = "discovered"
    MATCHED = "matched"
    SHORTLISTED = "shortlisted"
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"


class UserProfile(BaseModel):
    candidate_id: str = ""
    resume_file: str = ""
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience_years: float = 0.0
    education: list[str] = Field(default_factory=list)
    work_history: list[dict[str, Any]] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    target_locations: list[str] = Field(default_factory=list)
    salary_expectation: str = ""
    raw_resume: str = ""


class JobListing(BaseModel):
    id: str
    title: str
    company: str
    location: str
    description: str
    requirements: list[str] = Field(default_factory=list)
    salary_range: str = ""
    url: str = ""
    source: str = "mock"
    posted_date: str = ""


class SkillMatchResult(BaseModel):
    job_id: str
    match_score: float = Field(ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    gap_analysis: str = ""
    recommendation: str = ""


class SalaryAnalysis(BaseModel):
    job_id: str
    listed_range: str = ""
    market_estimate: str = ""
    competitiveness: str = ""
    negotiation_tips: list[str] = Field(default_factory=list)
    verdict: str = ""


class CompanyProfile(BaseModel):
    company: str
    industry: str = ""
    size: str = ""
    culture_summary: str = ""
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    interview_process: str = ""
    glassdoor_rating: str = ""


class CoverLetter(BaseModel):
    job_id: str
    candidate_id: str = ""
    content: str
    highlights: list[str] = Field(default_factory=list)


class ResumeOptimization(BaseModel):
    job_id: str
    candidate_id: str = ""
    optimized_summary: str = ""
    optimized_resume_text: str = ""
    keyword_additions: list[str] = Field(default_factory=list)
    bullet_rewrites: list[dict[str, str]] = Field(default_factory=list)
    ats_score: float = Field(default=0, ge=0, le=100)


class InterviewPrep(BaseModel):
    job_id: str
    likely_questions: list[str] = Field(default_factory=list)
    suggested_answers: list[dict[str, str]] = Field(default_factory=list)
    questions_to_ask: list[str] = Field(default_factory=list)
    preparation_tips: list[str] = Field(default_factory=list)


class JobApplication(BaseModel):
    job_id: str
    job_title: str
    company: str
    status: ApplicationStatus = ApplicationStatus.DISCOVERED
    match_score: float = 0.0
    notes: str = ""
    updated_at: datetime = Field(default_factory=datetime.now)


class AgentMessage(BaseModel):
    agent_name: str
    role: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class JobSearchState(BaseModel):
    """Shared state passed through the multi-agent pipeline."""

    user_profile: UserProfile
    search_query: str = ""
    job_listings: list[JobListing] = Field(default_factory=list)
    skill_matches: list[SkillMatchResult] = Field(default_factory=list)
    salary_analyses: list[SalaryAnalysis] = Field(default_factory=list)
    company_profiles: list[CompanyProfile] = Field(default_factory=list)
    cover_letters: list[CoverLetter] = Field(default_factory=list)
    resume_optimizations: list[ResumeOptimization] = Field(default_factory=list)
    interview_preps: list[InterviewPrep] = Field(default_factory=list)
    applications: list[JobApplication] = Field(default_factory=list)
    agent_messages: list[AgentMessage] = Field(default_factory=list)
    shortlisted_job_ids: list[str] = Field(default_factory=list)
    final_report: str = ""


class BatchRunResult(BaseModel):
    """Results from running the pipeline across multiple resumes."""

    run_id: str = ""
    search_query: str = ""
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None
    candidate_results: list[JobSearchState] = Field(default_factory=list)
    comparison_report: str = ""
    total_candidates: int = 0
    total_jobs_matched: int = 0
    top_matches_overall: list[dict[str, Any]] = Field(default_factory=list)
