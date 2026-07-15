"""Job search agents package — 10 specialized agents."""

from agents.application_tracker import ApplicationTrackerAgent
from agents.base import BaseAgent
from agents.company_researcher import CompanyResearcherAgent
from agents.cover_letter_writer import CoverLetterWriterAgent
from agents.interview_prep import InterviewPrepAgent
from agents.job_searcher import JobSearcherAgent
from agents.profile_analyzer import ProfileAnalyzerAgent
from agents.resume_optimizer import ResumeOptimizerAgent
from agents.salary_analyst import SalaryAnalystAgent
from agents.skills_matcher import SkillsMatcherAgent

ALL_AGENTS = [
    ProfileAnalyzerAgent,
    JobSearcherAgent,
    SkillsMatcherAgent,
    SalaryAnalystAgent,
    CompanyResearcherAgent,
    ApplicationTrackerAgent,
    CoverLetterWriterAgent,
    ResumeOptimizerAgent,
    InterviewPrepAgent,
]

__all__ = [
    "BaseAgent",
    "ProfileAnalyzerAgent",
    "JobSearcherAgent",
    "SkillsMatcherAgent",
    "SalaryAnalystAgent",
    "CompanyResearcherAgent",
    "ApplicationTrackerAgent",
    "CoverLetterWriterAgent",
    "ResumeOptimizerAgent",
    "InterviewPrepAgent",
    "ALL_AGENTS",
]
