from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal

# ==================== Phase 1: Data Schemas ====================

class Experience(BaseModel):
    company: str
    role: str
    duration: str
    description: List[str]

class Education(BaseModel):
    institution: str
    degree: str
    graduation_date: Optional[str] = None
    entry_type: Literal["degree", "certification", "bootcamp"] = "degree"

class Project(BaseModel):
    name: str
    description: List[str]
    tech_stack: List[str]
    url: Optional[str] = None

class ResumeSchema(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    links: List[str] = []
    skills: Dict[str, List[str]]
    work_history: List[Experience]
    education: List[Education]
    projects: List[Project] = []

class JobDescriptionSchema(BaseModel):
    title: str
    required_skills: List[str]
    responsibilities: List[str]

# ==================== Phase 2: Semantic Analysis Schemas ====================

class SemanticMatch(BaseModel):
    """Represents a semantic connection between resume content and job requirements."""
    resume_item: str = Field(description="The skill/experience from the resume")
    job_requirement: str = Field(description="The requirement from the job description")
    match_score: float = Field(ge=0.0, le=1.0, description="Confidence score (0-1)")
    reasoning: str = Field(description="Explanation of why these items match")
    match_type: Literal["exact", "semantic", "transferable"] = Field(
        description="Type of match: exact (same term), semantic (similar meaning), transferable (related skill)"
    )

class KeywordGap(BaseModel):
    """Represents a keyword/skill missing from the resume but present in job description."""
    missing_keyword: str = Field(description="The keyword missing from resume")
    importance: Literal["high", "medium", "low"] = Field(
        description="Priority level for adding this keyword"
    )
    context_in_job: Optional[str] = Field(default=None, description="How this keyword appears in the job description")
    suggested_section: str = Field(
        description="Which resume section should incorporate this (e.g., 'skills', 'work_history', specific company)"
    )
    integration_suggestion: str = Field(
        description="Suggested way to naturally incorporate this keyword"
    )

class AnalysisResult(BaseModel):
    """Complete semantic analysis of resume vs job description."""
    matches: List[SemanticMatch] = Field(description="Skills/experiences that align with job requirements")
    gaps: List[KeywordGap] = Field(description="Keywords/skills missing from resume")
    overall_alignment_score: float = Field(
        ge=0.0, le=1.0,
        description="Overall match score between resume and job (0-1)"
    )
    strengths: List[str] = Field(description="Strong points in the resume for this job")
    recommendations: List[str] = Field(description="High-level recommendations for improvement")

# ==================== Phase 3: Resume Tailoring Schemas ====================

class TailoredExperience(BaseModel):
    """Represents a single work experience with tailored bullet points."""
    company: str
    role: str
    duration: str
    tailored_bullet_points: List[str] = Field(description="Rewritten bullet points aligned with the job description")

class TailoredProject(BaseModel):
    name: str
    tailored_bullet_points: List[str]
    tech_stack: List[str]
    url: Optional[str] = None

class TailoredResume(BaseModel):
    """Represents the complete, tailored resume."""
    tailored_work_history: List[TailoredExperience] = Field(description="List of work experiences with tailored descriptions")
    updated_skills: Dict[str, List[str]] = Field(description="Categorized skills dict with gap keywords added")
    tailored_projects: List[TailoredProject] = []
    tailored_education: List[Education] = []

# ==================== Phase 4: Cover Letter Schema ====================

class CoverLetter(BaseModel):
    """Represents a generated cover letter."""
    greeting: str = Field(description="Opening greeting (e.g., 'Dear Hiring Manager,')")
    opening_paragraph: str = Field(description="Introduction expressing interest and fit")
    body_paragraphs: List[str] = Field(description="Body paragraphs highlighting relevant experience")
    closing_paragraph: str = Field(description="Closing paragraph with call to action")
    sign_off: str = Field(description="Sign-off (e.g., 'Sincerely,')")
