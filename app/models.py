from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal
from enum import Enum

# ==================== AUTHENTICATION MODELS ====================

class UserRole(str, Enum):
    HR = "hr"
    CANDIDATE = "candidate"

class RegisterRequest(BaseModel):
    """Request model for user registration."""
    email: str = Field(..., example="user@company.com")
    password: str = Field(..., min_length=6, example="securepassword123")
    full_name: str = Field(..., example="John Doe")
    role: UserRole = Field(..., example="hr")
    # Additional fields for candidates
    phone: Optional[str] = Field(None, example="+1234567890")
    resume_url: Optional[str] = Field(None, example="https://example.com/resume.pdf")

class LoginRequest(BaseModel):
    """Request model for user login."""
    email: str = Field(..., example="user@company.com")
    password: str = Field(..., example="securepassword123")

class User(BaseModel):
    """User model for database storage."""
    id: str
    email: str
    full_name: str
    role: UserRole
    phone: Optional[str] = None
    resume_url: Optional[str] = None
    created_at: str

class LoginResponse(BaseModel):
    """Response model for successful login."""
    success: bool
    message: str
    user: Optional[User] = None
    token: Optional[str] = None

class RegisterResponse(BaseModel):
    """Response model for successful registration."""
    success: bool
    message: str
    user: Optional[User] = None

class CandidateApplication(BaseModel):
    """Model for a scored candidate application."""
    id: str
    candidate_name: str
    candidate_email: Optional[str] = None
    job_role: Optional[str] = None
    score: int
    match_details: Optional[str] = None
    status: str
    created_at: str
    resume_url: Optional[str] = None

# ==================== EXISTING MODELS ====================

class ScoreResponse(BaseModel):
    """Defines the structure of the API response for scoring."""
    score: float
    explanation: str
    filename: Optional[str] = None

class BatchScoreResponse(BaseModel):
    results: list[ScoreResponse]

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

# ==================== CHAT MODELS ====================

class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(..., example="user")  # 'user' or 'assistant'
    content: str = Field(..., example="Hello, I'm here for my interview.")

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    messages: list[ChatMessage] = Field(..., description="List of conversation messages")
    candidate_name: str = Field(..., example="John Doe")

class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    success: bool
    message: str
    response: Optional[str] = None

# ==================== JOB POSTING MODELS ====================

class JobPostingStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    DRAFT = "draft"

class JobPostingCreate(BaseModel):
    """Request model for creating a job posting."""
    title: str = Field(..., example="Senior Python Developer")
    company_name: str = Field(..., example="Innovatech Solutions")
    description: str = Field(..., example="Full job description text...")
    experience_level: Optional[str] = Field(None, example="Senior Level (5-8 years)")
    location: Optional[str] = Field(None, example="Remote")
    responsibilities: Optional[str] = Field(None, example="Lead development projects...")
    skills: Optional[str] = Field(None, example="Python, FastAPI, Docker")

class JobPosting(BaseModel):
    """Model for a job posting."""
    id: str
    title: str
    company_name: str
    description: str
    experience_level: Optional[str] = None
    location: Optional[str] = None
    responsibilities: Optional[str] = None
    skills: Optional[str] = None
    status: str = "active"
    created_by: Optional[str] = None
    created_at: str

class JobPostingResponse(BaseModel):
    """Response model for job posting operations."""
    success: bool
    message: str
    job: Optional[JobPosting] = None

class JobPostingsListResponse(BaseModel):
    """Response model for listing job postings."""
    jobs: list[JobPosting]

# ==================== JOB APPLICATION MODELS ====================

class JobApplicationStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    HIRED = "hired"

class JobApplicationCreate(BaseModel):
    """Request model for creating a job application."""
    job_id: str = Field(..., example="job_123")
    cover_letter: Optional[str] = Field(None, example="I am excited to apply...")

class JobApplication(BaseModel):
    """Model for a job application."""
    id: str
    job_id: str
    candidate_id: str
    candidate_name: str
    candidate_email: str
    resume_path: Optional[str] = None
    resume_url: Optional[str] = None
    cover_letter: Optional[str] = None
    status: str = "pending"
    created_at: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None

class JobApplicationResponse(BaseModel):
    """Response model for job application operations."""
    success: bool
    message: str
    application: Optional[JobApplication] = None

class JobApplicationsListResponse(BaseModel):
    """Response model for listing job applications."""
    applications: list[JobApplication]