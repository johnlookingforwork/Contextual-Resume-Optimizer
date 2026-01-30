from pydantic import BaseModel
from typing import List, Optional

class Experience(BaseModel):
    company: str
    role: str
    duration: str
    description: List[str]

class ResumeSchema(BaseModel):
    name: str
    email: Optional[str] = None
    skills: List[str]
    work_history: List[Experience]
    education: List[dict]

class JobDescriptionSchema(BaseModel):
    title: str
    required_skills: List[str]
    responsibilities: List[str]