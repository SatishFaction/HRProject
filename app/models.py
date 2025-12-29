from pydantic import BaseModel, Field
from typing import Optional

class ScoreResponse(BaseModel):
    """Defines the structure of the API response for scoring."""
    score: float
    explanation: str

class JobRoleInput(BaseModel):
    """Defines the structure for the job description creation request."""
    job_title: str = Field(..., example="Senior Python Developer")
    company_name: str = Field(..., example="Innovatech Solutions")
    key_responsibilities: str = Field(
        ...,
        example="Develop and maintain web applications using FastAPI; Design and implement RESTful APIs; Collaborate with front-end developers."
    )
    required_skills: str = Field(
        ...,
        example="5+ years of Python experience, FastAPI, Docker, PostgreSQL, AWS."
    )
    experience_level: str = Field(..., example="Senior Level (5-8 years)")
    location: str = Field(..., example="Remote")
    extra_details: Optional[str] = Field(
        None,
        example="The ideal candidate should also have experience with CI/CD pipelines and microservices architecture."
    )

class JobDescriptionResponse(BaseModel):
    """Defines the structure of the job description response."""
    job_description: str